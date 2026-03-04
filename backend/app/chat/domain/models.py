"""チャット機能のドメインモデル。"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


@dataclass
class Conversation:
    """会話セッションのドメインエンティティ。"""

    id: uuid.UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    def is_deleted(self) -> bool:
        """論理削除済みかどうかを返す。"""
        return self.deleted_at is not None


@dataclass
class Message:
    """メッセージのドメインエンティティ。"""

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str  # "user" | "assistant" | "tool" | "system"
    content: str
    created_at: datetime
    tool_calls: Optional[list[dict]] = None
