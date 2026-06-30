"""Tests for persona models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from nekocat.persona.models import (
    BehaviorRule,
    PersonaProfile,
    PersonalityTrait,
    SpeechStyle,
)


class TestSpeechStyle:
    def test_values(self) -> None:
        assert SpeechStyle.MOE.value == "moe"
        assert SpeechStyle.TSUN.value == "tsundere"
        assert SpeechStyle.KUU.value == "kuudere"
        assert SpeechStyle.DEREDERE.value == "deredere"


class TestPersonalityTrait:
    def test_create(self) -> None:
        t = PersonalityTrait(name="Playful", description="Loves to play")
        assert t.name == "Playful"
        assert t.intensity == 0.7  # default

    def test_intensity_bounds(self) -> None:
        with pytest.raises(ValidationError):
            PersonalityTrait(name="X", description="desc", intensity=1.5)

        with pytest.raises(ValidationError):
            PersonalityTrait(name="X", description="desc", intensity=-0.1)


class TestBehaviorRule:
    def test_create(self) -> None:
        r = BehaviorRule(rule="Say nya~")
        assert r.priority == 0  # default
        assert r.rule == "Say nya~"


class TestPersonaProfile:
    def test_minimal_profile(self) -> None:
        p = PersonaProfile(
            name="Test",
            description="A test kitty",
            backstory="Was a test.",
        )
        assert p.display_name == "Test"  # auto-derived
        assert p.speech_style == SpeechStyle.MOE
        assert p.resolved_interjections == ["喵~", "喵呜~", "呜咪~", "诶嘿嘿~"]

    def test_full_profile(self) -> None:
        p = PersonaProfile(
            name="Full",
            display_name="Full Kitty",
            description="Full test",
            backstory="Story",
            speech_style=SpeechStyle.TSUN,
            traits=[PersonalityTrait(name="Tsun", description="tsuntsun")],
            rules=[BehaviorRule(rule="No exceptions", priority=0)],
            interjections=["哼~"],
            endings=["nya..."],
        )
        assert len(p.traits) == 1
        assert len(p.rules) == 1
        assert p.resolved_interjections == ["哼~"]  # custom
        assert p.resolved_endings == ["nya..."]

    def test_custom_system_prompt_overrides(self) -> None:
        p = PersonaProfile(
            name="Custom",
            description="desc",
            backstory="lore",
            custom_system_prompt="Be a cat.",
        )
        assert p.custom_system_prompt == "Be a cat."

    def test_default_display_name_fallback(self) -> None:
        p = PersonaProfile(name="OnlyName", description="d", backstory="b")
        assert p.display_name == "OnlyName"
