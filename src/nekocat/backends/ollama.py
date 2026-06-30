"""Ollama backend for locally-hosted open-source models.

Supports both the official ollama Python package and direct HTTP access.
"""

from __future__ import annotations

import json
from typing import AsyncIterator

import httpx

from nekocat.backends.base import (
    Backend,
    BackendCapabilities,
    BackendError,
    ConnectionError,
    GenerationRequest,
    GenerationResponse,
)


class OllamaBackend(Backend):
    """Backend for Ollama — local LLM server.

    Uses direct HTTP API for full control. Falls back to the ollama
    Python package if available.
    """

    DEFAULT_MODEL = "llama3.2"
    DEFAULT_BASE_URL = "http://localhost:11434"

    def __init__(
        self,
        api_key: str = "",
        model: str = "",
        base_url: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.9,
        timeout: float = 120.0,
        **kwargs,
    ) -> None:
        super().__init__()

        self.model = model or self.DEFAULT_MODEL
        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.timeout = timeout

        self._http = httpx.AsyncClient(
            base_url=self.base_url.rstrip("/"),
            timeout=httpx.Timeout(timeout),
        )

        # Try the official SDK if available
        self._use_sdk = False
        try:
            from ollama import AsyncClient
            self._ollama = AsyncClient(host=self.base_url)
            self._use_sdk = True
        except ImportError:
            self._ollama = None

        self._capabilities = BackendCapabilities(
            streaming=True,
            max_context_tokens=128_000,  # varies by model
            supports_system_prompt=True,
            supports_tools=False,
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Non-streaming generation."""
        if self._use_sdk and self._ollama is not None:
            return await self._generate_sdk(request)
        return await self._generate_http(request)

    async def stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """Streaming generation."""
        if self._use_sdk and self._ollama is not None:
            async for token in self._stream_sdk(request):
                yield token
        else:
            async for token in self._stream_http(request):
                yield token

    async def check_connection(self) -> bool:
        """Verify Ollama server is reachable."""
        try:
            response = await self._http.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """List models available from the Ollama server."""
        response = await self._http.get("/api/tags")
        if response.status_code != 200:
            return []
        data = response.json()
        return [m["name"] for m in data.get("models", [])]

    # ——— SDK path ———

    async def _generate_sdk(self, request: GenerationRequest) -> GenerationResponse:
        from ollama import AsyncClient
        client = AsyncClient(host=self.base_url)
        response = await client.chat(
            model=self.model,
            messages=request.messages,
            options={
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
        )
        return GenerationResponse(
            text=response["message"]["content"],
            finish_reason="stop",
        )

    async def _stream_sdk(self, request: GenerationRequest) -> AsyncIterator[str]:
        from ollama import AsyncClient
        client = AsyncClient(host=self.base_url)
        stream = await client.chat(
            model=self.model,
            messages=request.messages,
            options={
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
            },
            stream=True,
        )
        async for chunk in stream:
            if "message" in chunk and "content" in chunk["message"]:
                yield chunk["message"]["content"]

    # ——— Direct HTTP path ———

    async def _generate_http(self, request: GenerationRequest) -> GenerationResponse:
        payload = self._build_payload(request, stream=False)
        response = await self._http.post("/api/chat", json=payload)
        if response.status_code != 200:
            raise ConnectionError(f"Ollama API error: {response.status_code} {response.text}")
        data = response.json()
        return GenerationResponse(
            text=data.get("message", {}).get("content", ""),
            finish_reason="stop",
        )

    async def _stream_http(self, request: GenerationRequest) -> AsyncIterator[str]:
        payload = self._build_payload(request, stream=True)
        async with self._http.stream("POST", "/api/chat", json=payload) as response:
            if response.status_code != 200:
                raise ConnectionError(
                    f"Ollama API error: {response.status_code}"
                )
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    content = chunk.get("message", {}).get("content", "")
                    if content:
                        yield content
                except json.JSONDecodeError:
                    continue

    def _build_payload(self, request: GenerationRequest, stream: bool) -> dict:
        return {
            "model": self.model,
            "messages": request.messages,
            "stream": stream,
            "options": {
                "temperature": request.temperature or self.temperature,
                "num_predict": request.max_tokens or self.max_tokens,
            },
        }

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._http.aclose()
