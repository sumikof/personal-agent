/**
 * MessageInput コンポーネントの単体テスト（TDD: TC-021〜TC-024）。
 */
import "@testing-library/jest-dom";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MessageInput from "../MessageInput";

describe("MessageInput", () => {
  it("Enter キーでメッセージが送信されること（TC-021）", async () => {
    // Given
    const mockOnSend = jest.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<MessageInput onSend={mockOnSend} />);
    const textarea = screen.getByRole("textbox", { name: "メッセージ入力欄" });

    // When
    await user.type(textarea, "タスクを作成して");
    await user.keyboard("{Enter}");

    // Then
    expect(mockOnSend).toHaveBeenCalledWith("タスクを作成して");
  });

  it("Shift+Enter では送信されず改行されること（TC-022）", async () => {
    // Given
    const mockOnSend = jest.fn();
    const user = userEvent.setup();

    render(<MessageInput onSend={mockOnSend} />);
    const textarea = screen.getByRole("textbox", { name: "メッセージ入力欄" });

    // When
    await user.type(textarea, "1行目");
    await user.keyboard("{Shift>}{Enter}{/Shift}");
    await user.type(textarea, "2行目");

    // Then
    expect(mockOnSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("1行目\n2行目");
  });

  it("disabled=true のとき送信ボタンが無効化されること（TC-023）", () => {
    // Given / When
    render(<MessageInput onSend={jest.fn()} disabled={true} />);

    // Then
    const sendButton = screen.getByRole("button", { name: "メッセージを送信" });
    expect(sendButton).toBeDisabled();
  });

  it("空白のみのメッセージは送信されないこと（TC-024）", async () => {
    // Given
    const mockOnSend = jest.fn();
    const user = userEvent.setup();

    render(<MessageInput onSend={mockOnSend} />);
    const textarea = screen.getByRole("textbox", { name: "メッセージ入力欄" });

    // When
    await user.type(textarea, "   ");
    await user.keyboard("{Enter}");

    // Then
    expect(mockOnSend).not.toHaveBeenCalled();
  });
});
