"""AgentState: LangGraphグラフの状態型定義。"""
from __future__ import annotations

import operator
from typing import Annotated, Any, Optional, TypedDict


class ToolCallRecord(TypedDict):
    """ツール呼び出し実行記録。"""

    tool_name: str
    tool_input: dict
    tool_output: dict


class SSEEvent(TypedDict, total=False):
    """SSEイベント型。

    type: "chunk" | "tool_call" | "tool_result" | "message_start" | "done" | "error"
    """

    type: str
    content: Optional[str]
    tool: Optional[str]
    tool_input: Optional[dict]
    result: Optional[dict]
    message_id: Optional[str]
    error: Optional[str]


class AgentState(TypedDict):
    """LangGraphグラフの状態型。"""

    messages: Annotated[list[Any], operator.add]
    tool_calls: Optional[list[dict]]
    intermediate_steps: Annotated[list[ToolCallRecord], operator.add]
    conversation_id: str
    streaming_events: Annotated[list[SSEEvent], operator.add]
