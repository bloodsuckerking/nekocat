"""Tests for persona preset registry."""

from __future__ import annotations

from nekocat.persona.models import PersonaProfile
from nekocat.persona.presets._registry import (
    list_presets,
    load_persona_from_file,
    load_preset,
    validate_persona_file,
)


def test_list_presets() -> None:
    presets = list_presets()
    assert "classic_neko" in presets
    assert "tsundere_neko" in presets
    assert "kuudere_neko" in presets
    assert len(presets) >= 3


def test_load_classic_neko() -> None:
    p = load_preset("classic_neko")
    assert isinstance(p, PersonaProfile)
    assert p.name == "Mimi"
    assert len(p.traits) == 3
    assert len(p.rules) == 5


def test_load_tsundere_neko() -> None:
    p = load_preset("tsundere_neko")
    assert p.name == "Saki"
    assert p.speech_style.value == "tsundere"


def test_load_kuudere_neko() -> None:
    p = load_preset("kuudere_neko")
    assert p.name == "Rei"
    assert p.speech_style.value == "kuudere"


def test_load_nonexistent_preset() -> None:
    import pytest
    with pytest.raises(FileNotFoundError):
        load_preset("nonexistent_preset")


def test_validate_valid_persona(tmp_path) -> None:
    import yaml
    data = {
        "name": "Test",
        "description": "A test",
        "backstory": "Test backstory",
    }
    path = tmp_path / "test.yaml"
    with open(path, "w") as f:
        yaml.dump(data, f)

    valid, error = validate_persona_file(path)
    assert valid is True
    assert error is None


def test_validate_invalid_persona(tmp_path) -> None:
    path = tmp_path / "invalid.yaml"
    with open(path, "w") as f:
        f.write("name: MissingFields\n")

    valid, error = validate_persona_file(path)
    assert valid is False
    assert error is not None
