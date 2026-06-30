"""NekoChat — central orchestrator wiring persona + backend + history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncIterator

from nekocat.backends.base import Backend, GenerationRequest
from nekocat.core.history import ConversationHistory, Message
from nekocat.core.session import ChatSession
from nekocat.persona.models import PersonaProfile
from nekocat.persona.prompts import build_system_prompt


@dataclass
class NekoChat:
    """Central orchestrator for a catgirl conversation.

    Composes persona (who), backend (how), and history (what was said).
    This is the primary API users interact with.

    Usage:
        persona = load_preset("classic_neko")
        backend = BackendRegistry.get("mock")
        chat = NekoChat(persona=persona, backend=backend)

        session = ChatSession()
        async for token in chat.stream("你好~", session):
            print(token, end="")
    """

    persona: PersonaProfile
    backend: Backend
    history: ConversationHistory = field(default_factory=ConversationHistory)

    @property
    def system_prompt(self) -> str:
        """The current system prompt (generated from persona on each access)."""
        return build_system_prompt(self.persona)

    async def send(self, user_message: str, session: ChatSession) -> str:
        """Send a message and get the full response (non-streaming).

        Args:
            user_message: The user's input text.
            session: The current conversation session.

        Returns:
            The catgirl's complete response text.
        """
        self._append_user_message(user_message)
        response = await self.backend.generate(self._build_request())
        self._append_assistant_message(response.text)
        session.turn_count += 1
        return response.text

    async def stream(self, user_message: str, session: ChatSession) -> AsyncIterator[str]:
        """Send a message and stream the response token by token.

        Args:
            user_message: The user's input text.
            session: The current conversation session.

        Yields:
            Text tokens as they are generated.
        """
        self._append_user_message(user_message)
        full_response: list[str] = []

        async for token in self.backend.stream(self._build_request()):
            full_response.append(token)
            yield token

        complete = "".join(full_response)
        self._append_assistant_message(complete)
        session.turn_count += 1

    def reset(self) -> None:
        """Clear the conversation history, keeping persona and backend."""
        self.history.clear()

    # ——— Internal helpers ———

    def _build_request(self) -> GenerationRequest:
        """Build a GenerationRequest from current state."""
        return GenerationRequest(
            messages=self.history.to_api_format(system_prompt=self.system_prompt),
            max_tokens=1024,
            temperature=0.9,
        )

    def _append_user_message(self, text: str) -> None:
        self.history.append(Message(role="user", content=text))

    def _append_assistant_message(self, text: str) -> None:
        self.history.append(Message(role="assistant", content=text))
