"""Built-in persona preset loader and lister.

Presets are stored as YAML files alongside this module. The registry
provides functions to list available presets, load one by name, and
validate custom persona YAML files.
"""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Optional

import yaml

from nekocat.persona.models import PersonaProfile

# Path to the presets directory
_PRESETS_DIR = files(__package__)


def list_presets() -> list[str]:
    """Return a list of available built-in preset names.

    Returns:
        Preset names without the .yaml extension, e.g. ['classic_neko', ...].
    """
    preset_names: list[str] = []
    for p in sorted(_PRESETS_DIR.iterdir()):
        if p.suffix in (".yaml", ".yml") and not p.name.startswith("_"):
            preset_names.append(p.stem)
    return preset_names


def load_preset(name: str) -> PersonaProfile:
    """Load a built-in persona preset by name.

    Args:
        name: Preset name without extension, e.g. 'classic_neko'.

    Returns:
        A validated PersonaProfile.

    Raises:
        FileNotFoundError: If the preset does not exist.
    """
    # Try with both .yaml and .yml extensions
    for ext in (".yaml", ".yml"):
        preset_path = _PRESETS_DIR / f"{name}{ext}"
        if preset_path.is_file():
            return load_persona_from_file(preset_path)

    available = ", ".join(list_presets())
    raise FileNotFoundError(
        f"Preset '{name}' not found. Available presets: {available}"
    )


def load_persona_from_file(path: str | Path) -> PersonaProfile:
    """Load and validate a PersonaProfile from a YAML file path.

    Args:
        path: Path to a .yaml or .yml file containing a persona definition.

    Returns:
        A validated PersonaProfile.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the YAML is invalid or fails validation.
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Persona file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError(f"Persona file is empty: {path}")

    return PersonaProfile.model_validate(data)


def validate_persona_file(path: str | Path) -> tuple[bool, Optional[str]]:
    """Validate a persona YAML file without loading it into a profile.

    Args:
        path: Path to a .yaml or .yml file.

    Returns:
        A tuple of (is_valid, error_message). error_message is None if valid.
    """
    try:
        load_persona_from_file(path)
        return True, None
    except FileNotFoundError as e:
        return False, str(e)
    except yaml.YAMLError as e:
        return False, f"YAML parse error: {e}"
    except ValueError as e:
        # pydantic validation errors come through as ValueError groups
        error_detail = _format_validation_error(e)
        return False, f"Validation error: {error_detail}"


def _format_validation_error(error: ValueError) -> str:
    """Extract a readable string from a pydantic ValidationError."""
    try:
        from pydantic import ValidationError
        if isinstance(error, ValidationError):
            messages = []
            for err in error.errors():
                loc = " → ".join(str(l) for l in err["loc"])
                msg = err.get("msg", "unknown error")
                messages.append(f"  - {loc}: {msg}")
            return "\n" + "\n".join(messages)
    except Exception:
        pass
    return str(error)
