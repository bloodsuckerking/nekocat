"""NekoCat CLI entry point — Typer app with subcommands.

Commands:
    nekocat chat            Interactive chat (default)
    nekocat persona-list    List built-in personas
    nekocat persona-show    Show persona details
    nekocat persona-validate Validate a persona YAML
    nekocat backends        List available AI backends
    nekocat config-show     Show current config
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional

import typer

from nekocat._version import __version__
from nekocat.backends.registry import BackendRegistry
from nekocat.cli.chat_loop import run_chat_loop
from nekocat.persona.presets._registry import (
    list_presets,
    load_persona_from_file,
    load_preset,
    validate_persona_file,
)

app = typer.Typer(
    name="nekocat",
    help="🐱 猫娘对话系统 — Catgirl Conversational AI CLI",
    invoke_without_command=True,
    no_args_is_help=False,
)


# ——— Default command: chat ———


@app.callback(invoke_without_command=True)
def default(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", "-V", help="Show version and exit"),
) -> None:
    """Entry point. Runs interactive chat by default."""
    if version:
        typer.echo(f"nekocat {__version__}")
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        _run_chat()


# ——— Chat command ———


@app.command(name="chat")
def chat_cmd(
    persona: str = typer.Option("", "--persona", "-p", help="Persona preset name"),
    persona_file: Optional[Path] = typer.Option(None, "--persona-file", help="Custom persona YAML path"),
    backend: str = typer.Option("", "--backend", "-b", help="AI backend: mock, claude, openai, ollama, deepseek"),
    model: str = typer.Option("", "--model", "-m", help="Model name"),
    api_key: str = typer.Option("", "--api-key", help="API key for the backend"),
    api_base: str = typer.Option("", "--api-base", help="Custom API base URL"),
    speed: float = typer.Option(-1.0, "--speed", "-s", help="Typewriter speed (0 = instant)"),
    theme: str = typer.Option("", "--theme", "-t", help="Color theme: pink, purple, mint, sunset"),
) -> None:
    """Start an interactive catgirl chat session."""
    _run_chat(
        persona=persona,
        persona_file=persona_file,
        backend=backend,
        model=model,
        api_key=api_key,
        api_base=api_base,
        speed=speed,
        theme=theme,
    )


# ——— Persona subcommands ———


@app.command(name="persona-list")
def persona_list_cmd() -> None:
    """List available built-in persona presets."""
    presets = list_presets()
    typer.echo("📋 Available persona presets:")
    for name in presets:
        try:
            p = load_preset(name)
            typer.echo(f"  • {name:25s} — {p.display_name} [{p.speech_style.value}]")
        except Exception:
            typer.echo(f"  • {name}")


@app.command(name="persona-show")
def persona_show_cmd(
    name: str = typer.Argument(..., help="Preset name to show"),
) -> None:
    """Show full details of a persona preset."""
    try:
        p = load_preset(name)
    except FileNotFoundError:
        typer.echo(
            f"❌ Preset '{name}' not found. "
            f"Use 'nekocat persona-list' to see available."
        )
        raise typer.Exit(code=1)

    typer.echo(f"🐱 {p.display_name}")
    typer.echo(f"   Name:        {p.name}")
    typer.echo(f"   Style:       {p.speech_style.value}")
    typer.echo(f"   Description: {p.description}")
    typer.echo(f"   Author:      {p.author} (v{p.version})")
    typer.echo(f"   Tags:        {', '.join(p.tags) if p.tags else '(none)'}")
    typer.echo(f"   Traits ({len(p.traits)}):")
    for t in sorted(p.traits, key=lambda t: t.intensity, reverse=True):
        bar = "█" * int(t.intensity * 10) + "░" * (10 - int(t.intensity * 10))
        typer.echo(f"     [{bar}] {t.name} ({t.intensity:.1f}) — {t.description}")
    typer.echo(f"   Rules ({len(p.rules)}):")
    for r in sorted(p.rules, key=lambda r: r.priority):
        typer.echo(f"     [P{r.priority}] {r.rule}")
    typer.echo(f"   Interjections: {', '.join(p.resolved_interjections) or '(none)'}")
    typer.echo(f"   Endings:       {', '.join(p.resolved_endings) or '(none)'}")
    typer.echo(f"   Has custom prompt: {p.custom_system_prompt is not None}")


@app.command(name="persona-validate")
def persona_validate_cmd(
    file: Path = typer.Argument(..., help="Path to persona YAML file"),
) -> None:
    """Validate a custom persona YAML file."""
    valid, error = validate_persona_file(file)
    if valid:
        p = load_persona_from_file(file)
        typer.echo(f"✅ Valid persona: {p.display_name} ({p.speech_style.value})")
    else:
        typer.echo(f"❌ Invalid: {error}")
        raise typer.Exit(code=1)


# ——— Backend subcommand ———


@app.command(name="backends")
def backends_cmd() -> None:
    """List available AI backends."""
    registered = BackendRegistry.list_backends()
    typer.echo("🤖 Available backends:")
    for name in registered:
        if name == "mock":
            status, desc = "✅ ready", "Offline test backend"
        elif name == "claude":
            status, desc = "🔑 needs API key", "Anthropic Claude"
        elif name == "openai":
            status, desc = "🔑 needs API key", "OpenAI / compatible APIs"
        elif name == "ollama":
            status, desc = "🔑 needs local server", "Local Ollama server"
        elif name == "deepseek":
            status, desc = "🔑 needs API key", "DeepSeek V4 (OpenAI-compatible)"
        else:
            status, desc = "🔌 third-party", "third-party"
        typer.echo(f"  • {name:15s} — {desc:30s} [{status}]")


# ——— Config subcommand ———


@app.command(name="config-show")
def config_show_cmd() -> None:
    """Show current configuration."""
    typer.echo("Current configuration:")
    typer.echo()
    typer.echo("[backend]")
    typer.echo("  provider = mock (default)")
    typer.echo("  model = (backend default)")
    typer.echo("  temperature = 0.9")
    typer.echo()
    typer.echo("[persona]")
    typer.echo("  preset = classic_neko (default)")
    typer.echo()
    typer.echo("[cli]")
    typer.echo("  typewriter_speed = 0.02")
    typer.echo("  color_theme = pink")
    typer.echo()
    typer.echo("Override with: ENV vars (NEKOCAT_*), nekocat.yaml, or CLI flags.")


# ——— Helpers ———


def _run_chat(
    persona: str = "",
    persona_file: Optional[Path] = None,
    backend: str = "",
    model: str = "",
    api_key: str = "",
    api_base: str = "",
    speed: float = -1.0,
    theme: str = "",
) -> None:
    """Resolve configuration and launch the chat REPL."""
    # Resolve persona
    if persona_file:
        try:
            persona_obj = load_persona_from_file(persona_file)
        except Exception as e:
            typer.echo(f"❌ Failed to load persona file: {e}")
            raise typer.Exit(code=1)
    elif persona:
        try:
            persona_obj = load_preset(persona)
        except FileNotFoundError:
            typer.echo(
                f"❌ Preset '{persona}' not found. "
                f"Use 'nekocat persona-list' to see available."
            )
            raise typer.Exit(code=1)
    else:
        persona_obj = load_preset("classic_neko")

    # Resolve backend
    backend_key = backend or "mock"
    backend_kwargs: dict = {}
    if api_key:
        backend_kwargs["api_key"] = api_key
    if api_base:
        backend_kwargs["base_url"] = api_base
    if model:
        backend_kwargs["model"] = model

    try:
        backend_obj = BackendRegistry.get(backend_key, **backend_kwargs)
    except KeyError as e:
        typer.echo(f"❌ {e}")
        raise typer.Exit(code=1)
    except ImportError as e:
        typer.echo(f"❌ {e}")
        raise typer.Exit(code=1)

    # Set model_display
    model_display = model or getattr(backend_obj, "model", "")
    # Resolve renderer settings
    typewriter_speed = speed if speed >= 0 else 0.02
    color_theme = theme or "pink"

    # Run async loop
    try:
        asyncio.run(
            run_chat_loop(
                persona=persona_obj,
                backend=backend_obj,
                model=model_display,
                typewriter_speed=typewriter_speed,
                color_theme=color_theme,
                show_header=True,
            )
        )
    except KeyboardInterrupt:
        typer.echo("\n喵~ Goodbye! 🐾")
    except Exception as e:
        typer.echo(f"❌ Fatal error: {e}")
        raise typer.Exit(code=1)


def main() -> None:
    """Entry point for the nekocat CLI."""
    app()
