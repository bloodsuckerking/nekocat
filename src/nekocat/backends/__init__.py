"""Pluggable AI backend system.

Backends are registered via BackendRegistry. Built-in backends
are auto-registered on first import of this module.
"""

from nekocat.backends.base import (
    Backend,
    BackendCapabilities,
    BackendError,
    ConnectionError,
    GenerationRequest,
    GenerationResponse,
)
from nekocat.backends.mock import MockBackend
from nekocat.backends.registry import BackendRegistry


def _register_builtins() -> None:
    """Register all built-in backends. Called on module init."""
    # Mock is always available
    BackendRegistry.register("mock", MockBackend)

    # Optional backends: register even if SDK not installed;
    # they'll raise ImportError on instantiation with a helpful message.
    try:
        from nekocat.backends.claude import AnthropicBackend
        BackendRegistry.register("claude", AnthropicBackend)
    except ImportError:
        pass

    try:
        from nekocat.backends.openai import OpenAIBackend
        BackendRegistry.register("openai", OpenAIBackend)
    except ImportError:
        pass

    try:
        from nekocat.backends.ollama import OllamaBackend
        BackendRegistry.register("ollama", OllamaBackend)
    except ImportError:
        pass

    # DeepSeek — OpenAI-compatible, register as factory for auto base_url
    try:
        from nekocat.backends.openai import OpenAIBackend

        def _make_deepseek(**kwargs) -> OpenAIBackend:
            kwargs.setdefault("base_url", "https://api.deepseek.com/v1")
            # Default model if not specified
            if "model" not in kwargs or not kwargs["model"]:
                kwargs["model"] = "deepseek-v4-pro"
            return OpenAIBackend(**kwargs)

        BackendRegistry.register_factory("deepseek", _make_deepseek)
    except ImportError:
        pass


_register_builtins()


__all__ = [
    "Backend",
    "BackendCapabilities",
    "BackendError",
    "ConnectionError",
    "BackendRegistry",
    "GenerationRequest",
    "GenerationResponse",
    "MockBackend",
]
