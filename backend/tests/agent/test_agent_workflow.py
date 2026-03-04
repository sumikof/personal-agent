"""AgentWorkflow の単体テスト（TDD: TC-BE-009〜TC-BE-011）。"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.workflow import AgentWorkflow
from app.agent.state import AgentState
from app.agent.tools.registry import ToolRegistry
from app.integration.claude import ClaudeAPIClient


# ---------------------------------------------------------------------------
# TC-BE-009: LangGraphワークフロー初期化（正常系）
# ---------------------------------------------------------------------------
def test_agent_workflow_initializes_without_error(
    tool_registry: ToolRegistry,
    mock_claude_client: MagicMock,
) -> None:
    """TC-BE-009: AgentWorkflow() を初期化してもエラーが発生しない。"""
    # Given / When
    workflow = AgentWorkflow(tool_registry=tool_registry, claude_client=mock_claude_client)

    # Then
    assert workflow is not None
    assert workflow._graph is not None


# ---------------------------------------------------------------------------
# TC-BE-010: tool_router_nodeのルーティング（ツールあり）
# ---------------------------------------------------------------------------
def test_tool_router_with_tool_calls(
    agent_workflow: AgentWorkflow,
) -> None:
    """TC-BE-010: tool_callsがある場合、'tool_executor_node' が返される。"""
    # Given
    state = AgentState(
        messages=[],
        tool_calls=[{"id": "call_001", "name": "create_issue", "input": {}}],
        intermediate_steps=[],
        conversation_id="test-id",
        streaming_events=[],
    )

    # When
    result = agent_workflow.tool_router_node(state)

    # Then
    assert result == "tool_executor_node"


# ---------------------------------------------------------------------------
# TC-BE-011: tool_router_nodeのルーティング（ツールなし）
# ---------------------------------------------------------------------------
def test_tool_router_without_tool_calls(
    agent_workflow: AgentWorkflow,
) -> None:
    """TC-BE-011: tool_callsがNoneの場合、'__end__' が返される。"""
    # Given
    state = AgentState(
        messages=[],
        tool_calls=None,
        intermediate_steps=[],
        conversation_id="test-id",
        streaming_events=[],
    )

    # When
    result = agent_workflow.tool_router_node(state)

    # Then
    assert result == "__end__"
