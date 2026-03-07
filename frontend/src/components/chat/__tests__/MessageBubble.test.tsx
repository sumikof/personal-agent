/**
 * MessageBubble コンポーネントの単体テスト（TDD: TC-018〜TC-020）。
 */
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import MessageBubble from "../MessageBubble";
import type { Message } from "@/types/chat";

describe("MessageBubble", () => {
  it("ユーザーメッセージが右側に表示されること（TC-018）", () => {
    // Given
    const message: Message = {
      id: "1",
      role: "user",
      content: "タスクを作成してください",
      createdAt: "2026-03-03T10:00:00Z",
    };

    // When
    render(<MessageBubble message={message} />);

    // Then
    const listItem = screen.getByRole("listitem");
    expect(listItem).toHaveClass("justify-end");
    expect(screen.getByText("タスクを作成してください")).toBeInTheDocument();
  });

  it("エージェントメッセージが左側に表示されること（TC-019）", () => {
    // Given
    const message: Message = {
      id: "2",
      role: "assistant",
      content: "タスクを作成しました。",
      createdAt: "2026-03-03T10:00:01Z",
    };

    // When
    render(<MessageBubble message={message} />);

    // Then
    const listItem = screen.getByRole("listitem");
    expect(listItem).toHaveClass("justify-start");
    expect(screen.getByText("タスクを作成しました。")).toBeInTheDocument();
  });

  it("isStreaming=true のときカーソルアニメーションが表示されること（TC-020）", () => {
    // Given
    const message: Message = {
      id: "3",
      role: "assistant",
      content: "処理中",
      createdAt: "2026-03-03T10:00:01Z",
    };

    // When
    render(<MessageBubble message={message} isStreaming={true} />);

    // Then
    const cursor = document.querySelector(".animate-pulse");
    expect(cursor).toBeInTheDocument();
  });

  it("isStreaming=false のときカーソルアニメーションが表示されないこと（TC-020b）", () => {
    // Given
    const message: Message = {
      id: "4",
      role: "assistant",
      content: "完了しました",
      createdAt: "2026-03-03T10:00:02Z",
    };

    // When
    render(<MessageBubble message={message} isStreaming={false} />);

    // Then
    const cursor = document.querySelector(".animate-pulse");
    expect(cursor).not.toBeInTheDocument();
  });
});
