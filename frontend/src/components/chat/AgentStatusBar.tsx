"use client";

/**
 * AgentStatusBar コンポーネント（FEAT-002）
 *
 * エージェントの処理状態（thinking / tool_calling / generating）を表示するステータスバー。
 * FEAT-002 で search_tasks ツールのバッジ表示を追加。
 */
import React from "react";
import type { AgentStatus } from "@/types/chat";

interface AgentStatusBarProps {
  status: AgentStatus;
  currentToolCall?: string;
}

const TOOL_CALL_MESSAGES: Record<string, string> = {
  create_task: "Redmine にタスクを作成しています...",
  search_tasks: "Redmine からタスクを検索しています...", // FEAT-002
};

const STATUS_MESSAGES: Record<AgentStatus, string> = {
  thinking: "考えています...",
  tool_calling: "",
  generating: "回答を生成しています...",
};

const TOOL_BADGE_LABELS: Record<string, string> = {
  create_task: "タスク作成",
  search_tasks: "タスク検索", // FEAT-002
};

interface ToolCallBadgeProps {
  toolName: string;
}

const ToolCallBadge: React.FC<ToolCallBadgeProps> = ({ toolName }) => {
  const label = TOOL_BADGE_LABELS[toolName] ?? toolName;
  return (
    <span className="px-2 py-0.5 bg-yellow-200 text-yellow-900 rounded-full text-xs font-medium">
      {label}
    </span>
  );
};

export const AgentStatusBar: React.FC<AgentStatusBarProps> = ({
  status,
  currentToolCall,
}) => {
  const message =
    status === "tool_calling" && currentToolCall
      ? (TOOL_CALL_MESSAGES[currentToolCall] ?? "処理しています...")
      : STATUS_MESSAGES[status];

  return (
    <div
      className="flex items-center gap-2 px-4 py-2 bg-yellow-50 border-t border-yellow-100 text-sm text-yellow-800"
      role="status"
      aria-live="polite"
      aria-label={`エージェント状態: ${message}`}
    >
      {/* スピナー */}
      <span
        className="inline-block w-4 h-4 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"
        aria-hidden="true"
      />
      {/* ツール名バッジ */}
      {status === "tool_calling" && currentToolCall && (
        <ToolCallBadge toolName={currentToolCall} />
      )}
      {/* メッセージ */}
      <span>{message}</span>
    </div>
  );
};
