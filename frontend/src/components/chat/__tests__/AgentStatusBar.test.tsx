/**
 * AgentStatusBar コンポーネントの単体テスト（FEAT-002: TC-038〜TC-041）。
 */
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { AgentStatusBar } from "../AgentStatusBar";

describe("AgentStatusBar - FEAT-002", () => {
  // ------------------------------------------------------------------ //
  // TC-038: tool_calling + search_tasks → 「タスク検索」バッジが表示される   //
  // ------------------------------------------------------------------ //
  it("shows task search badge when search_tasks tool is called (TC-038)", () => {
    /**
     * Given: status="tool_calling", currentToolCall="search_tasks"
     * When:  AgentStatusBar をレンダリングする
     * Then:  「タスク検索」バッジと「Redmine からタスクを検索しています」が表示される
     */
    // Given / When
    render(
      <AgentStatusBar status="tool_calling" currentToolCall="search_tasks" />
    );

    // Then
    expect(screen.getByText("タスク検索")).toBeInTheDocument();
    expect(
      screen.getByText(/Redmine からタスクを検索しています/)
    ).toBeInTheDocument();
  });

  // ------------------------------------------------------------------ //
  // TC-039: tool_calling + create_task → 「タスク作成」バッジが表示される    //
  // ------------------------------------------------------------------ //
  it("shows task create badge when create_task tool is called (TC-039)", () => {
    /**
     * Given: status="tool_calling", currentToolCall="create_task"
     * When:  AgentStatusBar をレンダリングする
     * Then:  「タスク作成」バッジと「Redmine にタスクを作成しています」が表示される
     */
    // Given / When
    render(
      <AgentStatusBar status="tool_calling" currentToolCall="create_task" />
    );

    // Then
    expect(screen.getByText("タスク作成")).toBeInTheDocument();
    expect(
      screen.getByText(/Redmine にタスクを作成しています/)
    ).toBeInTheDocument();
  });

  // ------------------------------------------------------------------ //
  // TC-040: status="thinking" → 「考えています...」が表示される              //
  // ------------------------------------------------------------------ //
  it("shows thinking message when status is thinking (TC-040)", () => {
    /**
     * Given: status="thinking"
     * When:  AgentStatusBar をレンダリングする
     * Then:  「考えています...」が表示される
     */
    // Given / When
    render(<AgentStatusBar status="thinking" />);

    // Then
    expect(screen.getByText("考えています...")).toBeInTheDocument();
  });

  // ------------------------------------------------------------------ //
  // TC-041: status="generating" → 「回答を生成しています...」が表示される    //
  // ------------------------------------------------------------------ //
  it("shows generating message when status is generating (TC-041)", () => {
    /**
     * Given: status="generating"
     * When:  AgentStatusBar をレンダリングする
     * Then:  「回答を生成しています...」が表示される
     */
    // Given / When
    render(<AgentStatusBar status="generating" />);

    // Then
    expect(screen.getByText("回答を生成しています...")).toBeInTheDocument();
  });
});
