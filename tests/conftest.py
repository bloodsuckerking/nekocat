"""Shared test fixtures for nekocat."""

from __future__ import annotations

import pytest

from nekocat.backends.base import BackendCapabilities, GenerationRequest, GenerationResponse
from nekocat.backends.registry import BackendRegistry
from nekocat.persona.models import PersonaProfile, SpeechStyle


@pytest.fixture(autouse=True)
def clean_backend_registry() -> None:
    """Ensure backend registry is clean before each test."""
    # Don't clear — built-in backends are auto-registered on import
    yield


@pytest.fixture
def mock_persona() -> PersonaProfile:
    """A minimal persona for testing."""
    return PersonaProfile(
        name="TestNeko",
        display_name="测试喵",
        description="A test catgirl",
        backstory="Once a test kitty, now an AI tester.",
        speech_style=SpeechStyle.MOE,
        traits=[],
        rules=[],
        interjections=["喵~"],
        endings=["的说~"],
    )
