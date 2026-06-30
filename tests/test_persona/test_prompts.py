"""Tests for system prompt builder."""

from __future__ import annotations

from nekocat.persona.models import (
    BehaviorRule,
    PersonaProfile,
    PersonalityTrait,
    SpeechStyle,
)
from nekocat.persona.prompts import build_system_prompt


def test_build_moe_prompt() -> None:
    p = PersonaProfile(
        name="Mimi",
        display_name="小咪",
        description="A cute catgirl",
        backstory="Born from a shooting star.",
        speech_style=SpeechStyle.MOE,
    )
    prompt = build_system_prompt(p)
    assert "小咪" in prompt
    assert "猫娘" in prompt or "cat" in prompt.lower()
    assert "喵~" in prompt


def test_build_tsundere_prompt() -> None:
    p = PersonaProfile(
        name="Saki",
        description="A tsundere catgirl",
        backstory="Was once a stray.",
        speech_style=SpeechStyle.TSUN,
    )
    prompt = build_system_prompt(p)
    assert "Saki" in prompt or "咲希" in prompt


def test_traits_sorted_by_intensity() -> None:
    p = PersonaProfile(
        name="Test",
        description="d",
        backstory="b",
        traits=[
            PersonalityTrait(name="Low", description="low", intensity=0.3),
            PersonalityTrait(name="High", description="high", intensity=0.9),
        ],
    )
    prompt = build_system_prompt(p)
    high_idx = prompt.index("High")
    low_idx = prompt.index("Low")
    assert high_idx < low_idx  # higher intensity first


def test_custom_system_prompt_bypasses_builder() -> None:
    p = PersonaProfile(
        name="Test",
        description="d",
        backstory="b",
        custom_system_prompt="You are a dog. Yes, a dog.",
    )
    prompt = build_system_prompt(p)
    assert prompt == "You are a dog. Yes, a dog."


def test_rules_sorted_by_priority() -> None:
    p = PersonaProfile(
        name="Test",
        description="d",
        backstory="b",
        rules=[
            BehaviorRule(rule="Low priority", priority=10),
            BehaviorRule(rule="High priority", priority=0),
        ],
    )
    prompt = build_system_prompt(p)
    assert prompt.index("High priority") < prompt.index("Low priority")
