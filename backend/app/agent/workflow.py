"""AgentWorkflow: LangGraph エージェントワークフローの定義・実行。"""
from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from typing import Any, Optional

from app.agent.state import AgentState, SSEEvent
from app.agent.tools.registry import ToolRegistry
from app.integration.claude import ClaudeAPIClient

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "あなたはRedmineタスク管理を支援するAIアシスタントです。"
    "タスクの作成・更新・検索を行うツールを使用できます。"
    "タスクの削除は行いません。"
)


class AgentWorkflow:
    """LangGraph StateGraph ベースのエージェントワークフロー。"""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        claude_client: ClaudeAPIClient,
    ) -> None:
        self.tool_registry = tool_registry
        self.claude_client = claude_client
        self._graph = self._build_graph()

    def _build_graph(self) -> Any:
        """LangGraph StateGraph を構築してコンパイルする。"""
        try:
            from langgraph.graph import StateGraph, END  # noqa: PLC0415
            graph = StateGraph(AgentState)
            graph.add_node("llm_node", self._llm_node)
            graph.add_node("tool_executor_node", self._tool_executor_node)
            graph.add_edge("__start__", "llm_node")
            graph.add_conditional_edges(
                "llm_node",
                self.tool_router_node,
                {"tool_executor_node": "tool_executor_node", "__end__": END},
            )
            graph.add_edge("tool_executor_node", "llm_node")
            return graph.compile()
        except ImportError:
            logger.warning("langgraph がインストールされていません。ダミーグラフを使用します。")
            return None

    def tool_router_node(self, state: AgentState) -> str:
        """tool_calls の有無でルーティングを決定する条件分岐ノード。"""
        if state.get("tool_calls"):
            return "tool_executor_node"
        return "__end__"

    async def _llm_node(self, state: AgentState) -> AgentState:
        """Claude API にメッセージを送信し、推論結果を取得する。"""
        try:
            from langchain_core.messages import AIMessage, HumanMessage  # noqa: PLC0415
        except ImportError:
            AIMessage = dict  # type: ignore[misc,assignment]
            HumanMessage = dict  # type: ignore[misc,assignment]

        # ツール定義を取得
        tools = [t.to_anthropic_schema() for t in self.tool_registry.get_all()
                 if hasattr(t, "to_anthropic_schema")]

        # メッセージをAnthropicフォーマットに変換
        messages = _convert_messages_to_anthropic(state["messages"])

        text_content = ""
        tool_calls: list[dict] = []
        streaming_events: list[SSEEvent] = []

        try:
            async for event in self.claude_client.create_message_stream(
                messages=messages,
                tools=tools if tools else None,
                system=SYSTEM_PROMPT,
            ):
                event_type = getattr(event, "type", None) or event.get("type", "")
                if event_type == "content_block_delta":
                    delta = getattr(event, "delta", None) or event.get("delta", {})
                    delta_type = getattr(delta, "type", None) or delta.get("type", "")
                    if delta_type == "text_delta":
                        text = getattr(delta, "text", None) or delta.get("text", "")
                        text_content += text
                        streaming_events.append({"type": "chunk", "content": text})
                elif event_type == "content_block_start":
                    block = getattr(event, "content_block", None) or event.get("content_block", {})
                    block_type = getattr(block, "type", None) or block.get("type", "")
                    if block_type == "tool_use":
                        tool_name = getattr(block, "name", None) or block.get("name", "")
                        tool_id = getattr(block, "id", None) or block.get("id", "")
                        tool_calls.append({"id": tool_id, "name": tool_name, "input": {}})
                        streaming_events.append({"type": "tool_call", "tool": tool_name})
                elif event_type == "content_block_delta":
                    delta = getattr(event, "delta", None) or event.get("delta", {})
                    delta_type = getattr(delta, "type", None) or delta.get("type", "")
                    if delta_type == "input_json_delta":
                        # tool input の組み立ては完了後に行う（今回は簡略）
                        pass
        except Exception as e:
            logger.error("claude_api_error: %s", str(e))
            streaming_events.append({"type": "error", "error": f"AIとの通信に失敗しました: {e}"})
            return {
                **state,
                "tool_calls": None,
                "streaming_events": streaming_events,
            }  # type: ignore[return-value]

        return {
            **state,
            "tool_calls": tool_calls if tool_calls else None,
            "streaming_events": streaming_events,
        }  # type: ignore[return-value]

    async def _tool_executor_node(self, state: AgentState) -> AgentState:
        """tool_calls に含まれる各ツールを順次実行する。"""
        tool_calls = state.get("tool_calls") or []
        streaming_events: list[SSEEvent] = []
        intermediate_steps = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("name", "")
            tool_input = tool_call.get("input", {})
            try:
                result = await self.tool_registry.dispatch(tool_name, tool_input)
                streaming_events.append({
                    "type": "tool_result",
                    "tool": tool_name,
                    "result": result,
                })
                intermediate_steps.append({
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "tool_output": result,
                })
            except Exception as e:
                logger.error("tool_execution_error tool=%s error=%s", tool_name, str(e))
                streaming_events.append({
                    "type": "tool_result",
                    "tool": tool_name,
                    "result": {"error": str(e)},
                })

        return {
            **state,
            "tool_calls": None,
            "intermediate_steps": intermediate_steps,
            "streaming_events": streaming_events,
        }  # type: ignore[return-value]

    async def run_stream(
        self,
        conversation_id: str,
        messages: list[Any],
    ) -> AsyncIterator[SSEEvent]:
        """エージェントワークフローを実行してSSEイベントを yield する。"""
        initial_state: AgentState = {
            "messages": messages,
            "tool_calls": None,
            "intermediate_steps": [],
            "conversation_id": conversation_id,
            "streaming_events": [],
        }

        if self._graph is None:
            # LangGraph が使えない場合はフォールバック
            yield {"type": "error", "error": "エージェントワークフローが初期化されていません"}
            return

        try:
            async for chunk in self._graph.astream(initial_state):
                for _node_name, node_output in chunk.items():
                    for event in node_output.get("streaming_events", []):
                        yield event
        except Exception as e:
            logger.error("agent_workflow_error: %s (conversation_id=%s)", str(e), conversation_id)
            yield {"type": "error", "error": f"エージェント実行エラー: {e}"}


def _convert_messages_to_anthropic(messages: list[Any]) -> list[dict]:
    """LangChain BaseMessage を Anthropic API 形式に変換する。"""
    result = []
    for msg in messages:
        # LangChain BaseMessage の場合
        msg_type = type(msg).__name__
        if hasattr(msg, "type"):
            msg_type = msg.type
        content = getattr(msg, "content", str(msg))
        if msg_type in ("human", "HumanMessage"):
            result.append({"role": "user", "content": content})
        elif msg_type in ("ai", "AIMessage"):
            result.append({"role": "assistant", "content": content})
        elif isinstance(msg, dict):
            result.append(msg)
    return result
