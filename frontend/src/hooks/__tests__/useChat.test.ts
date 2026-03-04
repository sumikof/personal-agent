/**
 * useChat カスタムフックの単体テスト（TDD: TC-025〜TC-027）。
 */
import { renderHook, act } from "@testing-library/react";
import { useChat } from "../useChat";

describe("useChat", () => {
  it("sendMessage 呼び出しでユーザーメッセージが追加されること（TC-025）", async () => {
    // Given
    const mockFetch = jest.fn().mockResolvedValue(
      new Response(
        'data: {"type": "message_end", "total_tokens": 100, "input_tokens": 80, "output_tokens": 20}\ndata: [DONE]\n',
        {
          status: 200,
          headers: { "Content-Type": "text/event-stream" },
        }
      )
    );
    global.fetch = mockFetch;

    const { result } = renderHook(() =>
      useChat({ conversationId: "test-conv-id" })
    );

    // When
    await act(async () => {
      await result.current.sendMessage("タスクを作成して");
    });

    // Then
    expect(result.current.messages).toHaveLength(2); // ユーザー + エージェント
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("タスクを作成して");
  });

  it("SSE content_delta イベントでエージェントメッセージが逐次更新されること（TC-026）", async () => {
    // Given
    const sseStream = [
      'data: {"type": "message_start", "message_id": "msg_1", "conversation_id": "test-conv-id"}\n\n',
      'data: {"type": "content_delta", "delta": "タスクを"}\n\n',
      'data: {"type": "content_delta", "delta": "作成しました。"}\n\n',
      'data: {"type": "message_end", "total_tokens": 50, "input_tokens": 30, "output_tokens": 20}\n\n',
      "data: [DONE]\n\n",
    ].join("");

    const mockFetch = jest.fn().mockResolvedValue(
      new Response(sseStream, {
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
      })
    );
    global.fetch = mockFetch;

    const { result } = renderHook(() =>
      useChat({ conversationId: "test-conv-id" })
    );

    // When
    await act(async () => {
      await result.current.sendMessage("タスクを作成して");
    });

    // Then
    const assistantMessage = result.current.messages.find(
      (m) => m.role === "assistant"
    );
    expect(assistantMessage?.content).toBe("タスクを作成しました。");
  });

  it("API エラー時に onError コールバックが呼ばれること（TC-027）", async () => {
    // Given
    const mockFetch = jest.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: { code: "SERVICE_UNAVAILABLE" } }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      })
    );
    global.fetch = mockFetch;

    const mockOnError = jest.fn();
    const { result } = renderHook(() =>
      useChat({ conversationId: "test-conv-id", onError: mockOnError })
    );

    // When
    await act(async () => {
      await result.current.sendMessage("タスクを作成して");
    });

    // Then
    expect(mockOnError).toHaveBeenCalled();
  });
});
