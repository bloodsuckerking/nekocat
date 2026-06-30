"""NekoCat — 猫娘对话系统 SDK.

A Python SDK for building catgirl conversational AI with pluggable backends.
"""

from nekocat._version import __version__
from nekocat.persona.models import (
    BehaviorRule,
    PersonaProfile,
    PersonalityTrait,
    SpeechStyle,
)
from nekocat.persona.presets._registry import list_presets, load_preset

# Lazy imports for modules that may have optional dependencies
__all__ = [
    "__version__",
    "PersonaProfile",
    "PersonalityTrait",
    "BehaviorRule",
    "SpeechStyle",
    "list_presets",
    "load_preset",
]
