"""ConversationService の単体テスト（TDD: TC-BE-001〜TC-BE-008）。"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

import pytest

from app.chat.service import ConversationService
from app.chat.domain.models import Conversation, Message
from app.domain.exceptions import NotFoundException


# ---------------------------------------------------------------------------
# TC-BE-001: 会話新規作成（タイトルなし）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_conversation_without_title(conversation_service: ConversationService) -> None:
    """TC-BE-001: ConversationService.create_conversation(title=None) で Conversation が返される。"""
    # Given: DBが正常に動作している（fixtureで確保済み）

    # When
    result = await conversation_service.create_conversation(title=None)

    # Then
    assert result.id is not None
    assert result.title is None
    now = datetime.now(timezone.utc)
    assert abs((result.created_at - now).total_seconds()) < 5


# ---------------------------------------------------------------------------
# TC-BE-002: 会話新規作成（タイトルあり）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_conversation_with_title(conversation_service: ConversationService) -> None:
    """TC-BE-002: ConversationService.create_conversation(title='テスト会話') でタイトルが設定される。"""
    # Given / When
    result = await conversation_service.create_conversation(title="テスト会話")

    # Then
    assert result.title == "テスト会話"


# ---------------------------------------------------------------------------
# TC-BE-003: 存在しない会話の取得（異常系）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_conversation_not_found(conversation_service: ConversationService) -> None:
    """TC-BE-003: 存在しないIDでget_conversationするとNotFoundExceptionが raise される。"""
    # Given: 存在しないUUID
    fake_id = str(uuid.uuid4())

    # When / Then
    with pytest.raises(NotFoundException) as exc_info:
        await conversation_service.get_conversation(fake_id)
    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# TC-BE-004: 論理削除済み会話の取得（異常系）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_deleted_conversation_not_found(conversation_service: ConversationService) -> None:
    """TC-BE-004: 論理削除済みの会話を取得するとNotFoundExceptionが raise される。"""
    # Given: 会話を作成して論理削除
    conversation = await conversation_service.create_conversation(title=None)
    await conversation_service.delete_conversation(str(conversation.id))

    # When / Then
    with pytest.raises(NotFoundException):
        await conversation_service.get_conversation(str(conversation.id))


# ---------------------------------------------------------------------------
# TC-BE-005: メッセージ送信→エージェント応答（ツールなし）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_send_message_stream_no_tool_call(
    conversation_service_with_mock_agent: ConversationService,
) -> None:
    """TC-BE-005: ツール呼び出しなしの場合、chunk + done イベントが返される。"""
    # Given
    service = conversation_service_with_mock_agent
    conversation = await service.create_conversation()

    # When
    events: list[dict] = []
    async for event in service.send_message_stream(str(conversation.id), "はじめまして"):
        events.append(event)

    # Then: イベント順序確認
    event_types = [e["type"] for e in events]
    assert "message_start" in event_types
    assert "chunk" in event_types
    assert "done" in event_types

    # chunkのcontentを結合
    content = "".join(e.get("content", "") for e in events if e["type"] == "chunk")
    assert "こんにちは" in content


# ---------------------------------------------------------------------------
# TC-BE-006: メッセージ送信→ツール呼び出しあり（正常系）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_send_message_stream_with_tool_call(
    conversation_service_with_mock_agent_tool: ConversationService,
) -> None:
    """TC-BE-006: ツール呼び出しがある場合、tool_call + tool_result イベントが含まれる。"""
    # Given
    service = conversation_service_with_mock_agent_tool
    conversation = await service.create_conversation()

    # When
    events: list[dict] = []
    async for event in service.send_message_stream(str(conversation.id), "タスクを作成して"):
        events.append(event)

    # Then: ツール呼び出しイベントの確認
    tool_call_events = [e for e in events if e["type"] == "tool_call"]
    assert len(tool_call_events) >= 1
    assert tool_call_events[0]["tool"] == "create_issue"

    tool_result_events = [e for e in events if e["type"] == "tool_result"]
    assert len(tool_result_events) >= 1
    assert tool_result_events[0]["result"]["id"] == 123


# ---------------------------------------------------------------------------
# TC-BE-007: Claude API接続失敗（異常系）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_send_message_claude_api_error(
    conversation_service_with_mock_agent_error: ConversationService,
) -> None:
    """TC-BE-007: Claude API エラー時は error イベントが yield され、例外は伝播しない。"""
    # Given
    service = conversation_service_with_mock_agent_error
    conversation = await service.create_conversation()

    # When
    events: list[dict] = []
    async for event in service.send_message_stream(str(conversation.id), "テスト"):
        events.append(event)

    # Then
    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) >= 1
    error_msg = error_events[0].get("error", "")
    assert "AI" in error_msg or "通信" in error_msg or "エラー" in error_msg


# ---------------------------------------------------------------------------
# TC-BE-008: 会話削除（正常系）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_delete_conversation(conversation_service: ConversationService) -> None:
    """TC-BE-008: 会話削除後にget_conversationするとNotFoundExceptionが発生する。"""
    # Given: 有効な会話が存在する
    conversation = await conversation_service.create_conversation(title=None)
    conv_id = str(conversation.id)

    # When
    await conversation_service.delete_conversation(conv_id)

    # Then
    with pytest.raises(NotFoundException):
        await conversation_service.get_conversation(conv_id)
