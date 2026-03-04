"""ToolRegistry の単体テスト（TDD: TC-BE-012〜TC-BE-013）。"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# TC-BE-012: ツール登録と取得（正常系）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_register_and_get_tool(tool_registry: ToolRegistry) -> None:
    """TC-BE-012: ToolRegistryにツールを登録し、名前で取得できる。"""
    # Given: tool_registry fixture（空のレジストリ）
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"

    # When
    tool_registry.register(mock_tool)
    retrieved = tool_registry.get_by_name("test_tool")

    # Then
    assert retrieved is mock_tool


# ---------------------------------------------------------------------------
# TC-BE-013: 未登録ツールのディスパッチ（異常系）
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_dispatch_unknown_tool(tool_registry: ToolRegistry) -> None:
    """TC-BE-013: 未登録のツールをdispatchするとValueErrorが raise される。"""
    # Given: unknown_tool は未登録

    # When / Then
    with pytest.raises(ValueError, match="ツール 'unknown_tool' が登録されていません"):
        await tool_registry.dispatch("unknown_tool", {})
