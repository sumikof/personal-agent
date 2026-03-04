/**
 * チャット機能の型定義。
 */

export interface Message {
  id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  createdAt: string; // ISO 8601
  toolCalls?: ToolCall[];
}

export interface ToolCall {
  id: string;
  name: string;
  input: Record<string, unknown>;
  output?: string;
}

export type AgentStatus = "thinking" | "tool_calling" | "generating";

// SSE イベント型定義（バックエンドの SSE イベント仕様に対応）
export type SSEEvent =
  | {
      type: "message_start";
      message_id: string;
      conversation_id: string;
    }
  | {
      type: "content_delta";
      delta: string;
    }
  | {
      type: "tool_call";
      tool_call_id: string;
      tool: string;
      input: Record<string, unknown>;
    }
  | {
      type: "tool_result";
      tool_call_id: string;
      tool: string;
      output: string;
    }
  | {
      type: "message_end";
      total_tokens: number;
      input_tokens: number;
      output_tokens: number;
    }
  | {
      type: "error";
      code: string;
      message: string;
    };
