"""Tests for MockBackend."""

from __future__ import annotations

import pytest
from nekocat.backends.mock import MockBackend
from nekocat.backends.base import GenerationRequest, GenerationResponse


@pytest.fixture
def mock() -> MockBackend:
    return MockBackend()


@pytest.mark.asyncio
async def test_generate_returns_response(mock: MockBackend) -> None:
    resp = await mock.generate(GenerationRequest(
        messages=[{"role": "user", "content": "Hello"}],
    ))
    assert isinstance(resp, GenerationResponse)
    assert len(resp.text) > 0
    assert resp.finish_reason == "stop"


@pytest.mark.asyncio
async def test_generate_keyword_match(mock: MockBackend) -> None:
    resp = await mock.generate(GenerationRequest(
        messages=[{"role": "user", "content": "摸摸头"}],
    ))
    assert "摸摸" in resp.text or "呼噜" in resp.text


@pytest.mark.asyncio
async def test_stream_yields_tokens(mock: MockBackend) -> None:
    tokens: list[str] = []
    async for token in mock.stream(GenerationRequest(
        messages=[{"role": "user", "content": "你好"}],
    )):
        tokens.append(token)

    assert len(tokens) > 0
    full = "".join(tokens)
    # Should contain a catgirl greeting
    assert any(kw in full for kw in ["喵", "nya", "小咪"])


@pytest.mark.asyncio
async def test_stream_assembles_to_generate(mock: MockBackend) -> None:
    """Streaming a request should produce the same text as generate."""
    req = GenerationRequest(messages=[{"role": "user", "content": "你好"}])

    # Both generate and stream use the same keyword matching
    resp = await mock.generate(req)

    tokens: list[str] = []
    async for token in mock.stream(req):
        tokens.append(token)

    assert "".join(tokens) == resp.text


@pytest.mark.asyncio
async def test_stream_instant_with_zero_delay() -> None:
    mock = MockBackend(delay=0)
    tokens: list[str] = []
    async for token in mock.stream(GenerationRequest(
        messages=[{"role": "user", "content": "你好"}],
    )):
        tokens.append(token)
    assert len(tokens) > 0
