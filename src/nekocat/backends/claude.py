"""Anthropic Claude backend via the official SDK."""

from __future__ import annotations

import json
from typing import AsyncIterator

from nekocat.backends.base import (
    AuthenticationError,
    Backend,
    BackendCapabilities,
    BackendError,
    ConnectionError,
    GenerationRequest,
    GenerationResponse,
    RateLimitError,
)

try:
    from anthropic import AsyncAnthropic, APIStatusError
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    AsyncAnthropic = None  # type: ignore[assignment]
    APIStatusError = Exception  # fallback


class AnthropicBackend(Backend):
    """Backend for Anthropic Claude models.

    Converts OpenAI-format messages to Anthropic's native format.
    Supports streaming via SDK text_stream.
    """

    # Default model when none specified
    DEFAULT_MODEL = "claude-sonnet-4-20250514"

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
        base_url: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.9,
        timeout: float = 60.0,
        **kwargs,
    ) -> None:
        super().__init__()

        if not HAS_ANTHROPIC:
            raise ImportError(
                "anthropic package is required for AnthropicBackend. "
                "Install with: pip install nekocat[anthropic]"
            )

        self.model = model or self.DEFAULT_MODEL
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        client_kwargs: dict = {
            "timeout": timeout,
            "max_retries": 2,
        }
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = AsyncAnthropic(**client_kwargs)

        self._capabilities = BackendCapabilities(
            streaming=True,
            max_context_tokens=200_000,
            supports_system_prompt=True,
            supports_tools=True,
            supports_vision=True,
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Non-streaming generation."""
        system_prompt, messages = self._convert_messages(request.messages)
        try:
            response = await self._client.messages.create(
                model=self.model,
                system=system_prompt,
                messages=messages,
                max_tokens=request.max_tokens or self.max_tokens,
                temperature=request.temperature or self.temperature,
                stop_sequences=request.stop_sequences or [],
            )
            text = response.content[0].text if response.content else ""
            return GenerationResponse(
                text=text,
                finish_reason=response.stop_reason or "stop",
                usage={
                    "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                    "completion_tokens": response.usage.output_tokens if response.usage else 0,
                },
            )
        except APIStatusError as e:
            raise self._translate_error(e)

    async def stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """Streaming generation via text_stream."""
        system_prompt, messages = self._convert_messages(request.messages)
        try:
            async with self._client.messages.stream(
                model=self.model,
                system=system_prompt,
                messages=messages,
                max_tokens=request.max_tokens or self.max_tokens,
                temperature=request.temperature or self.temperature,
                stop_sequences=request.stop_sequences or [],
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except APIStatusError as e:
            raise self._translate_error(e)

    async def check_connection(self) -> bool:
        """Verify connectivity by creating a simple request."""
        try:
            await self.generate(
                GenerationRequest(
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=10,
                )
            )
            return True
        except Exception:
            return False

    # ——— Message conversion ———

    def _convert_messages(
        self, messages: list[dict[str, str]]
    ) -> tuple[str, list[dict[str, str]]]:
        """Convert OpenAI-format messages to Anthropic format.

        Returns (system_prompt, anthropic_messages).
        """
        system_parts: list[str] = []
        anthropic_messages: list[dict[str, str]] = []

        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                system_parts.append(content)
            elif role in ("user", "assistant"):
                anthropic_messages.append({"role": role, "content": content})

        return "\n\n".join(system_parts), anthropic_messages

    # ——— Error handling ———

    def _translate_error(self, error: APIStatusError) -> BackendError:
        """Map Anthropic error codes to nekocat exception types."""
        status = getattr(error, "status_code", 0)
        if status == 401 or status == 403:
            return AuthenticationError(str(error))
        elif status == 429:
            return RateLimitError(str(error))
        elif status >= 500:
            return ConnectionError(str(error))
        return BackendError(str(error))
