"""チャットリポジトリ: 会話・メッセージの永続化インターフェース定義。

このモジュールはリポジトリの抽象基底クラスを定義する。
実装はインフラストラクチャ層（SQLAlchemy）またはテスト用インメモリ実装で提供される。
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from app.chat.domain.models import Conversation, Message


class ConversationRepository(ABC):
    """会話セッションのリポジトリ抽象基底クラス。"""

    @abstractmethod
    async def create(self, title: Optional[str] = None) -> Conversation:
        """会話を新規作成して返す。"""

    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """IDで会話を取得する。存在しない場合は None を返す。"""

    @abstractmethod
    async def list_all(self, limit: int = 20, offset: int = 0) -> list[Conversation]:
        """論理削除されていない会話一覧を返す。"""

    @abstractmethod
    async def soft_delete(self, conversation_id: str) -> None:
        """会話を論理削除する（deleted_at を設定）。"""

    @abstractmethod
    async def update_timestamp(self, conversation_id: str) -> None:
        """会話の updated_at を現在時刻に更新する。"""


class MessageRepository(ABC):
    """メッセージのリポジトリ抽象基底クラス。"""

    @abstractmethod
    async def create(
        self,
        conversation_id: str,
        role: str,
        content: str,
    ) -> Message:
        """メッセージを新規作成して返す。"""

    @abstractmethod
    async def list_by_conversation(self, conversation_id: str) -> list[Message]:
        """指定された会話のメッセージ一覧を時系列順で返す。"""

    @abstractmethod
    async def save_tool_call(
        self,
        message_id: str,
        tool_name: str,
        tool_input: dict,
        tool_output: dict,
        status: str = "success",
    ) -> None:
        """ツール呼び出しの記録を保存する。"""
