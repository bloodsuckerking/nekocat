"""Async REPL chat loop — the core interactive chat experience."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from nekocat.backends.base import Backend
from nekocat.backends.registry import BackendRegistry
from nekocat.cli.renderer import Renderer
from nekocat.core.chat import NekoChat
from nekocat.core.session import ChatSession
from nekocat.persona.models import PersonaProfile
from nekocat.persona.presets._registry import (
    list_presets,
    load_persona_from_file,
    load_preset,
)


async def run_chat_loop(
    persona: PersonaProfile,
    backend: Backend,
    model: str = "",
    *,
    typewriter_speed: float = 0.02,
    color_theme: str = "pink",
    show_header: bool = True,
    history_file: Optional[Path] = None,
) -> None:
    """Run the interactive chat REPL.

    Args:
        persona: The loaded catgirl persona.
        backend: The AI backend instance.
        model: Model name for display purposes.
        typewriter_speed: Seconds between token prints (0 = instant).
        color_theme: Color theme for the renderer.
        show_header: Whether to show the header panel each turn.
        history_file: Optional path to save conversation history.
    """
    renderer = Renderer(
        color_theme=color_theme,
        typewriter_speed=typewriter_speed,
    )
    chat = NekoChat(persona=persona, backend=backend)
    session = ChatSession()

    # Welcome
    renderer.render_markdown(f"\n# 🐱 Welcome to NekoChat!")
    renderer.render_status(
        f"Persona: {persona.display_name} ({persona.speech_style.value})  |  "
        f"Backend: {backend.name}  |  "
        "Type /help for commands"
    )
    renderer.render_blank_line()

    # Main loop
    import builtins
    while True:
        try:
            # Use builtins.input() for maximum cross-platform compatibility.
            # Rich's Prompt.ask fails on some Windows terminals.
            renderer.console.print("\n[bold cyan]You:[/] ", end="")
            user_input = builtins.input()
        except (KeyboardInterrupt, EOFError):
            renderer.render_blank_line()
            await _say_goodbye(renderer, chat, persona, session, history_file)
            break

        user_input = user_input.strip()
        if not user_input:
            continue

        # Handle slash commands
        if user_input.startswith("/"):
            should_exit = await _handle_command(
                user_input, renderer, chat, backend, model, session, history_file
            )
            if should_exit:
                break
            continue

        # Normal message flow
        if show_header:
            renderer.render_header(session, persona, backend.name, model)

        renderer.render_user_message(user_input)

        try:
            # Stream the response with typewriter effect
            _print_neko_label(renderer, persona)
            full_response = await renderer.render_neko_stream(
                chat.stream(user_input, session),
                persona_name=persona.name,
            )
            # Save to history file if configured
            if history_file:
                _save_turn(history_file, user_input, full_response, session.turn_count)
        except Exception as e:
            renderer.render_error(str(e))
            renderer.render_status("An error occurred. You can continue chatting.")

    renderer.render_markdown("\n喵~ See you next time! 🐾\n")


def _print_neko_label(renderer: Renderer, persona: PersonaProfile) -> None:
    """Print the neko label line before streaming."""
    # This is handled inside render_neko_stream now, but we keep
    # this for potential standalone use
    pass


# ——— Slash commands ———


async def _handle_command(
    cmd: str,
    renderer: Renderer,
    chat: NekoChat,
    backend: Backend,
    model: str,
    session: ChatSession,
    history_file: Optional[Path],
) -> bool:
    """Handle a slash command. Returns True if the chat should exit."""
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if command in ("/exit", "/quit"):
        await _say_goodbye(renderer, chat, chat.persona, session, history_file)
        return True

    elif command == "/help":
        _show_help(renderer)

    elif command == "/reset":
        chat.reset()
        session.turn_count = 0
        renderer.render_status("🔄 Conversation history cleared.")

    elif command == "/persona":
        if not arg:
            presets = list_presets()
            renderer.render_status(f"Available personas: {', '.join(presets)}")
            renderer.render_status("Usage: /persona <name> or /persona-file <path>")
        else:
            try:
                new_persona = load_preset(arg)
                chat.persona = new_persona
                renderer.render_status(f"🎭 Switched persona to: {new_persona.display_name}")
            except FileNotFoundError:
                renderer.render_error(f"Persona '{arg}' not found. Use /persona list to see available.")

    elif command == "/persona-file":
        if not arg:
            renderer.render_status("Usage: /persona-file <path/to/persona.yaml>")
        else:
            try:
                new_persona = load_persona_from_file(Path(arg))
                chat.persona = new_persona
                renderer.render_status(f"🎭 Loaded custom persona: {new_persona.display_name}")
            except Exception as e:
                renderer.render_error(str(e))

    elif command == "/backend":
        if not arg:
            available = BackendRegistry.list_backends()
            renderer.render_status(f"Available backends: {', '.join(available)}")
            renderer.render_status("Usage: /backend <name>")
        else:
            try:
                # Note: backend switching requires re-creating NekoChat
                renderer.render_status(f"💡 Backend switching during chat is not yet supported. Restart with --backend {arg}")
            except Exception as e:
                renderer.render_error(str(e))

    elif command == "/system":
        renderer.render_markdown("## System Prompt\n")
        renderer.render_markdown(chat.system_prompt)

    elif command == "/save":
        filename = arg or f"nekocat-session-{session.id}.jsonl"
        path = Path(filename)
        if history_file:
            renderer.render_status(f"📁 History is being saved to: {history_file}")
        else:
            # Save current history
            with open(path, "w", encoding="utf-8") as f:
                for msg in chat.history.messages:
                    f.write(msg.model_dump_json() + "\n")
            renderer.render_status(f"📁 History saved to: {path.resolve()}")

    elif command == "/history":
        count = len(chat.history)
        tokens = chat.history.estimated_tokens
        renderer.render_status(f"📝 {count} messages in history (~{tokens} tokens)")

    else:
        renderer.render_error(f"Unknown command: {command}. Type /help for available commands.")

    return False


def _show_help(renderer: Renderer) -> None:
    """Show the help text."""
    help_text = """
## 🐱 NekoChat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show this help |
| `/reset` | Clear conversation history |
| `/persona <name>` | Switch to a different persona |
| `/persona-file <path>` | Load a custom persona YAML |
| `/backend <name>` | Show backend info |
| `/system` | Show the current system prompt |
| `/history` | Show conversation stats |
| `/save [file]` | Save conversation to file |
| `/exit`, `/quit` | Goodbye! |

**Tip:** Press Ctrl+C to exit.
"""
    renderer.render_markdown(help_text)


async def _say_goodbye(
    renderer: Renderer,
    chat: NekoChat,
    persona: PersonaProfile,
    session: ChatSession,
    history_file: Optional[Path],
) -> None:
    """Print a goodbye message. Don't call the API for this — keep it snappy."""
    goodbye = "喵~ 再见啦！下次再来找小咪玩哦！nya~"
    renderer.render_neko_message(f"**{persona.name}:** {goodbye}")
    if history_file and chat.history:
        renderer.render_status(f"📁 Session saved to: {history_file}")


# ——— History persistence ———

def _save_turn(path: Path, user_msg: str, neko_msg: str, turn: int) -> None:
    """Append a conversation turn to a JSONL history file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "turn": turn,
        "timestamp": datetime.now().isoformat(),
        "user": user_msg,
        "assistant": neko_msg,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
