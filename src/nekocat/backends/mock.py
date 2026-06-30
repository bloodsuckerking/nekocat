"""Mock backend — returns canned responses for testing, no API key needed."""

from __future__ import annotations

import asyncio
import random
from typing import AsyncIterator

from nekocat.backends.base import (
    Backend,
    BackendCapabilities,
    GenerationRequest,
    GenerationResponse,
)


# Cute canned responses in the catgirl style
_MOCK_RESPONSES = [
    "喵~ 你好呀！今天想和小咪聊什么呢？诶嘿嘿~",
    "喵呜~ 这个问题好有趣的说！让小咪想想看... 嗯... 小咪觉得应该是这样的呢~",
    "呼呼~ 主人来找小咪玩耍了吗？小咪好开心的说！喵~",
    "诶嘿嘿~ 小咪虽然不太懂这个，但是小咪会努力回答的说！喵呜~",
    "喵~ 是的说！就是这个意思呢！小咪也觉得是这样 nya~",
]


class MockBackend(Backend):
    """Fake backend for testing and offline development.

    Returns a random catgirl response. Supports stream mode by
    yielding the response char-by-char with a configurable delay.
    """

    def __init__(
        self,
        model: str = "mock-neko-v1",
        delay: float = 0.005,
        **kwargs,
    ) -> None:
        super().__init__()
        self.model = model
        self.delay = delay
        self._capabilities = BackendCapabilities(
            streaming=True,
            max_context_tokens=4000,
            supports_system_prompt=True,
        )

    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Return a random canned response."""
        full_text = self._pick_response(request)
        return GenerationResponse(
            text=full_text,
            finish_reason="stop",
            usage={
                "prompt_tokens": sum(
                    len(m.get("content", "")) // 4 for m in request.messages
                ),
                "completion_tokens": len(full_text) // 4,
            },
        )

    async def stream(self, request: GenerationRequest) -> AsyncIterator[str]:
        """Stream a canned response character by character."""
        full_text = self._pick_response(request)
        for char in full_text:
            yield char
            if self.delay > 0:
                await asyncio.sleep(self.delay)

    def _pick_response(self, request: GenerationRequest) -> str:
        """Pick a response, optionally influenced by the last user message."""
        last_user = ""
        for msg in reversed(request.messages):
            if msg.get("role") == "user":
                last_user = msg.get("content", "")
                break

        # Simple keyword matching for more relevant responses
        keywords = {
            "你好": "喵~ 你好呀！欢迎来找小咪玩的说！今天过得好吗？诶嘿嘿~",
            "再见": "喵呜~ 要走了吗？好吧... 下次一定要再来找小咪玩哦！nya~",
            "天气": "喵~ 今天天气暖暖的，最适合在窗台上晒太阳打滚了呢！主人要不要一起来晒太阳？",
            "饿": "喵呜~ 小咪也饿了！有没有小鱼干给喵吃？用期待的眼神看着主人...",
            "喜欢": "诶嘿嘿~ 小咪也最喜欢主人了！喵~ 所以要多摸摸头哦！",
            "摸摸": "喵呜~~~ 好舒服呀！小咪最喜欢被摸头了的说！可以再多摸一下吗？呼噜呼噜...",
            "晚安": "喵~ 晚安呢！小咪会守在你的身边，做个好梦哦... 呼...",
            "帮助": "喵！有什么困难吗？小咪虽然不太厉害，但一定会努力帮忙的说！喵呜~",
        }

        for kw, response in keywords.items():
            if kw in last_user:
                return response

        # Fall back to random
        return random.choice(_MOCK_RESPONSES)
