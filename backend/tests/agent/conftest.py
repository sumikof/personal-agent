"""agent テストの共通フィクスチャ。"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.tools.registry import ToolRegistry
from app.agent.workflow import AgentWorkflow
from app.integration.claude import ClaudeAPIClient


@pytest.fixture
def tool_registry() -> ToolRegistry:
    """空の ToolRegistry フィクスチャ。"""
    return ToolRegistry()


@pytest.fixture
def mock_claude_client() -> MagicMock:
    """ClaudeAPIClient のモックフィクスチャ。"""
    client = MagicMock(spec=ClaudeAPIClient)

    async def mock_stream(*args, **kwargs):
        yield {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "こんにちは"}}
        yield {"type": "message_stop"}

    client.create_message_stream = AsyncMock(return_value=mock_stream())
    return client


@pytest.fixture
def agent_workflow(tool_registry: ToolRegistry, mock_claude_client: MagicMock) -> AgentWorkflow:
    """AgentWorkflow フィクスチャ。"""
    return AgentWorkflow(tool_registry=tool_registry, claude_client=mock_claude_client)
