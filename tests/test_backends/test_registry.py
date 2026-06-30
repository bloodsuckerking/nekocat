"""Tests for BackendRegistry."""

from __future__ import annotations

import pytest
from nekocat.backends.registry import BackendRegistry


def test_list_backends_includes_mock() -> None:
    backends = BackendRegistry.list_backends()
    assert "mock" in backends
    assert len(backends) >= 1


def test_get_mock_backend() -> None:
    backend = BackendRegistry.get("mock")
    assert backend.name == "Mock"


def test_get_nonexistent_backend() -> None:
    with pytest.raises(KeyError):
        BackendRegistry.get("nonexistent_backend")


def test_is_registered() -> None:
    assert BackendRegistry.is_registered("mock") is True
    assert BackendRegistry.is_registered("made_up_backend") is False


def test_register_and_unregister() -> None:
    from nekocat.backends.mock import MockBackend

    # Register a custom key
    BackendRegistry.register("test_mock", MockBackend)
    assert BackendRegistry.is_registered("test_mock")

    # Unregister
    BackendRegistry.unregister("test_mock")
    assert not BackendRegistry.is_registered("test_mock")


def test_register_factory() -> None:
    from nekocat.backends.mock import MockBackend

    def factory(**kwargs):
        return MockBackend(model="factory-model", **kwargs)

    BackendRegistry.register_factory("factory_test", factory)
    assert BackendRegistry.is_registered("factory_test")

    backend = BackendRegistry.get("factory_test")
    assert backend.model == "factory-model"

    BackendRegistry.unregister("factory_test")
