/**
 * MarkdownContent コンポーネントの単体テスト（FEAT-002: TC-032〜TC-037）。
 */
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import { MarkdownContent } from "../MarkdownContent";

describe("MarkdownContent", () => {
  // ------------------------------------------------------------------ //
  // TC-032: Redmine URL → target="_blank" で新しいタブで開く              //
  // ------------------------------------------------------------------ //
  it("renders Redmine issue URL as external link with target blank (TC-032)", () => {
    /**
     * Given: Redmine チケット URL を含む Markdown テキスト
     * When:  MarkdownContent をレンダリングする
     * Then:  <a target="_blank" rel="noopener noreferrer"> としてレンダリングされる
     */
    // Given
    const content = "[設計書レビュー](http://localhost:8080/issues/123)";

    // When
    render(<MarkdownContent content={content} />);

    // Then
    const link = screen.getByRole("link", { name: /設計書レビュー/ });
    expect(link).toHaveAttribute("href", "http://localhost:8080/issues/123");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  // ------------------------------------------------------------------ //
  // TC-033: **高** → <strong> タグで太字表示される                         //
  // ------------------------------------------------------------------ //
  it("renders bold text for high priority tasks (TC-033)", () => {
    /**
     * Given: **高** を含む Markdown テキスト
     * When:  MarkdownContent をレンダリングする
     * Then:  <strong> タグでレンダリングされる
     */
    // Given
    const content = "1. [タスク](http://localhost:8080/issues/1) - **高**";

    // When
    render(<MarkdownContent content={content} />);

    // Then
    const boldText = screen.getByText("高");
    expect(boldText.tagName).toBe("STRONG");
  });

  // ------------------------------------------------------------------ //
  // TC-034: ## ヘッダ → h2 タグでレンダリングされる                         //
  // ------------------------------------------------------------------ //
  it("renders h2 heading for task list header (TC-034)", () => {
    /**
     * Given: ## タスク一覧（3件）を含む Markdown テキスト
     * When:  MarkdownContent をレンダリングする
     * Then:  <h2> タグでレンダリングされる
     */
    // Given
    const content = "## タスク一覧（3件）";

    // When
    render(<MarkdownContent content={content} />);

    // Then
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toHaveTextContent("タスク一覧（3件）");
  });

  // ------------------------------------------------------------------ //
  // TC-035: isStreaming=true → カーソル要素が表示される                     //
  // ------------------------------------------------------------------ //
  it("shows streaming cursor when isStreaming is true (TC-035)", () => {
    /**
     * Given: isStreaming=true
     * When:  MarkdownContent をレンダリングする
     * Then:  animate-pulse のカーソル要素が表示される
     */
    // Given / When
    const { container } = render(
      <MarkdownContent content="テキスト" isStreaming={true} />
    );

    // Then
    const cursor = container.querySelector(".animate-pulse");
    expect(cursor).toBeInTheDocument();
  });

  // ------------------------------------------------------------------ //
  // TC-036: isStreaming=false → カーソル要素が表示されない                  //
  // ------------------------------------------------------------------ //
  it("does not show streaming cursor when isStreaming is false (TC-036)", () => {
    /**
     * Given: isStreaming=false（デフォルト）
     * When:  MarkdownContent をレンダリングする
     * Then:  animate-pulse のカーソル要素は表示されない
     */
    // Given / When
    const { container } = render(<MarkdownContent content="テキスト" />);

    // Then
    const cursor = container.querySelector(".animate-pulse");
    expect(cursor).not.toBeInTheDocument();
  });

  // ------------------------------------------------------------------ //
  // TC-037: 複数リンク → すべてのリンクが target="_blank" で表示される        //
  // ------------------------------------------------------------------ //
  it("renders multiple issue links all with target blank (TC-037)", () => {
    /**
     * Given: 3 件のタスク URL を含む Markdown テキスト
     * When:  MarkdownContent をレンダリングする
     * Then:  すべてのリンクが target="_blank" でレンダリングされる
     */
    // Given
    const content = `## タスク一覧（3件）

1. [タスクA](http://localhost:8080/issues/1) - **高**
2. [タスクB](http://localhost:8080/issues/2) - 通常
3. [タスクC](http://localhost:8080/issues/3) - 低`;

    // When
    render(<MarkdownContent content={content} />);

    // Then
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(3);
    links.forEach((link) => {
      expect(link).toHaveAttribute("target", "_blank");
    });
  });
});
