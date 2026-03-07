"use client";

/**
 * MessageInput コンポーネント。
 *
 * メッセージ入力フォーム。Enter: 送信 / Shift+Enter: 改行に対応。
 */
import {
  useState,
  useCallback,
  type FC,
  type KeyboardEvent,
  type ChangeEvent,
} from "react";

interface MessageInputProps {
  onSend: (content: string) => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

const DEFAULT_PLACEHOLDER =
  "メッセージを入力（Enter: 送信 / Shift+Enter: 改行）";
const MAX_MESSAGE_LENGTH = 4000;

const MessageInput: FC<MessageInputProps> = ({
  onSend,
  disabled = false,
  placeholder = DEFAULT_PLACEHOLDER,
  maxLength = MAX_MESSAGE_LENGTH,
}) => {
  const [content, setContent] = useState("");
  const [isSending, setIsSending] = useState(false);

  const handleSend = useCallback(async () => {
    const trimmedContent = content.trim();
    if (!trimmedContent || isSending || disabled) return;

    setIsSending(true);
    setContent("");

    try {
      await onSend(trimmedContent);
    } finally {
      setIsSending(false);
    }
  }, [content, isSending, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        void handleSend();
      }
    },
    [handleSend]
  );

  const handleChange = useCallback(
    (e: ChangeEvent<HTMLTextAreaElement>) => {
      const value = e.target.value;
      if (value.length <= maxLength) {
        setContent(value);
      }
    },
    [maxLength]
  );

  const isOverLimit = content.length > maxLength * 0.9;
  const canSend = content.trim().length > 0 && !disabled && !isSending;

  return (
    <div className="flex gap-2 items-end">
      <div className="flex-1 relative">
        <textarea
          value={content}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isSending}
          rows={2}
          className="w-full resize-none pr-16 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          aria-label="メッセージ入力欄"
          aria-describedby="message-char-count"
        />
        {/* 文字数カウント */}
        <div
          id="message-char-count"
          className={`absolute bottom-2 right-2 text-xs ${
            isOverLimit ? "text-orange-500" : "text-gray-400"
          }`}
          aria-live="polite"
        >
          {content.length}/{maxLength}
        </div>
      </div>

      {/* 送信ボタン */}
      <button
        onClick={() => void handleSend()}
        disabled={!canSend}
        aria-label="メッセージを送信"
        className="h-10 px-4 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
      >
        {isSending ? (
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : (
          <span className="text-sm font-medium">送信</span>
        )}
      </button>
    </div>
  );
};

export default MessageInput;
