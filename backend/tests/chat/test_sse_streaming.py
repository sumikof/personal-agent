"""SSEイベントジェネレータの単体テスト（TDD: TC-BE-014〜TC-BE-015）。"""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.chat.router import event_generator


# ---------------------------------------------------------------------------
# TC-BE-014: SSEイベントジェネレータ（正常系）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_event_generator_format(mock_conversation_service: MagicMock) -> None:
    """TC-BE-014: event_generator が 'data: {JSON}\n\n' 形式で出力し、最後に [DONE] を送る。"""
    # Given
    async def _mock_stream(*args, **kwargs):
        yield {"type": "chunk", "content": "テスト"}
        yield {"type": "done", "message_id": "msg-001"}

    mock_conversation_service.send_message_stream = AsyncMock(return_value=_mock_stream())

    # When
    lines: list[str] = []
    async for line in event_generator("conv-id", "テスト入力", mock_conversation_service):
        lines.append(line)

    # Then
    assert len(lines) >= 2
    assert lines[0].startswith("data: ")
    # JSON としてパースできる
    data = json.loads(lines[0][6:].strip())
    assert data["type"] == "chunk"
    assert lines[-1] == "data: [DONE]\n\n"


# ---------------------------------------------------------------------------
# TC-BE-015: SSEチャンク分割受信（分割ストリームテスト）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_event_generator_multiple_chunks(mock_conversation_service: MagicMock) -> None:
    """TC-BE-015: 複数chunkイベントが個別に yield される。"""
    # Given: 1文字ずつ3つのchunkを送る
    async def _mock_stream(*args, **kwargs):
        for char in ["タ", "ス", "ク"]:
            yield {"type": "chunk", "content": char}
        yield {"type": "done", "message_id": "msg-002"}

    mock_conversation_service.send_message_stream = AsyncMock(return_value=_mock_stream())

    # When
    lines: list[str] = []
    async for line in event_generator("conv-id", "テスト", mock_conversation_service):
        lines.append(line)

    # Then: 3つのchunk + done + [DONE]
    chunk_lines = [l for l in lines if "chunk" in l]
    assert len(chunk_lines) == 3

    # 内容を結合すると "タスク"
    chunks = [json.loads(l[6:].strip())["content"] for l in chunk_lines]
    assert "".join(chunks) == "タスク"
