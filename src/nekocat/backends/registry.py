"""Backend registry — global lookup for backend classes and factories."""

from __future__ import annotations

from typing import Any, Callable, Type

from nekocat.backends.base import Backend


class BackendRegistry:
    """Global registry mapping string keys to Backend classes and factories.

    Usage:
        BackendRegistry.register("my_backend", MyBackend)
        backend = BackendRegistry.get("my_backend", api_key="...")
    """

    _backends: dict[str, Type[Backend]] = {}
    _factories: dict[str, Callable[..., Backend]] = {}

    @classmethod
    def register(cls, key: str, backend_cls: Type[Backend]) -> None:
        """Register a Backend subclass under a string key.

        Args:
            key: String identifier, e.g. 'claude', 'openai'.
            backend_cls: A Backend subclass.
        """
        cls._backends[key] = backend_cls

    @classmethod
    def register_factory(cls, key: str, factory: Callable[..., Backend]) -> None:
        """Register a factory function under a string key.

        Args:
            key: String identifier.
            factory: A callable that returns a Backend instance.
        """
        cls._factories[key] = factory

    @classmethod
    def get(cls, key: str, **kwargs: Any) -> Backend:
        """Instantiate and return a backend by key.

        Args:
            key: String identifier for the backend.
            **kwargs: Passed to the Backend constructor or factory.

        Returns:
            A Backend instance.

        Raises:
            KeyError: If no backend is registered under the given key.
        """
        if key in cls._factories:
            return cls._factories[key](**kwargs)

        if key in cls._backends:
            return cls._backends[key](**kwargs)

        available = cls.list_backends()
        raise KeyError(
            f"No backend registered under '{key}'. "
            f"Available backends: {available or '(none)'}"
        )

    @classmethod
    def list_backends(cls) -> list[str]:
        """Return a sorted list of all registered backend keys."""
        all_keys = set(cls._backends.keys()) | set(cls._factories.keys())
        return sorted(all_keys)

    @classmethod
    def is_registered(cls, key: str) -> bool:
        """Check if a backend key is registered."""
        return key in cls._backends or key in cls._factories

    @classmethod
    def unregister(cls, key: str) -> None:
        """Remove a backend registration."""
        cls._backends.pop(key, None)
        cls._factories.pop(key, None)

    @classmethod
    def clear(cls) -> None:
        """Remove all registrations. Useful for testing."""
        cls._backends.clear()
        cls._factories.clear()
