"""Tests for ConversationHistory."""

from __future__ import annotations

import pytest
from nekocat.core.history import ConversationHistory, Message


@pytest.fixture
def history() -> ConversationHistory:
    return ConversationHistory(max_messages=10, max_tokens=2000)


class TestAppend:
    def test_append_adds_message(self, history: ConversationHistory) -> None:
        history.append(Message(role="user", content="Hello"))
        assert len(history) == 1

    def test_append_respects_max_messages(self, history: ConversationHistory) -> None:
        history.max_messages = 3
        for i in range(5):
            history.append(Message(role="user", content=f"msg {i}"))
        assert len(history) == 3

    def test_oldest_evicted_first(self, history: ConversationHistory) -> None:
        history.max_messages = 2
        history.append(Message(role="user", content="first"))
        history.append(Message(role="user", content="second"))
        history.append(Message(role="user", content="third"))
        msgs = history.messages
        assert msgs[0].content == "second"
        assert msgs[1].content == "third"


class TestTrim:
    def test_trim_preserves_system(self, history: ConversationHistory) -> None:
        history.max_messages = 3
        history.append(Message(role="system", content="I am a cat"))
        for i in range(5):
            history.append(Message(role="user", content=f"msg {i}"))
        msgs = history.messages
        # System message should still be there
        assert msgs[0].role == "system"
        assert len(history) == 3


class TestClear:
    def test_clear_removes_all(self, history: ConversationHistory) -> None:
        history.append(Message(role="user", content="Hi"))
        history.append(Message(role="assistant", content="Hello!"))
        history.clear()
        assert len(history) == 0
        assert not history


class TestToApiFormat:
    def test_basic_conversion(self, history: ConversationHistory) -> None:
        history.append(Message(role="user", content="Hi"))
        history.append(Message(role="assistant", content="Hello!"))

        result = history.to_api_format()
        assert len(result) == 2
        assert result[0] == {"role": "user", "content": "Hi"}
        assert result[1] == {"role": "assistant", "content": "Hello!"}

    def test_with_system_prompt(self, history: ConversationHistory) -> None:
        history.append(Message(role="user", content="Ping"))

        result = history.to_api_format(system_prompt="You are a cat.")
        assert len(result) == 2
        assert result[0] == {"role": "system", "content": "You are a cat."}
        assert result[1] == {"role": "user", "content": "Ping"}


class TestTokenEstimation:
    def test_empty_history_zero_tokens(self, history: ConversationHistory) -> None:
        assert history.estimated_tokens == 0

    def test_nonzero_tokens(self, history: ConversationHistory) -> None:
        history.append(Message(role="user", content="Hello, how are you?"))
        assert history.estimated_tokens > 0
