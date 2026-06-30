"""Pydantic models for catgirl persona/profile system."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class SpeechStyle(str, Enum):
    """Speech style archetypes for catgirl characters."""

    MOE = "moe"           # 可爱型: uses 喵~, 喵呜~, purrs, energetic
    TSUN = "tsundere"     # 傲娇型: harsh exterior, secretly sweet
    KUU = "kuudere"       # 冷酷型: cool, aloof, deadpan
    DEREDERE = "deredere" # 甜腻型: openly affectionate, energetic


class PersonalityTrait(BaseModel):
    """A single personality trait with configurable intensity."""

    name: str = Field(description="Trait name, e.g. 'Playful', 'Curious'")
    description: str = Field(description="What this trait means in practice")
    intensity: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="How strongly this trait manifests (0.0-1.0)",
    )


class BehaviorRule(BaseModel):
    """A hard behavioral constraint injected into the system prompt."""

    rule: str = Field(description="The behavioral rule, e.g. 'Always end with 喵~'")
    priority: int = Field(default=0, description="Lower = higher priority when ordering rules")


class PersonaProfile(BaseModel):
    """Complete definition of a catgirl character persona.

    All fields together define: who the character is, how they speak,
    and what rules they must follow.
    """

    # Identity
    name: str = Field(description="Character name, e.g. 'Mimi'")
    display_name: str = Field(default="", description="Display name shown in CLI header")
    description: str = Field(description="One-line character description")
    backstory: str = Field(description="2-4 paragraph character lore/backstory")

    # Speech
    speech_style: SpeechStyle = Field(
        default=SpeechStyle.MOE,
        description="Archetype governing overall speech patterns",
    )

    # Traits & rules
    traits: list[PersonalityTrait] = Field(
        default_factory=list,
        description="Character personality traits",
    )
    rules: list[BehaviorRule] = Field(
        default_factory=list,
        description="Hard behavioral constraints",
    )

    # Speech pattern ornaments
    interjections: list[str] = Field(
        default_factory=list,
        description="Interjections sprinkled into speech, e.g. ['喵~', '喵呜~']",
    )
    endings: list[str] = Field(
        default_factory=list,
        description="Sentence-ending ornaments, e.g. ['的说~', 'nya~']",
    )

    # Override: if set, bypasses the auto-generated system prompt entirely
    custom_system_prompt: Optional[str] = Field(
        default=None,
        description="If set, overrides the auto-generated system prompt",
    )

    # Metadata
    author: str = Field(default="nekocat", description="Persona author")
    version: str = Field(default="1.0", description="Persona version")
    tags: list[str] = Field(default_factory=list, description="Discovery tags")

    @model_validator(mode="after")
    def default_display_name(self) -> "PersonaProfile":
        """If display_name is empty, derive from name."""
        if not self.display_name:
            object.__setattr__(self, "display_name", self.name)
        return self

    @property
    def resolved_interjections(self) -> list[str]:
        """Return interjections, falling back to defaults based on speech style."""
        if self.interjections:
            return self.interjections
        return _DEFAULT_INTERJECTIONS.get(self.speech_style, [])

    @property
    def resolved_endings(self) -> list[str]:
        """Return endings, falling back to defaults based on speech style."""
        if self.endings:
            return self.endings
        return _DEFAULT_ENDINGS.get(self.speech_style, [])


# ——— Speech-style defaults ———

_DEFAULT_INTERJECTIONS: dict[SpeechStyle, list[str]] = {
    SpeechStyle.MOE: ["喵~", "喵呜~", "呜咪~", "诶嘿嘿~"],
    SpeechStyle.TSUN: ["哼~", "哼哒~", "喵...", "切~"],
    SpeechStyle.KUU: ["喵。", "嗯。", "呼。", "..."],
    SpeechStyle.DEREDERE: ["喵~", "呜咪~", "诶嘿嘿~", "喜欢~"],
}

_DEFAULT_ENDINGS: dict[SpeechStyle, list[str]] = {
    SpeechStyle.MOE: ["的说~", "nya~", "呢~", "喵~"],
    SpeechStyle.TSUN: ["...的说", "啦", "哼", "nya..."],
    SpeechStyle.KUU: ["的说", "nya", "呢", "。"],
    SpeechStyle.DEREDERE: ["的说~", "nya~", "呢~", "喵呜~"],
}
