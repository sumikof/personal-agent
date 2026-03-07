"""chat テストの共通フィクスチャ。"""
from __future__ import annotations

import uuid
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.chat.service import ConversationService
from app.chat.repository import ConversationRepository, MessageRepository
from app.agent.workflow import AgentWorkflow
from app.agent.tools.registry import ToolRegistry
from app.integration.claude import ClaudeAPIClient


# ---------------------------------------------------------------------------
# リポジトリのインメモリモック
# ---------------------------------------------------------------------------

class InMemoryConversationRepository:
    """テスト用のインメモリ会話リポジトリ。"""

    def __init__(self) -> None:
        self._store: dict[str, dict] = {}

    async def create(self, title: str | None = None):
        from app.chat.domain.models import Conversation
        from datetime import datetime, timezone
        conv = Conversation(
            id=uuid.uuid4(),
            title=title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            deleted_at=None,
        )
        self._store[str(conv.id)] = conv
        return conv

    async def get_by_id(self, conversation_id: str):
        return self._store.get(conversation_id)

    async def list_all(self, limit: int = 20, offset: int = 0):
        items = list(self._store.values())
        return items[offset: offset + limit]

    async def soft_delete(self, conversation_id: str) -> None:
        from datetime import datetime, timezone
        if conversation_id in self._store:
            conv = self._store[conversation_id]
            conv.deleted_at = datetime.now(timezone.utc)

    async def update_timestamp(self, conversation_id: str) -> None:
        from datetime import datetime, timezone
        if conversation_id in self._store:
            self._store[conversation_id].updated_at = datetime.now(timezone.utc)


class InMemoryMessageRepository:
    """テスト用のインメモリメッセージリポジトリ。"""

    def __init__(self) -> None:
        self._store: list[dict] = []

    async def create(self, conversation_id: str, role: str, content: str):
        from app.chat.domain.models import Message
        from datetime import datetime, timezone
        msg = Message(
            id=uuid.uuid4(),
            conversation_id=uuid.UUID(conversation_id),
            role=role,
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        self._store.append(msg)
        return msg

    async def list_by_conversation(self, conversation_id: str):
        return [m for m in self._store if str(m.conversation_id) == conversation_id]

    async def save_tool_call(
        self,
        message_id: str,
        tool_name: str,
        tool_input: dict,
        tool_output: dict,
        status: str = "success",
    ) -> None:
        pass


# ---------------------------------------------------------------------------
# AgentWorkflow のモック
# ---------------------------------------------------------------------------

class MockAgentWorkflowNoTool:
    """ツール呼び出しなしのモックエージェントワークフロー。"""

    async def run_stream(self, conversation_id: str, messages: list) -> AsyncIterator[dict]:
        yield {"type": "message_start", "message_id": "msg-test-001"}
        yield {"type": "chunk", "content": "こんにちは！"}
        yield {"type": "done", "message_id": "msg-test-001"}


class MockAgentWorkflowWithTool:
    """ツール呼び出しありのモックエージェントワークフロー。"""

    async def run_stream(self, conversation_id: str, messages: list) -> AsyncIterator[dict]:
        yield {"type": "message_start", "message_id": "msg-test-002"}
        yield {"type": "tool_call", "tool": "create_issue", "input": {"title": "テストタスク"}}
        yield {"type": "tool_result", "tool": "create_issue", "result": {"id": 123, "title": "テストタスク"}}
        yield {"type": "chunk", "content": "タスクを作成しました。"}
        yield {"type": "done", "message_id": "msg-test-002"}


class MockAgentWorkflowError:
    """エラーを発生させるモックエージェントワークフロー。"""

    async def run_stream(self, conversation_id: str, messages: list) -> AsyncIterator[dict]:
        yield {"type": "error", "error": "AIとの通信に失敗しました"}


# ---------------------------------------------------------------------------
# フィクスチャ定義
# ---------------------------------------------------------------------------

@pytest.fixture
def conversation_service() -> ConversationService:
    """通常の ConversationService（AgentWorkflow なし）。"""
    return ConversationService(
        conversation_repo=InMemoryConversationRepository(),
        message_repo=InMemoryMessageRepository(),
        agent_workflow=None,
    )


@pytest.fixture
def conversation_service_with_mock_agent() -> ConversationService:
    """ツール呼び出しなしのエージェントワークフローを持つ ConversationService。"""
    return ConversationService(
        conversation_repo=InMemoryConversationRepository(),
        message_repo=InMemoryMessageRepository(),
        agent_workflow=MockAgentWorkflowNoTool(),
    )


@pytest.fixture
def conversation_service_with_mock_agent_tool() -> ConversationService:
    """ツール呼び出しありのエージェントワークフローを持つ ConversationService。"""
    return ConversationService(
        conversation_repo=InMemoryConversationRepository(),
        message_repo=InMemoryMessageRepository(),
        agent_workflow=MockAgentWorkflowWithTool(),
    )


@pytest.fixture
def conversation_service_with_mock_agent_error() -> ConversationService:
    """エラーを発生させるエージェントワークフローを持つ ConversationService。"""
    return ConversationService(
        conversation_repo=InMemoryConversationRepository(),
        message_repo=InMemoryMessageRepository(),
        agent_workflow=MockAgentWorkflowError(),
    )


@pytest.fixture
def mock_conversation_service() -> MagicMock:
    """ConversationService のモック（SSEテスト用）。"""
    return MagicMock(spec=ConversationService)
