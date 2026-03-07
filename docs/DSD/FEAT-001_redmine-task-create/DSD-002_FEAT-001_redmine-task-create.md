# DSD-002_FEAT-001 フロントエンド詳細設計書（Redmineタスク作成）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-002_FEAT-001 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-001 |
| 機能名 | Redmineタスク作成（redmine-task-create） |
| 入力元 | BSD-003, BSD-004 |
| ステータス | 初版 |

---

## 目次

1. 機能概要
2. コンポーネント構成
3. コンポーネント詳細設計
4. 状態管理設計
5. SSE ストリーミング実装
6. ルーティング設計
7. エラー表示設計
8. アクセシビリティ設計
9. 後続フェーズへの影響

---

## 1. 機能概要

### 1.1 概要

FEAT-001（Redmine タスク作成）のフロントエンド実装は、チャット画面（SCR-003）を通じて行う。専用のタスク作成フォーム画面（SCR-006）もあるが、チャット経由のエージェント対話が主要な操作経路。

### 1.2 対象画面

| 画面 ID | 画面名 | URL | 関与方法 |
|---|---|---|---|
| SCR-003 | チャット画面 | `/chat` | 主要操作画面。エージェントへの自然言語指示・SSE 応答表示 |
| SCR-006 | タスク作成画面 | `/tasks/new` | フォームでの直接タスク作成（POST /api/v1/tasks を呼び出す） |

### 1.3 主な UI フロー

```
1. ユーザーがチャット画面（/chat）にアクセス
2. テキスト入力欄に「〇〇タスクを作成して」と入力
3. Enter キーまたは送信ボタンでメッセージ送信
4. ローディングインジケータ表示
5. SSE ストリーミングでエージェント応答をリアルタイム表示
6. 作成完了メッセージ（チケット URL 含む）の表示
7. URL をクリックすると Redmine チケット詳細ページへ遷移
```

---

## 2. コンポーネント構成

### 2.1 コンポーネント階層図

```
src/app/chat/page.tsx（チャットページ）
└── ChatLayout（チャット画面レイアウト）
    ├── ChatWindow（チャットウィンドウ全体）
    │   ├── MessageList（メッセージ一覧）
    │   │   ├── MessageBubble（ユーザーメッセージ）
    │   │   │   └── MarkdownContent（テキスト表示）
    │   │   └── MessageBubble（エージェントメッセージ）
    │   │       ├── MarkdownContent（Markdown レンダリング）
    │   │       └── StreamingCursor（ストリーミング中カーソル）
    │   └── MessageInput（メッセージ入力エリア）
    │       ├── TextArea（テキスト入力フィールド）
    │       └── SendButton（送信ボタン）
    └── AgentStatusBar（エージェント実行状態表示）
        └── ToolCallBadge（ツール呼び出し中バッジ）
```

### 2.2 コンポーネント一覧

| コンポーネント名 | ファイルパス | 役割 | 主要 Props |
|---|---|---|---|
| `ChatWindow` | `src/components/chat/ChatWindow.tsx` | チャット画面の最上位コンポーネント。状態管理のエントリーポイント | `conversationId: string` |
| `MessageList` | `src/components/chat/MessageList.tsx` | メッセージ一覧表示。自動スクロール制御 | `messages: Message[]` |
| `MessageBubble` | `src/components/chat/MessageBubble.tsx` | 単一メッセージ表示。ユーザー/エージェントで外観を切り替え | `role`, `content`, `isStreaming` |
| `MarkdownContent` | `src/components/chat/MarkdownContent.tsx` | Markdown テキストのレンダリング。URL をクリック可能リンクに変換 | `content: string` |
| `StreamingCursor` | `src/components/chat/StreamingCursor.tsx` | ストリーミング中のカーソルアニメーション | なし |
| `MessageInput` | `src/components/chat/MessageInput.tsx` | メッセージ入力フォーム。Enter 送信・Shift+Enter 改行に対応 | `onSend`, `disabled` |
| `AgentStatusBar` | `src/components/chat/AgentStatusBar.tsx` | エージェント実行状態（thinking/tool_calling）の表示 | `status`, `toolName` |
| `ToolCallBadge` | `src/components/chat/ToolCallBadge.tsx` | ツール呼び出し中バッジ（例: 「Redmine にタスクを作成中...」） | `toolName: string` |

---

## 3. コンポーネント詳細設計

### 3.1 ChatWindow コンポーネント

```tsx
// src/components/chat/ChatWindow.tsx
"use client";

import { useEffect, useRef, type FC } from "react";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { AgentStatusBar } from "./AgentStatusBar";
import { useChat } from "@/hooks/useChat";
import { useToast } from "@/hooks/useToast";

interface ChatWindowProps {
  conversationId: string;
}

const ChatWindow: FC<ChatWindowProps> = ({ conversationId }) => {
  const { toast } = useToast();

  const {
    messages,
    isLoading,
    agentStatus,
    currentToolCall,
    sendMessage,
  } = useChat({
    conversationId,
    onError: (error) => {
      toast({
        variant: "destructive",
        title: "エラーが発生しました",
        description: error.message,
      });
    },
  });

  return (
    <div className="flex flex-col h-full bg-white">
      {/* エージェント状態バー */}
      {isLoading && (
        <AgentStatusBar
          status={agentStatus}
          toolName={currentToolCall}
        />
      )}

      {/* メッセージ一覧 */}
      <MessageList
        messages={messages}
        isLoading={isLoading}
        className="flex-1 overflow-y-auto"
      />

      {/* 入力エリア */}
      <div className="border-t border-gray-200 p-4">
        <MessageInput
          onSend={sendMessage}
          disabled={isLoading}
          placeholder="タスク作成の指示を入力（例：設計書レビューのタスクを作って、優先度高め）"
        />
      </div>
    </div>
  );
};

export default ChatWindow;
```

### 3.2 MessageBubble コンポーネント

```tsx
// src/components/chat/MessageBubble.tsx
"use client";

import { type FC } from "react";
import { MarkdownContent } from "./MarkdownContent";
import { StreamingCursor } from "./StreamingCursor";
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
        {/* メッセージ内容（Markdown レンダリング） */}
        <MarkdownContent
          content={message.content}
          className={isUser ? "text-white" : "text-gray-900"}
        />

        {/* ストリーミング中カーソル */}
        {isStreaming && isAssistant && <StreamingCursor />}

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
```

### 3.3 MessageList コンポーネント

```tsx
// src/components/chat/MessageList.tsx
"use client";

import { useEffect, useRef, type FC } from "react";
import { MessageBubble } from "./MessageBubble";
import type { Message } from "@/types/chat";

interface MessageListProps {
  messages: Message[];
  isLoading: boolean;
  className?: string;
}

const MessageList: FC<MessageListProps> = ({
  messages,
  isLoading,
  className = "",
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  // 新しいメッセージが追加されたら最下部にスクロール
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // 会話が空の場合のウェルカムメッセージ
  if (messages.length === 0) {
    return (
      <div
        role="list"
        aria-label="チャットメッセージ一覧"
        className={`flex items-center justify-center ${className}`}
      >
        <div className="text-center text-gray-400">
          <p className="text-lg mb-2">こんにちは！パーソナルエージェントです。</p>
          <p className="text-sm">タスク管理について何でもお気軽にどうぞ。</p>
          <div className="mt-4 space-y-2 text-xs text-gray-300">
            <p>例: 「設計書レビューのタスクを作成して」</p>
            <p>例: 「今日の未完了タスクを教えて」</p>
            <p>例: 「#123 のステータスを進行中に変更して」</p>
          </div>
        </div>
      </div>
    );
  }

  // 最後のメッセージがストリーミング中かどうかを判定
  const lastMessage = messages[messages.length - 1];
  const isLastMessageStreaming =
    isLoading && lastMessage?.role === "assistant";

  return (
    <div
      role="list"
      aria-label="チャットメッセージ一覧"
      aria-live="polite"
      className={`px-4 py-4 space-y-2 ${className}`}
    >
      {messages.map((message, index) => (
        <MessageBubble
          key={message.id}
          message={message}
          isStreaming={
            isLastMessageStreaming && index === messages.length - 1
          }
        />
      ))}

      {/* 自動スクロール用アンカー */}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;
```

### 3.4 MessageInput コンポーネント

```tsx
// src/components/chat/MessageInput.tsx
"use client";

import {
  useState,
  useCallback,
  type FC,
  type KeyboardEvent,
  type ChangeEvent,
} from "react";
import { Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface MessageInputProps {
  onSend: (content: string) => Promise<void>;
  disabled?: boolean;
  placeholder?: string;
  maxLength?: number;
}

const DEFAULT_PLACEHOLDER = "メッセージを入力（Enter: 送信 / Shift+Enter: 改行）";
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
        handleSend();
      }
    },
    [handleSend]
  );

  const handleChange = useCallback((e: ChangeEvent<HTMLTextAreaElement>) => {
    const value = e.target.value;
    if (value.length <= maxLength) {
      setContent(value);
    }
  }, [maxLength]);

  const isOverLimit = content.length > maxLength * 0.9;
  const canSend = content.trim().length > 0 && !disabled && !isSending;

  return (
    <div className="flex gap-2 items-end">
      <div className="flex-1 relative">
        <Textarea
          value={content}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isSending}
          rows={2}
          maxRows={8}
          className="resize-none pr-16"
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
      <Button
        onClick={handleSend}
        disabled={!canSend}
        aria-label="メッセージを送信"
        className="h-12 px-4"
      >
        {isSending ? (
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
        ) : (
          <Send className="w-4 h-4" />
        )}
      </Button>
    </div>
  );
};

export default MessageInput;
```

### 3.5 MarkdownContent コンポーネント

```tsx
// src/components/chat/MarkdownContent.tsx
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { FC } from "react";

interface MarkdownContentProps {
  content: string;
  className?: string;
}

/**
 * Markdown テキストを HTML にレンダリングするコンポーネント。
 * - タスク作成完了メッセージ内の URL を自動的にクリック可能リンクに変換する
 * - XSS 対策: react-markdown は自動的に HTML をエスケープする
 */
const MarkdownContent: FC<MarkdownContentProps> = ({
  content,
  className = "",
}) => {
  return (
    <div className={`prose prose-sm max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // リンクを新しいタブで開く（Redmine チケット URL 等）
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 underline"
            >
              {children}
            </a>
          ),
          // コードブロックのスタイリング
          code: ({ className, children }) => (
            <code
              className={`${className} bg-gray-100 rounded px-1 py-0.5 text-sm font-mono`}
            >
              {children}
            </code>
          ),
          // リスト項目のスタイリング（タスク一覧表示用）
          li: ({ children }) => (
            <li className="text-sm leading-relaxed">{children}</li>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownContent;
```

### 3.6 AgentStatusBar コンポーネント

```tsx
// src/components/chat/AgentStatusBar.tsx
import type { FC } from "react";
import { Loader2 } from "lucide-react";

type AgentStatus = "thinking" | "tool_calling" | "generating";

interface AgentStatusBarProps {
  status: AgentStatus;
  toolName?: string;
}

const STATUS_MESSAGES: Record<AgentStatus, string> = {
  thinking: "エージェントが考えています...",
  tool_calling: "Redmine を操作しています...",
  generating: "応答を生成しています...",
};

const TOOL_NAMES: Record<string, string> = {
  create_task: "タスクを作成しています",
  search_tasks: "タスクを検索しています",
  update_task: "タスクを更新しています",
  get_task: "タスク詳細を取得しています",
};

const AgentStatusBar: FC<AgentStatusBarProps> = ({ status, toolName }) => {
  const message =
    toolName && status === "tool_calling"
      ? `${TOOL_NAMES[toolName] ?? toolName}...`
      : STATUS_MESSAGES[status];

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={message}
      className="flex items-center gap-2 px-4 py-2 bg-blue-50 border-b border-blue-100"
    >
      <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
      <span className="text-sm text-blue-700">{message}</span>
    </div>
  );
};

export default AgentStatusBar;
```

---

## 4. 状態管理設計

### 4.1 useChat カスタムフック

```typescript
// src/hooks/useChat.ts
import {
  useState,
  useCallback,
  useRef,
  type Dispatch,
  type SetStateAction,
} from "react";
import type { Message, SSEEvent, AgentStatus } from "@/types/chat";

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
          throw new Error(`HTTP ${response.status}: メッセージ送信に失敗しました`);
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

// SSE ストリーム処理の内部関数
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
```

### 4.2 型定義

```typescript
// src/types/chat.ts
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

// SSE イベント型定義
export type SSEEvent =
  | { type: "message_start"; messageId: string }
  | { type: "content_delta"; delta: string }
  | { type: "tool_call"; tool: string; input: Record<string, unknown> }
  | { type: "tool_result"; tool: string; output: string }
  | { type: "message_end"; totalTokens: number }
  | { type: "error"; message: string };
```

---

## 5. SSE ストリーミング実装

### 5.1 SSE イベント仕様

| イベント type | タイミング | フロントエンドの処理 |
|---|---|---|
| `message_start` | エージェント応答開始時 | エージェントメッセージを空でリストに追加 |
| `content_delta` | テキスト生成中（逐次） | エージェントメッセージの content を追記更新 |
| `tool_call` | ツール呼び出し開始時 | AgentStatusBar を「Redmine 操作中」に更新 |
| `tool_result` | ツール実行完了時 | AgentStatusBar を「考え中」に戻す |
| `message_end` | 応答完了時 | isLoading を false に変更 |
| `error` | エラー発生時 | エラーメッセージをチャットに表示 |

### 5.2 SSE 受信 Next.js API Route

```typescript
// src/app/api/v1/conversations/[id]/messages/route.ts
// Next.js は直接バックエンドへプロキシせず、フロントエンドから直接バックエンドに接続する
// (NEXT_PUBLIC_API_URL=http://localhost:8000)
// この Route ファイルは不要（直接接続方式）

// フロントエンドから直接 FastAPI へ SSE 接続する構成
// http://localhost:3000/chat → useChat hook → fetch http://localhost:8000/api/v1/...
```

---

## 6. ルーティング設計

### 6.1 App Router ファイル構成

```typescript
// src/app/chat/page.tsx
import { ChatWindow } from "@/components/chat/ChatWindow";
import { MainLayout } from "@/components/layout/MainLayout";

export const metadata = {
  title: "チャット | personal-agent",
};

// 会話 ID はサーバーサイドで生成（または localStorage から取得）
export default function ChatPage() {
  return (
    <MainLayout>
      <ChatWindow conversationId="default" />
    </MainLayout>
  );
}
```

### 6.2 会話 ID 管理方針

フェーズ 1 では会話 ID を固定値（"default"）とする。セッションごとの会話分離が必要な場合は、`localStorage` または Cookie で管理する。

```typescript
// src/hooks/useConversationId.ts
import { useState, useEffect } from "react";

const STORAGE_KEY = "personal-agent-conversation-id";

export function useConversationId(): string {
  const [conversationId, setConversationId] = useState<string>("default");

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      setConversationId(stored);
    } else {
      const newId = crypto.randomUUID();
      localStorage.setItem(STORAGE_KEY, newId);
      setConversationId(newId);
    }
  }, []);

  return conversationId;
}
```

---

## 7. エラー表示設計

### 7.1 エラー表示パターン

| エラー種別 | 表示場所 | 表示内容 |
|---|---|---|
| メッセージ送信失敗（ネットワークエラー） | チャット画面内のエラーメッセージ + Toast | 「エージェントとの通信に失敗しました。再試行してください。」 |
| Redmine 接続失敗 | エージェントの返答として表示 | 「申し訳ありません。Redmine との接続に失敗しました。Redmine が起動しているか確認してください。」 |
| Claude API 接続失敗 | Toast 通知 + エラーメッセージ | 「処理に失敗しました。しばらく後に再試行してください。」 |
| タイムアウト（30秒） | Toast 通知 | 「処理に時間がかかっています。しばらくお待ちください。」 |
| 入力バリデーション（4000 文字超） | 入力欄下部 | 「メッセージは4000文字以内で入力してください。」 |

### 7.2 エラーバウンダリ

```tsx
// src/components/ErrorBoundary.tsx
"use client";

import { Component, type ReactNode, type ErrorInfo } from "react";
import { Button } from "@/components/ui/button";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error("ErrorBoundary caught:", error, info);
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center h-full p-8">
          <h2 className="text-lg font-semibold text-red-600 mb-2">
            予期しないエラーが発生しました
          </h2>
          <p className="text-gray-600 mb-4 text-sm">
            {this.state.error?.message}
          </p>
          <Button
            onClick={() => this.setState({ hasError: false, error: null })}
            variant="outline"
          >
            再試行
          </Button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
```

---

## 8. アクセシビリティ設計

### 8.1 ARIA 対応方針

| 要素 | ARIA 属性 | 値 |
|---|---|---|
| メッセージリスト | `role="list"` + `aria-label` | `"チャットメッセージ一覧"` |
| 各メッセージ | `role="listitem"` + `aria-label` | `"あなたのメッセージ"` / `"エージェントのメッセージ"` |
| 入力フォーム | `aria-label` | `"メッセージ入力欄"` |
| 送信ボタン | `aria-label` | `"メッセージを送信"` |
| エージェント状態 | `role="status"` + `aria-live="polite"` | エージェントの実行状態 |
| メッセージリスト更新 | `aria-live="polite"` | 新しいメッセージの読み上げ |

### 8.2 キーボード操作

| キー | 動作 |
|---|---|
| `Enter` | メッセージ送信 |
| `Shift + Enter` | 改行 |
| `Tab` | フォーカス移動（入力欄 → 送信ボタン） |
| `Escape` | 入力欄のテキストをクリア |

---

## 9. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-002_FEAT-001 | 本設計書に基づくフロントエンド実装・Jest テスト実施報告 |
| DSD-008_FEAT-001 | MessageBubble・MessageInput・useChat の単体テスト設計 |
| ST-001 | チャット画面の E2E テストシナリオ（ユーザー入力 → SSE 応答 → 表示確認） |
