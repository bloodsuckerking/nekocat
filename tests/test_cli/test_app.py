"""Tests for CLI app commands."""

from __future__ import annotations

from typer.testing import CliRunner

from nekocat.cli.app import app


runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "nekocat" in result.stdout


def test_persona_list() -> None:
    result = runner.invoke(app, ["persona-list"])
    assert result.exit_code == 0
    assert "classic_neko" in result.stdout
    assert "tsundere_neko" in result.stdout


def test_persona_show() -> None:
    result = runner.invoke(app, ["persona-show", "classic_neko"])
    assert result.exit_code == 0
    assert "Mimi" in result.stdout


def test_persona_show_nonexistent() -> None:
    result = runner.invoke(app, ["persona-show", "does_not_exist"])
    assert result.exit_code == 1


def test_backends() -> None:
    result = runner.invoke(app, ["backends"])
    assert result.exit_code == 0
    assert "mock" in result.stdout


def test_config_show() -> None:
    result = runner.invoke(app, ["config-show"])
    assert result.exit_code == 0
    assert "backend" in result.stdout


def test_chat_help() -> None:
    result = runner.invoke(app, ["chat", "--help"])
    assert result.exit_code == 0
    assert "--persona" in result.stdout
    assert "--backend" in result.stdout
