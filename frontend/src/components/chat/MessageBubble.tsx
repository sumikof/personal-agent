"use client";

/**
 * MessageBubble コンポーネント。
 *
 * 単一メッセージのバブル表示。ユーザー/エージェントで外観（左右配置・色）を切り替える。
 */
import { type FC } from "react";
import type { Message } from "@/types/chat";

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
}

const MessageBubble: FC<MessageBubbleProps> = ({
  message,
  isStreaming = false,
}) => {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  return (
    <div
      role="listitem"
      aria-label={isUser ? "あなたのメッセージ" : "エージェントのメッセージ"}
      className={`flex mb-4 ${isUser ? "justify-end" : "justify-start"}`}
    >
      {/* エージェントアイコン */}
      {isAssistant && (
        <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-xs font-bold mr-2 flex-shrink-0">
          AI
        </div>
      )}

      {/* メッセージバブル */}
      <div
        className={`max-w-2xl rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-blue-500 text-white rounded-tr-none"
            : "bg-gray-100 text-gray-900 rounded-tl-none"
        }`}
      >
        {/* メッセージ内容 */}
        <p className={`text-sm whitespace-pre-wrap ${isUser ? "text-white" : "text-gray-900"}`}>
          {message.content}
        </p>

        {/* ストリーミング中カーソル */}
        {isStreaming && isAssistant && (
          <span className="animate-pulse inline-block w-2 h-4 bg-gray-500 ml-1 align-middle" />
        )}

        {/* タイムスタンプ */}
        <time
          dateTime={message.createdAt}
          className={`block text-xs mt-1 ${
            isUser ? "text-blue-100" : "text-gray-400"
          }`}
        >
          {new Date(message.createdAt).toLocaleTimeString("ja-JP", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </time>
      </div>

      {/* ユーザーアイコン */}
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-400 flex items-center justify-center text-white text-xs font-bold ml-2 flex-shrink-0">
          You
        </div>
      )}
    </div>
  );
};

export default MessageBubble;
