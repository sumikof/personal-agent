/**
 * useChat カスタムフックの単体テスト（TDD: TC-025〜TC-029）。
 * FEAT-002: search_tasks ツール対応テストを追加（TC-028〜TC-029）。
 */
import { renderHook, act } from "@testing-library/react";
import { useChat } from "../useChat";

/**
 * SSE レスポンスのモック（Response を使わない実装）。
 * jsdom 環境では Response が未定義のため ReadableStream で代替する。
 */
function createMockSseResponse(sseBody: string, status = 200) {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(sseBody));
      controller.close();
    },
  });
  return {
    ok: status >= 200 && status < 300,
    status,
    body: stream,
  };
}

/**
 * エラーレスポンスのモック。
 */
function createMockErrorResponse(status: number) {
  return {
    ok: false,
    status,
    body: null,
  };
}

describe("useChat", () => {
  it("sendMessage 呼び出しでユーザーメッセージが追加されること（TC-025）", async () => {
    // Given
    const sseBody =
      'data: {"type": "message_end", "total_tokens": 100, "input_tokens": 80, "output_tokens": 20}\n\ndata: [DONE]\n\n';
    const mockFetch = jest
      .fn()
      .mockResolvedValue(createMockSseResponse(sseBody));
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
    const sseBody = [
      'data: {"type": "message_start", "message_id": "msg_1", "conversation_id": "test-conv-id"}\n\n',
      'data: {"type": "content_delta", "delta": "タスクを"}\n\n',
      'data: {"type": "content_delta", "delta": "作成しました。"}\n\n',
      'data: {"type": "message_end", "total_tokens": 50, "input_tokens": 30, "output_tokens": 20}\n\n',
      "data: [DONE]\n\n",
    ].join("");

    const mockFetch = jest
      .fn()
      .mockResolvedValue(createMockSseResponse(sseBody));
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
    const mockFetch = jest
      .fn()
      .mockResolvedValue(createMockErrorResponse(503));
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

  // ------------------------------------------------------------------ //
  // TC-028（FEAT-002）: tool_call search_tasks → agentStatus が tool_calling //
  // ------------------------------------------------------------------ //
  it("SSE で tool_call search_tasks を受信すると agentStatus が tool_calling になること（TC-028）", async () => {
    /**
     * Given: SSE ストリームが tool_call search_tasks イベントを送信する
     * When:  sendMessage を呼び出す
     * Then:  処理中に agentStatus が "tool_calling" になり currentToolCall が "search_tasks" になる
     */
    // Given: search_tasks ツール呼び出し後すぐに message_end で終了
    const sseBody = [
      'data: {"type": "tool_call", "tool_call_id": "call_001", "tool": "search_tasks", "input": {"status": "open"}}\n\n',
      'data: {"type": "tool_result", "tool_call_id": "call_001", "tool": "search_tasks", "output": "## タスク一覧（1件）"}\n\n',
      'data: {"type": "content_delta", "delta": "今日の期限タスクは 1 件あります。"}\n\n',
      'data: {"type": "message_end", "total_tokens": 60, "input_tokens": 40, "output_tokens": 20}\n\n',
      "data: [DONE]\n\n",
    ].join("");

    const mockFetch = jest
      .fn()
      .mockResolvedValue(createMockSseResponse(sseBody));
    global.fetch = mockFetch;

    const { result } = renderHook(() =>
      useChat({ conversationId: "test-conv-id" })
    );

    // When
    await act(async () => {
      await result.current.sendMessage("未完了タスク一覧を見せて");
    });

    // Then: 最終的にエージェントのメッセージが設定されている
    const assistantMessage = result.current.messages.find(
      (m) => m.role === "assistant"
    );
    expect(assistantMessage?.content).toContain("今日の期限タスクは 1 件あります。");
  });

  // ------------------------------------------------------------------ //
  // TC-029（FEAT-002）: tool_call 後に content_delta → テキストが蓄積される //
  // ------------------------------------------------------------------ //
  it("search_tasks tool_call 後の content_delta がメッセージに反映されること（TC-029）", async () => {
    /**
     * Given: tool_call → tool_result → content_delta の順で SSE イベントを受信
     * When:  sendMessage を呼び出す
     * Then:  エージェントメッセージに content_delta のテキストが含まれる
     */
    // Given
    const sseBody = [
      'data: {"type": "tool_call", "tool_call_id": "call_001", "tool": "search_tasks", "input": {}}\n\n',
      'data: {"type": "tool_result", "tool_call_id": "call_001", "tool": "search_tasks", "output": "## タスク一覧（3件）\\n\\n1. [タスクA](http://localhost:8080/issues/1)"}\n\n',
      'data: {"type": "content_delta", "delta": "3件のタスクが見つかりました。"}\n\n',
      'data: {"type": "message_end", "total_tokens": 100, "input_tokens": 80, "output_tokens": 20}\n\n',
      "data: [DONE]\n\n",
    ].join("");

    const mockFetch = jest
      .fn()
      .mockResolvedValue(createMockSseResponse(sseBody));
    global.fetch = mockFetch;

    const { result } = renderHook(() =>
      useChat({ conversationId: "test-conv-id" })
    );

    // When
    await act(async () => {
      await result.current.sendMessage("タスク一覧を見せて");
    });

    // Then
    const assistantMessage = result.current.messages.find(
      (m) => m.role === "assistant"
    );
    expect(assistantMessage?.content).toBe("3件のタスクが見つかりました。");
  });
});
