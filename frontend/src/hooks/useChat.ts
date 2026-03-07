/**
 * useChat カスタムフック。
 *
 * チャット画面の状態管理（メッセージ一覧・ローディング状態・SSE ストリーミング処理）を担う。
 */
import {
  useState,
  useCallback,
  useRef,
  type Dispatch,
  type SetStateAction,
} from "react";
import type { AgentStatus, Message, SSEEvent } from "@/types/chat";

interface UseChatOptions {
  conversationId: string;
  onError?: (error: Error) => void;
}

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  agentStatus: AgentStatus;
  currentToolCall: string | undefined;
  sendMessage: (content: string) => Promise<void>;
}

export function useChat({
  conversationId,
  onError,
}: UseChatOptions): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [agentStatus, setAgentStatus] = useState<AgentStatus>("thinking");
  const [currentToolCall, setCurrentToolCall] = useState<string | undefined>();
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (content: string): Promise<void> => {
      if (!content.trim()) return;

      // 前の SSE 接続をキャンセル
      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      // ユーザーメッセージを追加
      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content,
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);
      setAgentStatus("thinking");
      setCurrentToolCall(undefined);

      // エージェントメッセージのプレースホルダー
      const assistantMessageId = crypto.randomUUID();
      const assistantMessage: Message = {
        id: assistantMessageId,
        role: "assistant",
        content: "",
        createdAt: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      try {
        const response = await fetch(
          `/api/v1/conversations/${conversationId}/messages`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Accept: "text/event-stream",
            },
            body: JSON.stringify({ content }),
            signal: controller.signal,
          }
        );

        if (!response.ok) {
          throw new Error(
            `HTTP ${response.status}: メッセージ送信に失敗しました`
          );
        }

        // SSE ストリーム処理
        await processSSEStream(response, {
          assistantMessageId,
          setMessages,
          setAgentStatus,
          setCurrentToolCall,
        });
      } catch (error) {
        if (error instanceof Error && error.name !== "AbortError") {
          // エージェントメッセージにエラー内容を表示
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content:
                      "申し訳ありません。エラーが発生しました。再試行してください。",
                  }
                : msg
            )
          );
          onError?.(error instanceof Error ? error : new Error(String(error)));
        }
      } finally {
        setIsLoading(false);
        setAgentStatus("thinking");
        setCurrentToolCall(undefined);
      }
    },
    [conversationId, onError]
  );

  return { messages, isLoading, agentStatus, currentToolCall, sendMessage };
}

/**
 * SSE ストリーム処理の内部関数。
 *
 * バックエンドからの SSE イベントを受信し、メッセージ・エージェント状態を更新する。
 */
async function processSSEStream(
  response: Response,
  context: {
    assistantMessageId: string;
    setMessages: Dispatch<SetStateAction<Message[]>>;
    setAgentStatus: Dispatch<SetStateAction<AgentStatus>>;
    setCurrentToolCall: Dispatch<SetStateAction<string | undefined>>;
  }
): Promise<void> {
  const { assistantMessageId, setMessages, setAgentStatus, setCurrentToolCall } =
    context;

  const reader = response.body?.getReader();
  if (!reader) throw new Error("Response body is not readable");

  const decoder = new TextDecoder();
  let assistantContent = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split("\n");

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;

        const rawData = line.slice(6);
        if (rawData === "[DONE]") break;

        let event: SSEEvent;
        try {
          event = JSON.parse(rawData) as SSEEvent;
        } catch {
          continue;
        }

        switch (event.type) {
          case "content_delta":
            assistantContent += event.delta ?? "";
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: assistantContent }
                  : msg
              )
            );
            setAgentStatus("generating");
            break;

          case "tool_call":
            setAgentStatus("tool_calling");
            setCurrentToolCall(event.tool ?? undefined);
            break;

          case "tool_result":
            setAgentStatus("thinking");
            setCurrentToolCall(undefined);
            break;

          case "message_end":
            break;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
