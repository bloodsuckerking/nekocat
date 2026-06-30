"""OpenAI backend via the official SDK.

Also works with any OpenAI-compatible API (Azure, Groq, Together, DeepSeek, etc.)
by setting the base_url parameter.
"""

from __future__ import annotations

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
    from openai import APIStatusError, AsyncOpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    AsyncOpenAI = None  # type: ignore[assignment]
    APIStatusError = Exception  # fallback


class OpenAIBackend(Backend):
    """Backend for OpenAI models (GPT-4o, GPT-4o-mini, etc.).

    Also compatible with any OpenAI-compatible API endpoint.
    Messages are already in OpenAI format, so minimal conversion needed.
    """

    DEFAULT_MODEL = "gpt-4o-mini"

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

        if not HAS_OPENAI:
            raise ImportError(
                "openai package is required for OpenAIBackend. "
                "Install with: pip install nekocat[openai]"
            )

        self.model = model or self.DEFAULT_MODEL
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        client_kwargs: dict = {
            "timeout": timeout,
            "max_retries": 2,
        }
        # Only pass api_key if it's non-empty — empty string overrides env var
        if api_key:
            client_kwargs["api_key"] = api_key
        if base_url:
            client_kwargs["base_url"] = base_url

        self._client = AsyncOpenAI(**client_kwargs)

        self._capabilities = BackendCapabilities(
            streaming=True,
            max_context_tokens=128_000,
            supports_system_prompt=True,
            supports_tools=True,
            supports_vision=True,
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Non-streaming generation."""
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=request.messages,  # type: ignore[arg-type]
                max_tokens=request.max_tokens or self.max_tokens,
                temperature=request.temperature or self.temperature,
            )
            choice = response.choices[0]
            return GenerationResponse(
                text=choice.message.content or "",
                finish_reason=choice.finish_reason or "stop",
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            )
        except APIStatusError as e:
            raise self._translate_error(e)

    async def stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """Streaming generation yielding tokens as they arrive."""
        try:
            stream = await self._client.chat.completions.create(
                model=self.model,
                messages=request.messages,  # type: ignore[arg-type]
                max_tokens=request.max_tokens or self.max_tokens,
                temperature=request.temperature or self.temperature,
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except APIStatusError as e:
            raise self._translate_error(e)

    async def check_connection(self) -> bool:
        """Verify connectivity with a simple request."""
        try:
            await self.generate(
                GenerationRequest(
                    messages=[{"role": "user", "content": "ping"}],
                    max_tokens=5,
                )
            )
            return True
        except Exception:
            return False

    def _translate_error(self, error: APIStatusError) -> BackendError:
        """Map OpenAI error codes to nekocat exception types."""
        status = getattr(error, "status_code", 0)
        if status == 401 or status == 403:
            return AuthenticationError(str(error))
        elif status == 429:
            return RateLimitError(str(error))
        elif status >= 500:
            return ConnectionError(str(error))
        return BackendError(str(error))
