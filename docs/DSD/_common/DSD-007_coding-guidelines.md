# DSD-007 コーディング規約・開発ガイドライン

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-007 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 作成単位 | システム共通 |
| 入力元 | BSD-001, BSD-002, BSD-009 |
| ステータス | 初版 |

---

## 目次

1. 概要・適用範囲
2. Pythonコーディング規約（バックエンド）
3. TypeScript/Reactコーディング規約（フロントエンド）
4. フォルダ構成規約
5. 命名規則
6. テスト規約
7. ログ規約
8. エラーハンドリング規約
9. セキュリティコーディング規約
10. Gitコミット規約
11. コードレビュー規約
12. ツール・静的解析設定

---

## 1. 概要・適用範囲

### 1.1 目的

本ドキュメントは personal-agent プロジェクトにおけるコーディング規約・開発ガイドラインを定義する。一貫したコードスタイルと品質基準を維持し、保守性・可読性を高めることを目的とする。

### 1.2 適用範囲

| 対象 | 言語・フレームワーク | 適用規約 |
|---|---|---|
| バックエンド | Python 3.11+ / FastAPI / LangGraph | セクション 2, 4.1, 5.1, 6.1, 7, 8.1 |
| フロントエンド | TypeScript / Next.js 14+ / React | セクション 3, 4.2, 5.2, 6.2, 8.2 |
| 全体共通 | Git / テスト / セキュリティ | セクション 9, 10, 11, 12 |

### 1.3 優先順位

規約の優先順位は以下の通り。矛盾が生じた場合は上位を優先する。

1. 本ドキュメントの規約
2. 各言語の標準規約（PEP 8 / TypeScript ESLint 推奨設定）
3. フレームワークの推奨スタイル（FastAPI / Next.js）

---

## 2. Pythonコーディング規約（バックエンド）

### 2.1 基本方針

- PEP 8 に準拠する
- 行長: 最大 120 文字（PEP 8 の 79 文字より緩和。ruff の設定で適用）
- インデント: スペース 4 文字（タブ禁止）
- 文字コード: UTF-8（ファイル先頭の `# -*- coding: utf-8 -*-` は不要）
- 型ヒント: 全ての関数・メソッドの引数・戻り値に必須。`from __future__ import annotations` を使用する

### 2.2 型ヒント規約

```python
from __future__ import annotations

from typing import Optional, Union
from collections.abc import Sequence


# 良い例: 型ヒントを明示する
def create_task(
    title: str,
    description: str | None = None,
    priority: str = "normal",
    due_date: str | None = None,
    project_id: int = 1,
) -> dict[str, str | int]:
    """タスクを作成して結果を返す。"""
    ...


# 悪い例: 型ヒントなし
def create_task(title, description=None, priority="normal"):
    ...
```

**型ヒントのルール:**
- Python 3.10+ のユニオン型記法 `X | Y` を使用する（`Union[X, Y]` より優先）
- `Optional[X]` は `X | None` と書く
- コレクション型は `list[str]`・`dict[str, int]` のように小文字で書く（Python 3.9+）
- 複雑な型は `TypeAlias` で別名を定義する

```python
from typing import TypeAlias

TaskId: TypeAlias = str
RedmineIssueId: TypeAlias = int
ToolCallResult: TypeAlias = dict[str, str | int | list]
```

### 2.3 docstring 規約

Google スタイルの docstring を使用する。

```python
def search_tasks(
    status: str | None = None,
    due_date: str | None = None,
    keyword: str | None = None,
    project_id: int | None = None,
    limit: int = 25,
) -> list[dict]:
    """Redmine からタスク一覧を検索して返す。

    Args:
        status: タスクステータスでフィルタ（"open", "closed", "all"）。
            None の場合はフィルタなし。
        due_date: 期日でフィルタ（ISO 8601 形式 "YYYY-MM-DD"）。
            None の場合はフィルタなし。
        keyword: タイトル・説明のキーワード検索文字列。
        project_id: Redmine プロジェクト ID。
        limit: 取得件数の上限（デフォルト: 25, 最大: 100）。

    Returns:
        タスク情報の辞書のリスト。各辞書は以下のキーを含む:
        - id: タスク ID（文字列）
        - title: タスクタイトル
        - status: ステータス文字列
        - priority: 優先度文字列
        - due_date: 期日（YYYY-MM-DD または None）

    Raises:
        RedmineConnectionError: Redmine への接続に失敗した場合。
        RedmineAPIError: Redmine API がエラーレスポンスを返した場合。

    Examples:
        >>> tasks = search_tasks(status="open", keyword="設計書")
        >>> print(tasks[0]["title"])
        '設計書作成タスク'
    """
    ...
```

**docstring ルール:**
- すべての public 関数・クラス・モジュールに docstring を記述する
- private 関数（`_` プレフィックス）は省略可だが、複雑なロジックには記述する
- クラスの docstring はコンストラクタ引数の説明を含める

```python
class RedmineAdapter:
    """Redmine REST API との通信を担うアダプタークラス。

    MCP（Model Context Protocol）を介して Redmine の Issue を操作する。
    ACL（Anti-Corruption Layer）として機能し、Redmine のデータモデルを
    内部ドメインモデルに変換する責務を持つ。

    Attributes:
        base_url: Redmine サーバーのベース URL。
        api_key: Redmine API キー（環境変数 REDMINE_API_KEY から取得）。
        timeout: HTTPリクエストのタイムアウト秒数。

    Examples:
        >>> adapter = RedmineAdapter(
        ...     base_url="http://localhost:8080",
        ...     api_key="your_api_key",
        ... )
        >>> issue = await adapter.create_issue(project_id=1, subject="テスト")
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
```

### 2.4 インポート規約

```python
# 正しいインポート順序（isort に準拠）
# 1. 標準ライブラリ
from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, date
from typing import Any

# 2. サードパーティライブラリ
import httpx
import structlog
from fastapi import FastAPI, HTTPException, Depends
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field, validator

# 3. 自社モジュール（絶対インポート）
from app.domain.task import Task, TaskStatus, TaskPriority
from app.infra.redmine_adapter import RedmineAdapter
from app.application.task_create_service import TaskCreateService

logger = structlog.get_logger(__name__)
```

**インポートルール:**
- 相対インポート（`from . import xxx`）は禁止。常に絶対インポートを使用する
- 循環インポートは禁止。依存方向はレイヤードアーキテクチャに従う
- ワイルドカードインポート（`from xxx import *`）は禁止

### 2.5 クラス設計規約

```python
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(str, Enum):
    """タスクのステータスを表す値オブジェクト。

    Redmine のデフォルトステータスに対応する。
    """

    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"

    @classmethod
    def from_redmine_id(cls, status_id: int) -> TaskStatus:
        """Redmine のステータス ID から TaskStatus を生成する。

        Args:
            status_id: Redmine のステータス ID（整数）。

        Returns:
            対応する TaskStatus インスタンス。

        Raises:
            ValueError: 未知のステータス ID の場合。
        """
        mapping = {
            1: cls.NEW,
            2: cls.IN_PROGRESS,
            3: cls.RESOLVED,
            4: cls.CLOSED,
            5: cls.REJECTED,
        }
        if status_id not in mapping:
            raise ValueError(f"未知の Redmine ステータス ID: {status_id}")
        return mapping[status_id]


@dataclass(frozen=True)
class TaskPriority:
    """タスクの優先度を表す値オブジェクト。frozen=True で不変にする。"""

    name: str
    redmine_id: int

    LOW: ClassVar[TaskPriority]
    NORMAL: ClassVar[TaskPriority]
    HIGH: ClassVar[TaskPriority]
    URGENT: ClassVar[TaskPriority]


TaskPriority.LOW = TaskPriority(name="low", redmine_id=1)
TaskPriority.NORMAL = TaskPriority(name="normal", redmine_id=2)
TaskPriority.HIGH = TaskPriority(name="high", redmine_id=3)
TaskPriority.URGENT = TaskPriority(name="urgent", redmine_id=4)
```

### 2.6 非同期処理規約

```python
import asyncio
import httpx


# 良い例: async/await を使用した非同期処理
async def create_issue(self, subject: str, project_id: int) -> dict:
    """Redmine にイシューを非同期で作成する。"""
    async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(
            f"{self.base_url}/issues.json",
            json={"issue": {"subject": subject, "project_id": project_id}},
            headers={"X-Redmine-API-Key": self.api_key},
        )
        response.raise_for_status()
        return response.json()


# 悪い例: 同期処理をそのまま使用（FastAPI のイベントループをブロックする）
def create_issue_sync(self, subject: str, project_id: int) -> dict:
    import requests  # 禁止: 同期 HTTP クライアント
    response = requests.post(...)
    return response.json()
```

**非同期処理ルール:**
- FastAPI のエンドポイントはすべて `async def` で定義する
- HTTP クライアントは `httpx.AsyncClient` を使用する（`requests` ライブラリは禁止）
- データベース操作は SQLAlchemy の非同期セッションを使用する
- `asyncio.sleep()` の代わりに `await asyncio.sleep()` を使用する

### 2.7 Pydantic モデル規約

```python
from pydantic import BaseModel, Field, field_validator
from datetime import date


class TaskCreateRequest(BaseModel):
    """タスク作成 API のリクエストスキーマ。"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="タスクタイトル（必須・1〜200文字）",
        examples=["設計書レビュー"],
    )
    description: str | None = Field(
        default=None,
        max_length=10000,
        description="タスクの詳細説明（任意）",
    )
    priority: str = Field(
        default="normal",
        pattern="^(low|normal|high|urgent)$",
        description="優先度（low/normal/high/urgent）",
    )
    due_date: date | None = Field(
        default=None,
        description="期日（YYYY-MM-DD 形式）",
    )
    project_id: int = Field(
        default=1,
        ge=1,
        description="Redmine プロジェクト ID",
    )

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        """タイトルが空白のみの文字列でないことを検証する。"""
        if not v.strip():
            raise ValueError("タイトルは空白のみの文字列にできません")
        return v.strip()

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "設計書レビュー",
                    "description": "DSD-001 のレビューを実施する",
                    "priority": "high",
                    "due_date": "2026-03-31",
                    "project_id": 1,
                }
            ]
        }
    }
```

**Pydantic ルール:**
- すべての API リクエスト・レスポンスは Pydantic `BaseModel` を使用する
- `Field()` で説明・バリデーションルール・サンプルを明示する
- `field_validator` でビジネスロジックのバリデーションを実装する
- `model_config` で OpenAPI のサンプルを設定する

### 2.8 例外クラス規約

```python
class PersonalAgentError(Exception):
    """アプリケーション基底例外クラス。すべてのカスタム例外はこれを継承する。"""

    def __init__(self, message: str, error_code: str = "INTERNAL_ERROR") -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(message)


class RedmineConnectionError(PersonalAgentError):
    """Redmine への接続に失敗した場合の例外。"""

    def __init__(self, message: str = "Redmine への接続に失敗しました") -> None:
        super().__init__(message, error_code="SERVICE_UNAVAILABLE")


class RedmineAPIError(PersonalAgentError):
    """Redmine API がエラーレスポンスを返した場合の例外。"""

    def __init__(self, message: str, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(message, error_code="REDMINE_API_ERROR")


class TaskValidationError(PersonalAgentError):
    """タスクのバリデーションエラー。"""

    def __init__(self, message: str, field: str | None = None) -> None:
        self.field = field
        super().__init__(message, error_code="VALIDATION_ERROR")


class TaskNotFoundError(PersonalAgentError):
    """指定したタスクが存在しない場合の例外。"""

    def __init__(self, task_id: str) -> None:
        super().__init__(f"タスク ID {task_id} が見つかりません", error_code="NOT_FOUND")
```

---

## 3. TypeScript/Reactコーディング規約（フロントエンド）

### 3.1 基本方針

- TypeScript 厳格モード（`strict: true`）を使用する
- `any` 型の使用は原則禁止。やむを得ない場合は `// eslint-disable-next-line @typescript-eslint/no-explicit-any` でコメントを付ける
- `null` と `undefined` は明確に区別する。API レスポンスでは `null` を使用する
- React コンポーネントは関数コンポーネントのみ使用する（クラスコンポーネント禁止）

### 3.2 TypeScript 型定義規約

```typescript
// 良い例: 明示的な型定義
interface Task {
  id: string;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  dueDate: string | null; // ISO 8601 形式 "YYYY-MM-DD"
  createdAt: string; // ISO 8601 形式
  updatedAt: string;
}

type TaskStatus = "new" | "in_progress" | "resolved" | "closed" | "rejected";

type TaskPriority = "low" | "normal" | "high" | "urgent";

// API レスポンスの型定義
interface ApiResponse<T> {
  data: T;
  meta?: PaginationMeta;
}

interface PaginationMeta {
  total: number;
  page: number;
  perPage: number;
}

interface ApiError {
  error: {
    code: string;
    message: string;
    details?: Array<{ field: string; message: string }>;
  };
}
```

**型定義ルール:**
- `interface` はオブジェクト型の定義に使用する（`type` より `interface` を優先）
- `type` はユニオン型・プリミティブ型エイリアスに使用する
- ジェネリクスは積極的に活用する（特に API クライアント層）
- 型定義ファイルは `src/types/` ディレクトリに集約する

### 3.3 React コンポーネント規約

```tsx
import { useState, useCallback, type FC } from "react";
import type { Task } from "@/types/task";

// Props インターフェースは "Props" サフィックスを付ける
interface MessageBubbleProps {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  isStreaming?: boolean;
}

// コンポーネント名は PascalCase
const MessageBubble: FC<MessageBubbleProps> = ({
  role,
  content,
  timestamp,
  isStreaming = false,
}) => {
  const isUser = role === "user";

  return (
    <div
      className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}
      role="listitem"
      aria-label={`${isUser ? "あなた" : "エージェント"}のメッセージ`}
    >
      <div
        className={`max-w-3xl rounded-lg px-4 py-3 ${
          isUser
            ? "bg-blue-500 text-white"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        <div className="prose prose-sm max-w-none">
          {content}
        </div>
        {isStreaming && (
          <span className="inline-block w-2 h-4 bg-current animate-pulse ml-1" />
        )}
        <time
          className="block text-xs opacity-70 mt-1"
          dateTime={timestamp}
        >
          {new Date(timestamp).toLocaleTimeString("ja-JP")}
        </time>
      </div>
    </div>
  );
};

export default MessageBubble;
```

**コンポーネントルール:**
- 1ファイル1コンポーネントを基本とする
- Props は `interface` で定義し、ファイルの先頭付近に配置する
- デフォルトエクスポートを使用する（named export は hooks や型定義に使用）
- JSX ファイルの拡張子は `.tsx`、純粋な TS ファイルは `.ts`
- コンポーネント内に定義する関数は `useCallback` でメモ化する（props として渡す場合）

### 3.4 カスタム Hooks 規約

```typescript
import { useState, useEffect, useCallback, useRef } from "react";
import type { Message } from "@/types/chat";

interface UseChatOptions {
  conversationId: string;
  onError?: (error: Error) => void;
}

interface UseChatReturn {
  messages: Message[];
  isLoading: boolean;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

// Hooks は "use" プレフィックスを付ける
export function useChat({
  conversationId,
  onError,
}: UseChatOptions): UseChatReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (content: string): Promise<void> => {
      if (!content.trim()) return;

      // 前の SSE 接続をキャンセル
      abortControllerRef.current?.abort();
      const controller = new AbortController();
      abortControllerRef.current = controller;

      const userMessage: Message = {
        id: crypto.randomUUID(),
        role: "user",
        content,
        createdAt: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setIsLoading(true);

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
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        // SSE ストリーミング処理
        const reader = response.body?.getReader();
        if (!reader) throw new Error("Response body is not readable");

        const decoder = new TextDecoder();
        let assistantContent = "";

        const assistantMessage: Message = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "",
          createdAt: new Date().toISOString(),
        };

        setMessages((prev) => [...prev, assistantMessage]);

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = JSON.parse(line.slice(6));
              if (data.type === "content_delta") {
                assistantContent += data.delta;
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessage.id
                      ? { ...msg, content: assistantContent }
                      : msg
                  )
                );
              }
            }
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name !== "AbortError") {
          onError?.(error);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [conversationId, onError]
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // クリーンアップ
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  return { messages, isLoading, sendMessage, clearMessages };
}
```

**Hooks ルール:**
- Hooks は `src/hooks/` ディレクトリに配置する
- 戻り値の型は明示的に定義する
- `useEffect` の依存配列は必ず正確に指定する
- クリーンアップ関数（`return () => { ... }`）は必ず実装する

### 3.5 API クライアント規約

```typescript
// src/lib/api-client.ts
const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

class ApiClient {
  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${BASE_URL}${path}`;
    const response = await fetch(url, {
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new ApiError(
        errorData?.error?.message ?? "API エラーが発生しました",
        response.status,
        errorData?.error?.code ?? "UNKNOWN_ERROR"
      );
    }

    return response.json() as Promise<T>;
  }

  async getTasks(params: TaskSearchParams): Promise<ApiResponse<Task[]>> {
    const query = new URLSearchParams();
    if (params.status) query.set("status", params.status);
    if (params.keyword) query.set("keyword", params.keyword);
    if (params.page) query.set("page", String(params.page));

    return this.request<ApiResponse<Task[]>>(`/api/v1/tasks?${query}`);
  }

  async createTask(data: TaskCreateRequest): Promise<ApiResponse<Task>> {
    return this.request<ApiResponse<Task>>("/api/v1/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }
}

export const apiClient = new ApiClient();
```

---

## 4. フォルダ構成規約

### 4.1 バックエンド フォルダ構成

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI アプリケーションエントリーポイント
│   ├── config.py                  # 設定管理（環境変数読み込み）
│   │
│   ├── api/                       # プレゼンテーション層（FastAPI ルーター）
│   │   ├── __init__.py
│   │   ├── dependencies.py        # 依存性注入定義
│   │   ├── error_handlers.py      # エラーハンドラー
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── tasks.py           # タスク関連エンドポイント
│   │       ├── conversations.py   # 会話関連エンドポイント
│   │       └── health.py          # ヘルスチェック
│   │
│   ├── application/               # アプリケーション層（ユースケース）
│   │   ├── __init__.py
│   │   ├── task/
│   │   │   ├── __init__.py
│   │   │   ├── task_create_service.py
│   │   │   └── task_search_service.py
│   │   └── agent/
│   │       ├── __init__.py
│   │       └── agent_service.py
│   │
│   ├── domain/                    # ドメイン層（エンティティ・値オブジェクト・ドメインサービス）
│   │   ├── __init__.py
│   │   ├── task/
│   │   │   ├── __init__.py
│   │   │   ├── task.py            # Task エンティティ
│   │   │   ├── task_status.py     # TaskStatus 値オブジェクト
│   │   │   └── task_priority.py   # TaskPriority 値オブジェクト
│   │   └── conversation/
│   │       ├── __init__.py
│   │       ├── conversation.py    # Conversation エンティティ
│   │       └── message.py         # Message 値オブジェクト
│   │
│   ├── infra/                     # インフラストラクチャ層（外部システム連携・DB）
│   │   ├── __init__.py
│   │   ├── redmine/
│   │   │   ├── __init__.py
│   │   │   ├── redmine_adapter.py  # Redmine REST API アダプター
│   │   │   └── mcp_client.py       # MCP クライアント
│   │   ├── claude/
│   │   │   ├── __init__.py
│   │   │   └── claude_client.py    # Anthropic Claude API クライアント
│   │   └── db/
│   │       ├── __init__.py
│   │       ├── session.py          # DB セッション管理
│   │       └── models.py           # SQLAlchemy ORM モデル
│   │
│   └── agent/                     # LangGraph エージェント定義
│       ├── __init__.py
│       ├── graph.py               # LangGraph ワークフロー定義
│       ├── state.py               # エージェント状態定義
│       ├── nodes/
│       │   ├── __init__.py
│       │   ├── task_create_node.py
│       │   └── task_search_node.py
│       └── tools/
│           ├── __init__.py
│           ├── create_task_tool.py
│           └── search_tasks_tool.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # pytest フィクスチャ
│   ├── unit/
│   │   ├── test_task_create_service.py
│   │   ├── test_task_search_service.py
│   │   ├── test_redmine_adapter.py
│   │   └── test_agent_tools.py
│   └── integration/
│       ├── test_tasks_api.py
│       └── test_conversations_api.py
│
├── alembic/                       # DB マイグレーション
│   ├── env.py
│   └── versions/
│
├── requirements.txt               # 本番用依存関係
├── requirements-dev.txt           # 開発用依存関係（pytest, ruff 等）
├── pyproject.toml                 # プロジェクト設定（ruff, pytest）
└── .env.example                   # 環境変数テンプレート
```

### 4.2 フロントエンド フォルダ構成

```
frontend/
├── src/
│   ├── app/                       # Next.js App Router
│   │   ├── layout.tsx             # ルートレイアウト
│   │   ├── page.tsx               # ダッシュボード（/）
│   │   ├── chat/
│   │   │   └── page.tsx           # チャット画面（/chat）
│   │   ├── tasks/
│   │   │   ├── page.tsx           # タスク一覧（/tasks）
│   │   │   ├── new/
│   │   │   │   └── page.tsx       # タスク作成（/tasks/new）
│   │   │   └── [id]/
│   │   │       └── page.tsx       # タスク詳細（/tasks/[id]）
│   │   └── settings/
│   │       └── page.tsx           # 設定（/settings）
│   │
│   ├── components/                # React コンポーネント
│   │   ├── ui/                    # 汎用 UI コンポーネント（Shadcn/ui）
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   └── ...
│   │   ├── chat/                  # チャット関連コンポーネント
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── MessageInput.tsx
│   │   ├── task/                  # タスク関連コンポーネント
│   │   │   ├── TaskCard.tsx
│   │   │   ├── TaskList.tsx
│   │   │   └── TaskForm.tsx
│   │   └── layout/                # レイアウトコンポーネント
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── MainLayout.tsx
│   │
│   ├── hooks/                     # カスタム Hooks
│   │   ├── useChat.ts
│   │   ├── useTasks.ts
│   │   └── useToast.ts
│   │
│   ├── lib/                       # ユーティリティ・API クライアント
│   │   ├── api-client.ts          # API クライアント
│   │   ├── api-error.ts           # エラークラス
│   │   └── utils.ts               # 汎用ユーティリティ
│   │
│   └── types/                     # TypeScript 型定義
│       ├── task.ts
│       ├── chat.ts
│       └── api.ts
│
├── public/                        # 静的ファイル
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── .eslintrc.json
└── next.config.ts
```

---

## 5. 命名規則

### 5.1 バックエンド命名規則（Python）

| 対象 | 規則 | 例 |
|---|---|---|
| クラス名 | PascalCase | `TaskCreateService`, `RedmineAdapter` |
| 関数名 | snake_case | `create_task`, `search_issues` |
| 変数名 | snake_case | `task_id`, `redmine_api_key` |
| 定数名 | UPPER_SNAKE_CASE | `MAX_RETRY_COUNT`, `DEFAULT_PAGE_SIZE` |
| モジュール名 | snake_case | `task_create_service.py`, `redmine_adapter.py` |
| パッケージ名 | snake_case | `task/`, `infra/` |
| テストファイル | `test_` プレフィックス | `test_task_create_service.py` |
| テスト関数 | `test_` プレフィックス | `test_create_task_success` |
| プライベートメンバー | `_` プレフィックス | `_validate_title`, `_api_key` |
| 抽象クラス | `Abstract` プレフィックス | `AbstractTaskRepository` |
| インターフェース（Protocol） | `I` プレフィックスなし | `TaskRepository`（Protocolで定義） |
| 例外クラス | `Error` サフィックス | `RedmineConnectionError` |
| Pydantic モデル | `Request`/`Response` サフィックス | `TaskCreateRequest`, `TaskResponse` |
| Enum | PascalCase（値はUPPER_SNAKE_CASE） | `TaskStatus.IN_PROGRESS` |

### 5.2 フロントエンド命名規則（TypeScript/React）

| 対象 | 規則 | 例 |
|---|---|---|
| コンポーネント名 | PascalCase | `MessageBubble`, `TaskCard` |
| コンポーネントファイル | PascalCase | `MessageBubble.tsx`, `ChatWindow.tsx` |
| Props インターフェース | PascalCase + `Props` | `MessageBubbleProps` |
| カスタム Hooks | `use` + PascalCase | `useChat`, `useTasks` |
| 関数名 | camelCase | `sendMessage`, `fetchTasks` |
| 変数名 | camelCase | `taskId`, `isLoading` |
| 定数名 | UPPER_SNAKE_CASE | `MAX_MESSAGE_LENGTH`, `API_BASE_URL` |
| 型エイリアス | PascalCase | `TaskStatus`, `ApiResponse` |
| インターフェース | PascalCase（`I` プレフィックスなし） | `Task`, `Message` |
| Enum（TypeScriptのconst） | PascalCase + as const | `const TaskStatus = { ... } as const` |
| ファイル（hooks/lib） | camelCase | `useChat.ts`, `api-client.ts` |
| CSS クラス | Tailwind CSS の規則に従う | `bg-blue-500`, `text-gray-900` |
| データ属性 | kebab-case | `data-testid="send-button"` |

### 5.3 チャットUIコンポーネント共通命名規則

チャット画面（SCR-003）を構成するコンポーネントは、FEAT-005（chat-ui）の設計を正本とし、全機能（FEAT-001/003/005等）で以下の名称を統一して使用すること。

| コンポーネント役割 | 確定名称 | ファイルパス | 説明 |
|---|---|---|---|
| ページラッパー | `ChatPage` | `src/app/chat/page.tsx` | チャット画面のページエントリーポイント。Next.js App Router のページコンポーネント |
| チャットウィンドウ | `ChatWindow` | `src/components/chat/ChatWindow.tsx` | メッセージ一覧と入力欄を含むチャット全体コンテナ。状態管理のエントリーポイント |
| メッセージ一覧 | `MessageList` | `src/components/chat/MessageList.tsx` | メッセージ一覧の表示・自動スクロール制御 |
| 個別メッセージ | `MessageBubble` | `src/components/chat/MessageBubble.tsx` | 個別メッセージのバブル表示（user/assistant で色分け） |
| 入力欄 | `MessageInput` | `src/components/chat/MessageInput.tsx` | メッセージ入力欄・送信ボタン（Enter 送信・Shift+Enter 改行） |

**適用ルール**:
- 上記名称を別名（`ChatContainer`, `ChatMessageList`, `ChatMessage`, `ChatInput` 等）で定義・使用してはならない
- FEAT 固有の拡張コンポーネント（`ToolCallBadge`, `TaskUpdateConfirmation`, `AgentThinkingIndicator` 等）は命名制限なし
- 各 FEAT の DSD-002 でチャット関連コンポーネントを記述する場合は、本表の確定名称を参照すること

---

## 6. テスト規約

### 6.1 バックエンドテスト規約（pytest）

#### テストファイル・関数の命名

```python
# ファイル名: test_{テスト対象モジュール名}.py
# test_task_create_service.py

import pytest
from unittest.mock import AsyncMock, patch


class TestTaskCreateService:
    """TaskCreateService のテストクラス。"""

    # メソッド名: test_{テスト対象メソッド名}_{状況}_{期待結果}
    async def test_create_task_with_valid_input_returns_task(self):
        """正常系: 有効な入力でタスクが作成されること。"""
        ...

    async def test_create_task_with_empty_title_raises_validation_error(self):
        """異常系: 空のタイトルでバリデーションエラーが発生すること。"""
        ...

    async def test_create_task_when_redmine_unavailable_raises_connection_error(self):
        """異常系: Redmine 接続不可時に RedmineConnectionError が発生すること。"""
        ...
```

#### Given-When-Then パターン

```python
@pytest.mark.asyncio
async def test_create_task_success(
    mock_redmine_adapter: AsyncMock,
    task_create_service: TaskCreateService,
) -> None:
    """タスク作成成功のテスト（Given-When-Then パターン）。"""
    # Given: 有効なタスク作成パラメータと Redmine アダプターのモック
    title = "テストタスク"
    project_id = 1
    mock_redmine_adapter.create_issue.return_value = {
        "issue": {
            "id": 123,
            "subject": title,
            "status": {"id": 1, "name": "新規"},
            "priority": {"id": 2, "name": "通常"},
            "created_on": "2026-03-03T10:00:00Z",
        }
    }

    # When: タスクを作成する
    result = await task_create_service.create_task(
        title=title,
        project_id=project_id,
    )

    # Then: タスクが作成され、正しいデータが返ること
    assert result["id"] == "123"
    assert result["title"] == title
    mock_redmine_adapter.create_issue.assert_called_once_with(
        subject=title,
        project_id=project_id,
    )
```

#### conftest.py によるフィクスチャ

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock
from app.infra.redmine.redmine_adapter import RedmineAdapter
from app.application.task.task_create_service import TaskCreateService


@pytest.fixture
def mock_redmine_adapter() -> AsyncMock:
    """RedmineAdapter のモックフィクスチャ。"""
    mock = AsyncMock(spec=RedmineAdapter)
    return mock


@pytest.fixture
def task_create_service(mock_redmine_adapter: AsyncMock) -> TaskCreateService:
    """TaskCreateService のフィクスチャ（RedmineAdapter をモック化）。"""
    return TaskCreateService(redmine_adapter=mock_redmine_adapter)
```

**テストルール:**
- テストクラス: `Test` + テスト対象クラス名
- テスト関数: `test_` + メソッド名 + `_` + 状況 + `_` + 期待結果
- 1テスト関数で1つのことだけテストする（単一責任）
- アサーションは 1 テストに複数許容するが、テスト観点は1つに絞る
- モックは `unittest.mock.AsyncMock` と `patch` を使用する

### 6.2 フロントエンドテスト規約（Jest + React Testing Library）

```typescript
// MessageBubble.test.tsx
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import MessageBubble from "@/components/chat/MessageBubble";

describe("MessageBubble コンポーネント", () => {
  // Given-When-Then パターン
  it("ユーザーメッセージが右側に表示されること", () => {
    // Given: ユーザーロールのメッセージ
    const props = {
      role: "user" as const,
      content: "タスクを作成してください",
      timestamp: "2026-03-03T10:00:00Z",
    };

    // When: コンポーネントをレンダリングする
    render(<MessageBubble {...props} />);

    // Then: メッセージが表示されること
    expect(screen.getByText("タスクを作成してください")).toBeInTheDocument();
    expect(screen.getByRole("listitem")).toHaveClass("justify-end");
  });

  it("エージェントメッセージが左側に表示されること", () => {
    // Given: エージェントロールのメッセージ
    const props = {
      role: "assistant" as const,
      content: "タスクを作成しました",
      timestamp: "2026-03-03T10:00:00Z",
    };

    // When: コンポーネントをレンダリングする
    render(<MessageBubble {...props} />);

    // Then: メッセージが左側に表示されること
    expect(screen.getByRole("listitem")).toHaveClass("justify-start");
  });

  it("ストリーミング中はカーソルが表示されること", () => {
    const props = {
      role: "assistant" as const,
      content: "処理中...",
      timestamp: "2026-03-03T10:00:00Z",
      isStreaming: true,
    };

    render(<MessageBubble {...props} />);

    // カーソルアニメーション要素が存在すること
    expect(screen.getByRole("listitem").querySelector(".animate-pulse")).toBeInTheDocument();
  });
});
```

**フロントエンドテストルール:**
- ユーザー操作には `userEvent` を使用する（`fireEvent` より優先）
- DOM クエリは `getByRole` > `getByLabelText` > `getByText` の優先順で使用する
- `getByTestId` は最終手段（`data-testid` 属性を追加した場合のみ）
- スナップショットテストは原則使用しない

---

## 7. ログ規約

### 7.1 使用ライブラリ

バックエンドのログは `structlog` を使用する。構造化ログ（JSON 形式）で出力し、検索・分析を容易にする。

```python
# app/config.py のログ設定
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),  # 本番環境
        # structlog.dev.ConsoleRenderer(),   # 開発環境（カラー出力）
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)
```

### 7.2 ログレベル定義

| レベル | 用途 | 例 |
|---|---|---|
| DEBUG | 開発時のデバッグ情報（本番では出力しない） | API リクエスト/レスポンスの全内容 |
| INFO | 通常の業務イベント | タスク作成成功・エージェント実行完了 |
| WARNING | 注意が必要な状況（継続可能） | Redmine への接続リトライ発生・低残高アラート |
| ERROR | エラー（処理継続不可） | Redmine 接続失敗・Claude API エラー |
| CRITICAL | システム停止レベル | DB 接続不可・設定ファイル読み込みエラー |

### 7.3 ログ出力ルール

```python
import structlog

logger = structlog.get_logger(__name__)


async def create_task(title: str, project_id: int) -> dict:
    """タスクを作成する。"""
    # 良い例: 構造化ログ + コンテキスト情報
    logger.info(
        "task_create_started",
        title=title[:50],  # 長い文字列は切り詰める
        project_id=project_id,
    )

    try:
        result = await redmine_adapter.create_issue(
            subject=title,
            project_id=project_id,
        )
        logger.info(
            "task_create_succeeded",
            task_id=result["issue"]["id"],
            title=title[:50],
        )
        return result
    except RedmineConnectionError as e:
        logger.error(
            "task_create_failed_redmine_unavailable",
            error=str(e),
            title=title[:50],
            project_id=project_id,
        )
        raise


# 禁止事項
# - APIキー・パスワードをログに出力しない
# - ユーザーの入力内容を全文ログに出力しない（先頭50文字に切り詰める）
# - print() でのデバッグログは禁止（structlog を使用する）
```

**ログのマスキングルール:**
- `ANTHROPIC_API_KEY`・`REDMINE_API_KEY` などの APIキーは絶対にログに出力しない
- ユーザーのチャット内容・タスク内容は先頭 50 文字に切り詰める
- パスワード・トークンを含む可能性のあるフィールドはログから除外する

---

## 8. エラーハンドリング規約

### 8.1 バックエンドエラーハンドリング

```python
# app/api/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from app.domain.exceptions import (
    PersonalAgentError,
    RedmineConnectionError,
    TaskValidationError,
    TaskNotFoundError,
)

HTTP_STATUS_MAP = {
    "VALIDATION_ERROR": 400,
    "NOT_FOUND": 404,
    "SERVICE_UNAVAILABLE": 503,
    "INTERNAL_ERROR": 500,
}


async def personal_agent_error_handler(
    request: Request,
    exc: PersonalAgentError,
) -> JSONResponse:
    """アプリケーション例外の共通エラーハンドラー。"""
    status_code = HTTP_STATUS_MAP.get(exc.error_code, 500)

    logger.error(
        "application_error",
        error_code=exc.error_code,
        message=exc.message,
        path=str(request.url),
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": exc.error_code,
                "message": exc.message,
            }
        },
    )
```

```python
# ルーター内でのエラーハンドリング例
@router.post("/tasks", status_code=201, response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    service: TaskCreateService = Depends(get_task_create_service),
) -> TaskResponse:
    """タスクを作成するエンドポイント。"""
    # ビジネスロジック例外はグローバルハンドラーで処理
    # ここでは予期しない例外のみキャッチする
    try:
        result = await service.create_task(
            title=request.title,
            description=request.description,
            priority=request.priority,
            due_date=request.due_date,
            project_id=request.project_id,
        )
        return TaskResponse(**result)
    except PersonalAgentError:
        raise  # グローバルハンドラーに委譲
    except Exception as e:
        logger.exception("unexpected_error", error=str(e))
        raise PersonalAgentError("予期しないエラーが発生しました")
```

### 8.2 フロントエンドエラーハンドリング

```typescript
// src/lib/api-error.ts
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly errorCode: string
  ) {
    super(message);
    this.name = "ApiError";
  }

  get isNotFound(): boolean {
    return this.statusCode === 404;
  }

  get isServiceUnavailable(): boolean {
    return this.statusCode === 503;
  }
}
```

```tsx
// コンポーネントでのエラーハンドリング
function ChatWindow() {
  const { sendMessage, isLoading } = useChat({
    conversationId,
    onError: (error) => {
      if (error instanceof ApiError) {
        if (error.isServiceUnavailable) {
          toast.error("Redmine またはエージェントに接続できません。しばらく後に再試行してください。");
        } else {
          toast.error(error.message);
        }
      } else {
        toast.error("予期しないエラーが発生しました。");
      }
    },
  });
  ...
}
```

---

## 9. セキュリティコーディング規約

### 9.1 APIキー管理

```python
# 良い例: 環境変数から取得し、コードに埋め込まない
import os
from functools import lru_cache


class Settings:
    """アプリケーション設定。環境変数から読み込む。"""

    anthropic_api_key: str = os.environ["ANTHROPIC_API_KEY"]
    redmine_api_key: str = os.environ["REDMINE_API_KEY"]
    redmine_url: str = os.environ.get("REDMINE_URL", "http://localhost:8080")


# 悪い例: コードに直接埋め込む（絶対禁止）
ANTHROPIC_API_KEY = "sk-ant-xxxxx"  # 禁止！
```

### 9.2 .gitignore 登録必須ファイル

```
# .gitignore に必ず含めること
.env
.env.local
.env.*.local
*.key
*.pem
```

### 9.3 入力バリデーション

```python
# 全ての外部入力（API リクエスト）は Pydantic で検証する
# SQLAlchemy ORM を使用し、生の SQL 文字列は禁止
# HTML を返す場合は自動エスケープを使用する（React は自動エスケープ済み）
```

---

## 10. Gitコミット規約

### 10.1 Conventional Commits

コミットメッセージは [Conventional Commits](https://www.conventionalcommits.org/) に従う。

**形式:**
```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

**type 一覧:**

| type | 説明 | 例 |
|---|---|---|
| `feat` | 新機能追加 | `feat(task): タスク作成 API を追加` |
| `fix` | バグ修正 | `fix(redmine): 接続タイムアウト時のリトライを修正` |
| `docs` | ドキュメント更新 | `docs(dsd): DSD-001 バックエンド設計書を更新` |
| `style` | コードスタイル（機能変更なし） | `style: ruff による自動フォーマット` |
| `refactor` | リファクタリング | `refactor(agent): LangGraph ノードを分割` |
| `test` | テスト追加・修正 | `test(task): タスク作成サービスのテストを追加` |
| `chore` | ビルド・ツール設定変更 | `chore: ruff の設定を更新` |

**scope 一覧:**

| scope | 対象 |
|---|---|
| `task` | タスク管理機能 |
| `chat` | チャット・会話機能 |
| `agent` | LangGraph エージェント |
| `redmine` | Redmine 連携 |
| `api` | FastAPI エンドポイント |
| `ui` | フロントエンド UI |
| `db` | データベース・マイグレーション |
| `config` | 設定・環境変数 |

**コミットメッセージ例:**
```
feat(task): タスク作成 API エンドポイントを実装

POST /api/v1/tasks エンドポイントを追加する。
Redmine MCP アダプター経由でタスクを作成し、
作成結果を JSON で返す。

Closes #123
```

### 10.2 ブランチ戦略

```
main           # 本番ブランチ（直接コミット禁止）
develop        # 開発ブランチ
feature/feat-001-task-create   # 機能ブランチ（FEAT-ID を含める）
fix/issue-123-redmine-timeout  # バグ修正ブランチ
```

### 10.3 コミット前チェック（pre-commit hook）

```bash
#!/bin/sh
# .git/hooks/pre-commit

# バックエンド: ruff チェック
cd backend && ruff check . && ruff format --check .

# フロントエンド: ESLint チェック
cd ../frontend && npm run lint
```

---

## 11. コードレビュー規約

### 11.1 レビュー観点

| 観点 | チェック項目 |
|---|---|
| 正確性 | 機能要件・詳細設計書（DSD）通りに実装されているか |
| 型安全性 | 型ヒント・TypeScript 型定義が正しいか |
| エラーハンドリング | 例外処理・エラーレスポンスが設計書通りか |
| テスト | 単体テストが十分なカバレッジを持つか（80%以上） |
| セキュリティ | APIキー漏洩・インジェクション対策が適切か |
| パフォーマンス | 不必要なデータベースクエリ・N+1 問題がないか |
| ログ | 適切なログレベル・マスキングが行われているか |

### 11.2 レビューコメント形式

```
# コードレビューのコメント形式
# 重大度: [BLOCKING] / [SUGGESTION] / [NITS]

[BLOCKING] セキュリティ上の問題: APIキーがログに出力されています。
マスキングを実装してください。

[SUGGESTION] パフォーマンス改善: RedmineAdapter のインスタンスを
毎リクエスト生成しているため、DI コンテナを使用してください。

[NITS] 変数名を `task_id` に変更してください（`id` だと曖昧）。
```

---

## 12. ツール・静的解析設定

### 12.1 バックエンド（pyproject.toml）

```toml
[tool.ruff]
target-version = "py311"
line-length = 120
select = [
    "E",   # pycodestyle
    "W",   # pycodestyle
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "N",   # pep8-naming
    "ANN", # flake8-annotations（型ヒントチェック）
]
ignore = [
    "ANN101",  # self の型ヒントは不要
    "ANN102",  # cls の型ヒントは不要
]

[tool.ruff.isort]
known-first-party = ["app"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=80"

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

### 12.2 フロントエンド（.eslintrc.json）

```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/strict",
    "plugin:@typescript-eslint/stylistic"
  ],
  "rules": {
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/no-unused-vars": ["error", { "argsIgnorePattern": "^_" }],
    "@typescript-eslint/explicit-function-return-type": "warn",
    "react-hooks/exhaustive-deps": "error",
    "no-console": ["warn", { "allow": ["warn", "error"] }]
  }
}
```

### 12.3 tsconfig.json（厳格モード）

```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "exactOptionalPropertyTypes": true
  }
}
```

---

## 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-001_{FEAT-ID} | バックエンド実装はセクション 2・4.1・5.1・6.1・7・8.1 の規約に従う |
| IMP-002_{FEAT-ID} | フロントエンド実装はセクション 3・4.2・5.2・6.2・8.2 の規約に従う |
| REV-003 | DSD→IMP レビューでコーディング規約への準拠を確認する |
| ST-003 | セキュリティテストでセクション 9 の規約遵守を確認する |
