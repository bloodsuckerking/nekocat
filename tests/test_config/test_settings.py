"""Tests for config/settings."""

from __future__ import annotations

from nekocat.config.settings import (
    BackendConfig,
    CLIConfig,
    PersonaConfig,
    Settings,
)


class TestBackendConfig:
    def test_defaults(self) -> None:
        cfg = BackendConfig()
        assert cfg.provider == "mock"
        assert cfg.model == ""

    def test_custom_values(self) -> None:
        cfg = BackendConfig(provider="claude", model="claude-sonnet-4")
        assert cfg.provider == "claude"


class TestPersonaConfig:
    def test_defaults(self) -> None:
        cfg = PersonaConfig()
        assert cfg.preset == "classic_neko"
        assert cfg.file is None


class TestCLIConfig:
    def test_defaults(self) -> None:
        cfg = CLIConfig()
        assert cfg.typewriter_speed == 0.02
        assert cfg.color_theme == "pink"


class TestSettings:
    def test_default_settings(self) -> None:
        s = Settings()
        assert s.backend.provider == "mock"
        assert s.persona.preset == "classic_neko"
        assert s.cli.typewriter_speed == 0.02
