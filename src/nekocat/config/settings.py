"""Pydantic settings model for NekoCat configuration.

Priority (highest to lowest):
1. CLI arguments (set on the model after init)
2. Environment variables (NEKOCAT_ prefix, __ as nested delimiter)
3. YAML config file (nekocat.yaml in cwd or ~/.config/nekocat/)
4. Defaults defined below
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Tuple, Type

from pydantic import Field, model_validator
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


class BackendConfig(BaseSettings):
    """AI backend configuration."""

    provider: str = Field(
        default="mock",
        description="Backend key: 'claude', 'openai', 'ollama', or 'mock'",
    )
    model: str = Field(
        default="",
        description="Model name. Empty = backend default.",
    )
    api_key: str = Field(
        default="",
        repr=False,
        description="API key for the provider (also checked from provider env vars)",
    )
    api_base: str = Field(
        default="",
        description="Custom API base URL for proxies / self-hosted",
    )
    max_tokens: int = Field(
        default=1024,
        ge=1,
        le=128_000,
        description="Max tokens per response",
    )
    temperature: float = Field(
        default=0.9,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (higher = more creative for moe style)",
    )
    timeout: float = Field(
        default=60.0,
        ge=1.0,
        description="HTTP request timeout in seconds",
    )

    model_config = SettingsConfigDict(extra="forbid")


class PersonaConfig(BaseSettings):
    """Persona selection configuration."""

    preset: str = Field(
        default="classic_neko",
        description="Name of a built-in persona preset",
    )
    file: Optional[Path] = Field(
        default=None,
        description="Path to a custom persona YAML file (takes priority over preset)",
    )

    model_config = SettingsConfigDict(extra="forbid")


class CLIConfig(BaseSettings):
    """CLI/terminal configuration."""

    typewriter_speed: float = Field(
        default=0.02,
        ge=0.0,
        le=1.0,
        description="Seconds between token prints (0 = instant)",
    )
    show_header: bool = Field(
        default=True,
        description="Show the header panel on each turn",
    )
    color_theme: Literal["pink", "purple", "mint", "sunset"] = Field(
        default="pink",
        description="CLI color theme",
    )
    history_file: Path = Field(
        default=Path.home() / ".nekocat" / "history.jsonl",
        description="Path for saving conversation history",
    )

    model_config = SettingsConfigDict(extra="forbid")


class Settings(BaseSettings):
    """Top-level NekoCat settings.

    Loaded from environment variables and config files.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="NEKOCAT_",
        env_nested_delimiter="__",
        extra="allow",
        yaml_file="nekocat.yaml",
        yaml_file_encoding="utf-8",
    )

    backend: BackendConfig = Field(default_factory=BackendConfig)
    persona: PersonaConfig = Field(default_factory=PersonaConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Inject YAML config source into the settings pipeline."""
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    @model_validator(mode="after")
    def resolve_api_key(self) -> "Settings":
        """If backend.api_key is empty, try reading from provider-specific env vars."""
        import os

        if not self.backend.api_key:
            provider_env_map = {
                "claude": "ANTHROPIC_API_KEY",
                "openai": "OPENAI_API_KEY",
            }
            env_var = provider_env_map.get(self.backend.provider)
            if env_var:
                key = os.environ.get(env_var, "")
                if key:
                    self.backend.api_key = key

        return self
