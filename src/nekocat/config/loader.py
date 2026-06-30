"""Configuration loader — merge YAML/file, env vars, and CLI overrides."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from nekocat.config.settings import Settings


def load_settings(
    config_path: Optional[str | Path] = None,
    *,
    backend_provider: Optional[str] = None,
    backend_model: Optional[str] = None,
    persona_preset: Optional[str] = None,
    persona_file: Optional[str | Path] = None,
    typewriter_speed: Optional[float] = None,
    color_theme: Optional[str] = None,
) -> Settings:
    """Load settings with optional CLI overrides.

    Args:
        config_path: Override path to YAML config file.
        backend_provider: CLI --backend flag.
        backend_model: CLI --model flag.
        persona_preset: CLI --persona flag.
        persona_file: CLI --persona-file flag.
        typewriter_speed: CLI --speed flag.
        color_theme: CLI --theme flag.

    Returns:
        A fully resolved Settings instance.
    """
    # Build base settings from env vars and YAML file
    settings = Settings()

    # Apply YAML config file if specified
    if config_path:
        _apply_yaml_file(settings, Path(config_path))

    # Apply CLI overrides (they take highest priority)
    if backend_provider:
        settings.backend.provider = backend_provider
    if backend_model:
        settings.backend.model = backend_model
    if persona_preset:
        settings.persona.preset = persona_preset
    if persona_file:
        settings.persona.file = Path(persona_file)
    if typewriter_speed is not None:
        settings.cli.typewriter_speed = typewriter_speed
    if color_theme:
        # Validated by pydantic
        settings.cli.color_theme = color_theme  # type: ignore[assignment]

    return settings


def _apply_yaml_file(settings: Settings, path: Path) -> None:
    """Merge YAML config file values into the settings model."""
    if not path.is_file():
        return

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or not isinstance(data, dict):
        return

    if "backend" in data and isinstance(data["backend"], dict):
        b = data["backend"]
        for key in ("provider", "model", "api_key", "api_base", "max_tokens", "temperature", "timeout"):
            if key in b:
                setattr(settings.backend, key, b[key])

    if "persona" in data and isinstance(data["persona"], dict):
        p = data["persona"]
        if "preset" in p:
            settings.persona.preset = p["preset"]
        if "file" in p:
            settings.persona.file = Path(p["file"])

    if "cli" in data and isinstance(data["cli"], dict):
        c = data["cli"]
        for key in ("typewriter_speed", "show_header", "color_theme", "history_file"):
            if key in c:
                setattr(settings.cli, key, c[key])
