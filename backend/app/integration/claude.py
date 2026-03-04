"""Claude API クライアント（Anthropic SDK ラッパー）。"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ClaudeAPIClient:
    """Anthropic SDK の非同期ラッパー。ストリーミング対応。"""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-opus-4-6",
        max_tokens: int = 4096,
        timeout: float = 30.0,
    ) -> None:
        self._api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        # 実際のAnthropicクライアントは遅延初期化（テスト時モック差し替え可能）
        self._client: Any = None

    def _get_client(self) -> Any:
        """Anthropic 非同期クライアントを遅延初期化して返す。"""
        if self._client is None:
            try:
                import anthropic  # noqa: PLC0415
                self._client = anthropic.AsyncAnthropic(api_key=self._api_key)
            except ImportError:
                raise RuntimeError("anthropic パッケージがインストールされていません")
        return self._client

    async def create_message_stream(
        self,
        messages: list[dict],
        tools: Optional[list[dict]] = None,
        system: Optional[str] = None,
    ) -> AsyncIterator[dict]:
        """ストリーミング形式でメッセージを送信し、イベントを yield する。"""
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
        }
        if tools:
            kwargs["tools"] = tools
        if system:
            kwargs["system"] = system

        logger.info("claude_api_stream_start model=%s", self.model)
        async with client.messages.stream(**kwargs) as stream:
            async for event in stream:
                yield event
