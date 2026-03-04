"""ConversationService: チャット会話のユースケース制御。"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any, Optional

from app.chat.domain.models import Conversation, Message
from app.domain.exceptions import NotFoundException

logger = logging.getLogger(__name__)


class ConversationService:
    """会話セッション管理のアプリケーションサービス。

    会話の作成・取得・削除とメッセージ送受信（SSEストリーミング）を管理する。
    """

    def __init__(
        self,
        conversation_repo: Any,
        message_repo: Any,
        agent_workflow: Optional[Any] = None,
    ) -> None:
        self._conversation_repo = conversation_repo
        self._message_repo = message_repo
        self._agent_workflow = agent_workflow

    async def create_conversation(self, title: Optional[str] = None) -> Conversation:
        """新しい会話セッションを作成する。"""
        return await self._conversation_repo.create(title=title)

    async def get_conversation(self, conversation_id: str) -> Conversation:
        """会話セッションを取得する。

        Raises:
            NotFoundException: 会話が存在しない、または論理削除済みの場合。
        """
        conversation = await self._conversation_repo.get_by_id(conversation_id)
        if conversation is None or conversation.is_deleted():
            raise NotFoundException(f"会話 {conversation_id} が見つかりません")
        return conversation

    async def delete_conversation(self, conversation_id: str) -> None:
        """会話セッションを論理削除する。"""
        await self._conversation_repo.soft_delete(conversation_id)

    async def send_message_stream(
        self,
        conversation_id: str,
        content: str,
    ) -> AsyncIterator[dict]:
        """ユーザーメッセージを送信し、エージェント応答をSSEイベントとして yield する。

        Yields:
            dict: SSEイベント（type: "message_start" | "chunk" | "tool_call" | "tool_result" | "done" | "error"）
        """
        # ユーザーメッセージをDBに保存
        user_msg = await self._message_repo.create(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )

        # 会話履歴を取得してエージェントに渡す
        history = await self._message_repo.list_by_conversation(conversation_id)
        messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

        if self._agent_workflow is None:
            yield {"type": "error", "error": "エージェントワークフローが設定されていません"}
            return

        # エージェントワークフローを実行してストリーミング
        assistant_content_parts: list[str] = []
        try:
            async for event in self._agent_workflow.run_stream(
                conversation_id=conversation_id,
                messages=messages,
            ):
                if event.get("type") == "chunk":
                    assistant_content_parts.append(event.get("content", ""))
                yield event
        except Exception as e:
            logger.error("send_message_stream_error: %s", str(e))
            yield {"type": "error", "error": f"メッセージ送信エラー: {e}"}
            return

        # エージェント応答をDBに保存
        if assistant_content_parts:
            assistant_content = "".join(assistant_content_parts)
            await self._message_repo.create(
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_content,
            )
            # 会話の最終更新日時を更新
            await self._conversation_repo.update_timestamp(conversation_id)
