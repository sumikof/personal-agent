"""チャットAPIルーター: 会話管理・SSEストリーミングエンドポイント。"""
from __future__ import annotations

import inspect
import json
import logging
from collections.abc import AsyncIterator
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.chat.service import ConversationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/conversations", tags=["chat"])


async def event_generator(
    conversation_id: str,
    content: str,
    service: ConversationService,
) -> AsyncIterator[str]:
    """SSEイベントジェネレータ。

    ConversationService.send_message_stream のイベントを
    'data: {JSON}\\n\\n' 形式に変換して yield する。
    最後に 'data: [DONE]\\n\\n' を送信する。

    Args:
        conversation_id: 会話セッションID
        content: ユーザーメッセージ内容
        service: ConversationService インスタンス

    Yields:
        str: SSEフォーマット文字列
    """
    try:
        stream = service.send_message_stream(conversation_id, content)
        # AsyncMock はコルーチンを返すため、inspect でチェックして await する
        if inspect.iscoroutine(stream):
            stream = await stream
        async for event in stream:
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
    except Exception as e:
        logger.error("event_generator_error: %s", str(e))
        error_event = {"type": "error", "error": f"ストリーミングエラー: {e}"}
        yield f"data: {json.dumps(error_event, ensure_ascii=False)}\n\n"
    finally:
        yield "data: [DONE]\n\n"


@router.post("", status_code=201)
async def create_conversation(
    body: dict[str, Any] = {},
    service: ConversationService = Depends(),
) -> dict:
    """会話セッションを新規作成する。"""
    title = body.get("title") if body else None
    conversation = await service.create_conversation(title=title)
    return {
        "data": {
            "id": str(conversation.id),
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        }
    }


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    body: dict[str, Any],
    service: ConversationService = Depends(),
) -> StreamingResponse:
    """メッセージを送信してSSEストリームで応答を返す。"""
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=422, detail="content は必須です")

    return StreamingResponse(
        event_generator(conversation_id, content, service),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: str,
    service: ConversationService = Depends(),
) -> None:
    """会話セッションを論理削除する。"""
    await service.delete_conversation(conversation_id)
