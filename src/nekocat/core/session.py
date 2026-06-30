"""Chat session — per-conversation bookkeeping."""

from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class ChatSession:
    """Ephemeral per-conversation state.

    Allows a single NekoChat instance to serve multiple concurrent
    conversations (e.g., one per user in a chat room).
    """

    id: str = field(default_factory=lambda: uuid4().hex[:8])
    turn_count: int = 0
    metadata: dict = field(default_factory=dict)
