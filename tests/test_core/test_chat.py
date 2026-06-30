"""Tests for NekoChat core orchestrator."""

from __future__ import annotations

import pytest
from nekocat.backends.mock import MockBackend
from nekocat.core.chat import NekoChat
from nekocat.core.session import ChatSession
from nekocat.persona.models import PersonaProfile


@pytest.fixture
def chat(mock_persona: PersonaProfile) -> NekoChat:
    return NekoChat(persona=mock_persona, backend=MockBackend())


@pytest.fixture
def session() -> ChatSession:
    return ChatSession()


class TestSystemPrompt:
    def test_system_prompt_contains_name(self, chat: NekoChat) -> None:
        prompt = chat.system_prompt
        assert "测试喵" in prompt

    def test_system_prompt_contains_interjections(self, chat: NekoChat) -> None:
        prompt = chat.system_prompt
        assert "喵~" in prompt


@pytest.mark.asyncio
class TestSend:
    async def test_send_returns_string(self, chat: NekoChat, session: ChatSession) -> None:
        resp = await chat.send("Hello!", session)
        assert isinstance(resp, str)
        assert len(resp) > 0

    async def test_send_increments_turn(self, chat: NekoChat, session: ChatSession) -> None:
        assert session.turn_count == 0
        await chat.send("msg1", session)
        assert session.turn_count == 1
        await chat.send("msg2", session)
        assert session.turn_count == 2

    async def test_send_adds_to_history(self, chat: NekoChat, session: ChatSession) -> None:
        await chat.send("Hello", session)
        assert len(chat.history) == 2  # user + assistant


@pytest.mark.asyncio
class TestStream:
    async def test_stream_yields_tokens(self, chat: NekoChat, session: ChatSession) -> None:
        tokens: list[str] = []
        async for token in chat.stream("Hello~", session):
            tokens.append(token)
        assert len(tokens) > 0

    async def test_stream_increments_turn(self, chat: NekoChat, session: ChatSession) -> None:
        async for _ in chat.stream("Hi", session):
            pass
        assert session.turn_count == 1

    async def test_stream_adds_to_history(self, chat: NekoChat, session: ChatSession) -> None:
        async for _ in chat.stream("Hello", session):
            pass
        assert len(chat.history) == 2


class TestReset:
    def test_reset_clears_history(self, chat: NekoChat, session: ChatSession) -> None:
        import asyncio

        async def _send() -> None:
            await chat.send("Hello", session)

        asyncio.run(_send())
        assert len(chat.history) == 2
        chat.reset()
        assert len(chat.history) == 0
