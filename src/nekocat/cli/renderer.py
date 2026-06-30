"""Rich-based rendering for the CLI — headers, messages, streaming typewriter."""

from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator, Optional

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

from nekocat.core.session import ChatSession
from nekocat.persona.models import PersonaProfile

# ——— Color themes ———

_COLOR_THEMES: dict[str, dict[str, str]] = {
    "pink": {
        "header_border": "hot_pink",
        "neko_name": "hot_pink",
        "neko_border": "plum4",
        "user_color": "cyan",
        "accent": "pink1",
        "dim": "grey66",
    },
    "purple": {
        "header_border": "medium_purple",
        "neko_name": "medium_purple",
        "neko_border": "purple4",
        "user_color": "green",
        "accent": "orchid",
        "dim": "grey66",
    },
    "mint": {
        "header_border": "spring_green2",
        "neko_name": "spring_green2",
        "neko_border": "dark_sea_green4",
        "user_color": "cyan",
        "accent": "medium_spring_green",
        "dim": "grey66",
    },
    "sunset": {
        "header_border": "dark_orange",
        "neko_name": "orange1",
        "neko_border": "orange4",
        "user_color": "yellow",
        "accent": "gold1",
        "dim": "grey66",
    },
}


class Renderer:
    """Terminal renderer using Rich for styled output.

    Handles: header panels, user/neko message formatting,
    streaming typewriter effect, and error display.
    """

    def __init__(
        self,
        color_theme: str = "pink",
        typewriter_speed: float = 0.02,
    ) -> None:
        self.console = Console()
        self.theme = _COLOR_THEMES.get(color_theme, _COLOR_THEMES["pink"])
        self.typewriter_speed = typewriter_speed

    # ——— Header ———

    def render_header(
        self,
        session: ChatSession,
        persona: PersonaProfile,
        backend_name: str,
        model: str = "",
    ) -> None:
        """Render the top-of-screen header panel."""
        theme = self.theme

        parts = []
        # Character name
        parts.append(f"[bold {theme['neko_name']}]🐱 {persona.display_name}[/]")
        # Backend info
        backend_info = backend_name
        if model:
            backend_info += f"  ·  {model}"
        parts.append(f"[{theme['dim']}]{backend_info}[/]")
        # Turn count
        parts.append(f"[{theme['dim']}]turn {session.turn_count}[/]")

        header_line = "  │  ".join(parts)
        rule_text = f"  {header_line}  [{theme['dim']}]│  /help for commands[/]"

        panel = Panel(
            rule_text,
            border_style=theme["header_border"],
            padding=(0, 1),
            width=self.console.width,
        )
        self.console.print(panel)

    # ——— Messages ———

    def render_user_message(self, text: str) -> None:
        """Render a user message (right-aligned, cyan)."""
        theme = self.theme
        display = f"[bold {theme['user_color']}]You:[/] {text}"
        self.console.print(display)

    def render_neko_message(self, text: str) -> None:
        """Render a complete (non-streamed) neko message in a panel."""
        theme = self.theme
        panel = Panel(
            Markdown(text),
            border_style=theme["neko_border"],
            padding=(0, 1),
        )
        self.console.print(panel)

    async def render_neko_stream(
        self,
        tokens: AsyncIterator[str],
        persona_name: Optional[str] = None,
    ) -> str:
        """Stream-render neko tokens with a typewriter effect.

        Each new token is appended to a Live-updating Panel.

        Args:
            tokens: Async iterator yielding string tokens.
            persona_name: Character name for the label.

        Returns:
            The complete assembled response text.
        """
        theme = self.theme
        name = persona_name or "Neko"
        buffer: list[str] = []

        # Create a Live display that will auto-refresh
        with Live(
            self._build_stream_panel("", name, theme),
            console=self.console,
            refresh_per_second=60,
            transient=False,
        ) as live:
            async for token in tokens:
                buffer.append(token)
                # Apply typewriter delay
                if self.typewriter_speed > 0:
                    await asyncio.sleep(self.typewriter_speed)

                text = "".join(buffer)
                live.update(self._build_stream_panel(text, name, theme))

            # Final render
            full_text = "".join(buffer)
            live.update(self._build_stream_panel(full_text, name, theme))

        return "".join(buffer)

    def _build_stream_panel(
        self, text: str, name: str, theme: dict[str, str]
    ) -> Panel:
        """Build a panel for stream rendering."""
        if text:
            content = Markdown(text)
        else:
            content = Text("...", style=theme["dim"])

        return Panel(
            content,
            title=f"[bold {theme['neko_name']}]{name}:[/]",
            title_align="left",
            border_style=theme["neko_border"],
            padding=(0, 1),
        )

    # ——— System / status ———

    def render_error(self, text: str) -> None:
        """Render an error message in a red panel."""
        panel = Panel(
            f"[bold red]Error:[/] {text}",
            border_style="red",
            padding=(0, 1),
        )
        self.console.print(panel)

    def render_status(self, text: str) -> None:
        """Render a dim status line."""
        self.console.print(f"[{self.theme['dim']}]{text}[/]")

    def render_markdown(self, text: str) -> None:
        """Render arbitrary markdown."""
        self.console.print(Markdown(text))

    def render_blank_line(self) -> None:
        """Print a blank line."""
        self.console.print()
