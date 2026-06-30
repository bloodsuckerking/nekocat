"""Conversation history — FIFO sliding-window context manager."""

from __future__ import annotations

import time
from typing import Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single message in the conversation history."""

    role: Literal["system", "user", "assistant"]
    content: str
    timestamp: float = Field(default_factory=time.time)


class ConversationHistory:
    """Sliding-window conversation history.

    Maintains a FIFO list of messages with both a message-count cap
    and a soft token-count ceiling. Oldest messages are evicted first.
    """

    def __init__(
        self,
        max_messages: int = 50,
        max_tokens: int = 8000,
    ) -> None:
        """Initialize conversation history.

        Args:
            max_messages: Hard cap on number of stored messages.
            max_tokens: Soft ceiling for estimated token count.
                        When exceeded, oldest non-system messages are evicted.
        """
        self.max_messages = max_messages
        self.max_tokens = max_tokens
        self._messages: list[Message] = []

    # ——— Properties ———

    @property
    def messages(self) -> list[Message]:
        """Return a copy of the current message list."""
        return list(self._messages)

    def __len__(self) -> int:
        return len(self._messages)

    def __bool__(self) -> bool:
        return len(self._messages) > 0

    # ——— Mutations ———

    def append(self, message: Message) -> None:
        """Add a message and trim if limits are exceeded."""
        self._messages.append(message)
        self.trim()

    def trim(self) -> None:
        """Evict oldest messages until both limits are satisfied.

        System messages are preserved at the front of the list.
        Eviction is FIFO: oldest user/assistant messages go first.
        """
        # Enforce message count cap
        while len(self._messages) > self.max_messages:
            self._evict_one()

        # Enforce token count soft cap
        while self.estimated_tokens > self.max_tokens and len(self._messages) > 1:
            self._evict_one()

    def clear(self) -> None:
        """Remove all messages."""
        self._messages.clear()

    # ——— Token estimation ———

    @property
    def estimated_tokens(self) -> int:
        """Rough estimate of total token count.

        Uses the heuristic: tokens ≈ characters / 4.
        For more accurate counting, integrate tiktoken in a future version.
        """
        total = 0
        for msg in self._messages:
            # Chinese characters are denser; count each char as ~1.5 tokens
            total += self._estimate_message_tokens(msg.content)
        return total

    @staticmethod
    def _estimate_message_tokens(text: str) -> int:
        """Estimate tokens for a string, treating CJK chars as higher density."""
        cjk_count = sum(1 for c in text if "一" <= c <= "鿿" or "぀" <= c <= "ヿ")
        other_count = len(text) - cjk_count
        return (cjk_count * 3) // 2 + other_count // 4

    # ——— API format conversion ———

    def to_api_format(self, system_prompt: str | None = None) -> list[dict[str, str]]:
        """Convert history to OpenAI-compatible message list.

        Args:
            system_prompt: If provided, prepended as a system message.
                           Use this instead of storing system messages in history.

        Returns:
            List of dicts with 'role' and 'content' keys.
        """
        result: list[dict[str, str]] = []

        if system_prompt:
            result.append({"role": "system", "content": system_prompt})

        for msg in self._messages:
            # Skip system messages already in history if we're injecting one
            if msg.role == "system" and system_prompt:
                continue
            result.append({"role": msg.role, "content": msg.content})

        return result

    # ——— Internal helpers ———

    def _evict_one(self) -> None:
        """Remove the oldest non-system message."""
        for i, msg in enumerate(self._messages):
            if msg.role != "system":
                self._messages.pop(i)
                return
        # Fallback: if all messages are system messages (shouldn't happen),
        # remove the oldest one anyway
        if self._messages:
            self._messages.pop(0)
