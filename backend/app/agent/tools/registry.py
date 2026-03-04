"""ToolRegistry: Redmine MCPツールの登録・管理・ディスパッチ。"""
from __future__ import annotations

from typing import Any, Optional


class ToolRegistry:
    """Redmine MCPツールの登録・管理・ディスパッチを行うレジストリ。"""

    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}

    def register(self, tool: Any) -> None:
        """ツールを登録する。tool.name をキーとして格納する。"""
        self._tools[tool.name] = tool

    def get_all(self) -> list[Any]:
        """登録済み全ツールのリストを返す。"""
        return list(self._tools.values())

    def get_by_name(self, name: str) -> Optional[Any]:
        """名前でツールを取得する。未登録の場合は None を返す。"""
        return self._tools.get(name)

    async def dispatch(self, tool_name: str, tool_input: dict) -> dict:
        """ツールを実行する。未登録の場合は ValueError を raise する。"""
        tool = self.get_by_name(tool_name)
        if tool is None:
            raise ValueError(f"ツール '{tool_name}' が登録されていません")
        result = await tool.arun(tool_input)
        return result
