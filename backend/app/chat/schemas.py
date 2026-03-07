"""チャットAPIのPydanticスキーマ定義。"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ConversationCreateRequest(BaseModel):
    """会話作成リクエスト。"""

    title: Optional[str] = None


class ConversationResponse(BaseModel):
    """会話レスポンス。"""

    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime


class MessageSendRequest(BaseModel):
    """メッセージ送信リクエスト。"""

    content: str


class SSEEvent(BaseModel):
    """SSEイベントスキーマ。"""

    type: str
    content: Optional[str] = None
    tool: Optional[str] = None
    tool_input: Optional[dict] = None
    result: Optional[dict] = None
    message_id: Optional[str] = None
    error: Optional[str] = None
