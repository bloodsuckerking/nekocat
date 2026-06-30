"""Abstract base class for AI backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional


@dataclass
class BackendCapabilities:
    """Declared capabilities of a backend."""

    streaming: bool = True
    max_context_tokens: int = 200_000
    supports_system_prompt: bool = True
    supports_tools: bool = False
    supports_vision: bool = False


@dataclass
class GenerationRequest:
    """A request to generate a response.

    Uses OpenAI-compatible message format internally.
    """

    messages: list[dict[str, str]]  # [{role, content}, ...]
    max_tokens: int = 1024
    temperature: float = 0.9
    stop_sequences: Optional[list[str]] = None


@dataclass
class GenerationResponse:
    """A generated response from the AI backend."""

    text: str
    finish_reason: str = "stop"  # "stop", "length", "error"
    usage: Optional[dict[str, int]] = None  # {"prompt_tokens": N, "completion_tokens": M}


class Backend(ABC):
    """Abstract backend for AI generation.

    Concrete implementations manage the transport layer (HTTP, SDK, etc.).
    Subclasses should accept configuration as keyword arguments in __init__.
    """

    # Subclasses MUST set these
    _capabilities: BackendCapabilities

    @property
    def name(self) -> str:
        """Human-readable backend name."""
        return self.__class__.__name__.replace("Backend", "")

    @property
    def capabilities(self) -> BackendCapabilities:
        """Backend feature declarations."""
        return self._capabilities

    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a complete response (non-streaming).

        Args:
            request: The generation request with messages and parameters.

        Returns:
            A GenerationResponse with the full text.
        """
        ...

    @abstractmethod
    async def stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """Generate a response as a stream of text tokens.

        Args:
            request: The generation request with messages and parameters.

        Yields:
            String chunks (typically token-level).
        """
        ...

    async def check_connection(self) -> bool:
        """Quick connectivity check. Returns True if the backend is reachable."""
        return True


class BackendError(Exception):
    """Base exception for backend-level errors."""
    pass


class ConnectionError(BackendError):
    """Failed to connect to the backend."""
    pass


class AuthenticationError(BackendError):
    """API key or authentication failure."""
    pass


class RateLimitError(BackendError):
    """Rate limit exceeded."""
    pass
