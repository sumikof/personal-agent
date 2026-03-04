# DSD-003_FEAT-002 API詳細設計書（Redmineタスク検索・一覧表示）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-003_FEAT-002 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-002 |
| 機能名 | Redmineタスク検索・一覧表示（redmine-task-search） |
| 入力元 | BSD-005, DSD-001_FEAT-002, DSD-002_FEAT-002 |
| ステータス | 初版 |

---

## 目次

1. 概要
2. エンドポイント一覧
3. POST /api/v1/conversations/{id}/messages（FEAT-001 と共有）
4. GET /api/v1/tasks
5. GET /api/v1/conversations/{id}/messages
6. 共通仕様
7. FastAPI 実装設計
8. バリデーション設計
9. エラーレスポンス設計
10. OpenAPI スキーマ
11. 後続フェーズへの影響

---

## 1. 概要

FEAT-002 で使用する API エンドポイントの詳細仕様を定義する。

| 用途 | エンドポイント | FEAT |
|---|---|---|
| チャットでタスク検索を依頼する | `POST /api/v1/conversations/{id}/messages` | 共有（FEAT-001 と同一） |
| REST API でタスク一覧を取得する | `GET /api/v1/tasks` | FEAT-002 で新規追加 |
| 会話履歴を取得する | `GET /api/v1/conversations/{id}/messages` | FEAT-002 で新規追加 |

### 1.1 エンドポイント追加の背景

`POST /api/v1/conversations/{id}/messages` はチャット経由（エージェント呼び出し）でタスクを検索するエンドポイントであり FEAT-001 で定義済み。FEAT-002 では追加で以下の REST エンドポイントを提供する。

- `GET /api/v1/tasks`: フロントエンドが直接タスク一覧を取得するための REST API（チャット経由ではなく直接参照）
- `GET /api/v1/conversations/{id}/messages`: ページリロード後にチャット履歴を復元するための API

---

## 2. エンドポイント一覧

| # | メソッド | パス | 説明 | 認証 |
|---|---|---|---|---|
| 1 | POST | `/api/v1/conversations/{id}/messages` | チャットメッセージ送信（SSE ストリーミング） | なし（Phase 1） |
| 2 | GET | `/api/v1/tasks` | Redmine タスク一覧取得（REST） | なし（Phase 1） |
| 3 | GET | `/api/v1/conversations/{id}/messages` | 会話メッセージ履歴取得 | なし（Phase 1） |

---

## 3. POST /api/v1/conversations/{id}/messages（FEAT-001 と共有）

> 詳細は DSD-003_FEAT-001 を参照。FEAT-002 においても同一エンドポイントを使用する。
> ユーザーが「今日の期限タスクを見せて」とメッセージを送ると、エージェントが `search_tasks_tool` を呼び出してタスク一覧を返す。

### 3.1 FEAT-002 用の SSE ストリーム例

```
POST /api/v1/conversations/123e4567-e89b-12d3-a456-426614174000/messages
Content-Type: application/json

{"content": "今日の期限タスクを見せて"}

---

HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no

event: message_start
data: {"type":"message_start","message_id":"msg_abc123"}

event: tool_call
data: {
  "type": "tool_call",
  "tool_name": "search_tasks",
  "tool_call_id": "toolu_xyz789",
  "input": {
    "status": "open",
    "due_date": "2026-03-03"
  }
}

event: tool_result
data: {
  "type": "tool_result",
  "tool_call_id": "toolu_xyz789",
  "output": "## タスク一覧（2026-03-03 期限）（3件）\n\n1. [設計書レビュー](http://localhost:8080/issues/123) - **高** - 期日: 2026-03-03\n2. [API テスト](http://localhost:8080/issues/124) - 通常 - 期日: 2026-03-03\n3. [ドキュメント更新](http://localhost:8080/issues/125) - 低 - 期日: 2026-03-03",
  "status": "success"
}

event: content_delta
data: {"type":"content_delta","delta":"本日（2026年3月3日）が期限のタスクは3件あります。\n\n","message_id":"msg_abc123"}

event: content_delta
data: {"type":"content_delta","delta":"1. [設計書レビュー](http://localhost:8080/issues/123) - **高**\n","message_id":"msg_abc123"}

event: content_delta
data: {"type":"content_delta","delta":"2. [API テスト](http://localhost:8080/issues/124) - 通常\n","message_id":"msg_abc123"}

event: content_delta
data: {"type":"content_delta","delta":"3. [ドキュメント更新](http://localhost:8080/issues/125) - 低\n","message_id":"msg_abc123"}

event: content_delta
data: {"type":"content_delta","delta":"\n他に確認したいことがあればお気軽にどうぞ。","message_id":"msg_abc123"}

event: message_end
data: {"type":"message_end","message_id":"msg_abc123","finish_reason":"end_turn"}
```

---

## 4. GET /api/v1/tasks

### 4.1 概要

Redmine からタスク一覧を取得する REST API エンドポイント。
エージェント（チャット）を経由せずにフロントエンドが直接タスクデータを取得するために使用する。

### 4.2 リクエスト仕様

| 項目 | 値 |
|---|---|
| メソッド | GET |
| パス | `/api/v1/tasks` |
| 認証 | なし（Phase 1） |
| Content-Type | なし（クエリパラメータのみ） |

#### クエリパラメータ

| パラメータ名 | 型 | 必須 | デフォルト | 説明 |
|---|---|---|---|---|
| `status` | string | 任意 | `open` | タスクのステータスフィルタ。`open` / `closed` / `all` |
| `due_date` | string (YYYY-MM-DD) | 任意 | なし | 期日でフィルタ（完全一致） |
| `keyword` | string | 任意 | なし | タイトルの部分一致検索（1〜100文字） |
| `project_id` | integer | 任意 | なし | Redmine プロジェクト ID でフィルタ |
| `page` | integer | 任意 | `1` | ページ番号（1 以上） |
| `per_page` | integer | 任意 | `25` | 1 ページあたりの件数（1〜100） |

#### リクエスト例

```
GET /api/v1/tasks?status=open&due_date=2026-03-03
GET /api/v1/tasks?keyword=設計書&per_page=50
GET /api/v1/tasks?status=all&project_id=1&page=2&per_page=25
GET /api/v1/tasks
```

### 4.3 レスポンス仕様

#### 成功レスポンス（200 OK）

```json
{
  "data": {
    "tasks": [
      {
        "id": "123",
        "title": "設計書レビュー",
        "description": "DSD-001〜DSD-008 のレビューを実施する",
        "status": "新規",
        "priority": "high",
        "due_date": "2026-03-03",
        "project_id": 1,
        "project_name": "パーソナルエージェント開発",
        "url": "http://localhost:8080/issues/123",
        "created_at": "2026-02-20T09:00:00Z",
        "updated_at": "2026-03-01T14:30:00Z"
      },
      {
        "id": "124",
        "title": "API テスト実施",
        "description": null,
        "status": "進行中",
        "priority": "normal",
        "due_date": "2026-03-03",
        "project_id": 1,
        "project_name": "パーソナルエージェント開発",
        "url": "http://localhost:8080/issues/124",
        "created_at": "2026-02-22T10:00:00Z",
        "updated_at": "2026-03-02T09:00:00Z"
      }
    ],
    "pagination": {
      "total_count": 3,
      "page": 1,
      "per_page": 25,
      "total_pages": 1
    }
  }
}
```

#### レスポンスフィールド定義

| フィールド | 型 | 説明 |
|---|---|---|
| `data.tasks` | array | タスクオブジェクトの配列 |
| `data.tasks[].id` | string | Redmine チケット ID（文字列） |
| `data.tasks[].title` | string | チケットのタイトル（subject） |
| `data.tasks[].description` | string \| null | チケットの説明（null の場合あり） |
| `data.tasks[].status` | string | ステータス名（Redmine の表示名） |
| `data.tasks[].priority` | string | 優先度（`low` / `normal` / `high` / `urgent`） |
| `data.tasks[].due_date` | string \| null | 期日（YYYY-MM-DD 形式）または null |
| `data.tasks[].project_id` | integer | Redmine プロジェクト ID |
| `data.tasks[].project_name` | string | Redmine プロジェクト名 |
| `data.tasks[].url` | string | Redmine チケット詳細ページの URL |
| `data.tasks[].created_at` | string | 作成日時（ISO 8601 UTC） |
| `data.tasks[].updated_at` | string | 更新日時（ISO 8601 UTC） |
| `data.pagination.total_count` | integer | 条件に一致する全件数 |
| `data.pagination.page` | integer | 現在のページ番号 |
| `data.pagination.per_page` | integer | 1 ページあたりの件数 |
| `data.pagination.total_pages` | integer | 総ページ数 |

### 4.4 エラーレスポンス

| HTTP ステータス | error_code | 発生条件 |
|---|---|---|
| 400 | `INVALID_QUERY_PARAMETER` | クエリパラメータのバリデーションエラー |
| 503 | `REDMINE_UNAVAILABLE` | Redmine サーバーへの接続失敗・タイムアウト |
| 500 | `INTERNAL_SERVER_ERROR` | 予期しないサーバーエラー |

---

## 5. GET /api/v1/conversations/{id}/messages

### 5.1 概要

指定した会話の全メッセージ履歴を取得する。フロントエンドがページリロード後にチャット履歴を復元するために使用する。

### 5.2 リクエスト仕様

| 項目 | 値 |
|---|---|
| メソッド | GET |
| パス | `/api/v1/conversations/{id}/messages` |
| パスパラメータ | `id`: 会話 ID（UUID 形式） |
| 認証 | なし（Phase 1） |

#### クエリパラメータ

| パラメータ名 | 型 | 必須 | デフォルト | 説明 |
|---|---|---|---|---|
| `limit` | integer | 任意 | `50` | 取得するメッセージ件数（1〜200） |
| `before` | string (UUID) | 任意 | なし | このメッセージ ID より古いメッセージを取得（ページネーション） |

#### リクエスト例

```
GET /api/v1/conversations/123e4567-e89b-12d3-a456-426614174000/messages
GET /api/v1/conversations/123e4567-e89b-12d3-a456-426614174000/messages?limit=20
```

### 5.3 レスポンス仕様

#### 成功レスポンス（200 OK）

```json
{
  "data": {
    "conversation_id": "123e4567-e89b-12d3-a456-426614174000",
    "messages": [
      {
        "id": "msg_001",
        "role": "user",
        "content": "今日の期限タスクを見せて",
        "created_at": "2026-03-03T10:00:00Z"
      },
      {
        "id": "msg_002",
        "role": "assistant",
        "content": "本日（2026年3月3日）が期限のタスクは3件あります。\n\n1. [設計書レビュー](http://localhost:8080/issues/123) - **高**\n...",
        "created_at": "2026-03-03T10:00:05Z"
      }
    ],
    "has_more": false
  }
}
```

#### レスポンスフィールド定義

| フィールド | 型 | 説明 |
|---|---|---|
| `data.conversation_id` | string (UUID) | 会話 ID |
| `data.messages` | array | メッセージオブジェクトの配列（時系列昇順） |
| `data.messages[].id` | string | メッセージ ID |
| `data.messages[].role` | string | 送信者ロール（`user` / `assistant`） |
| `data.messages[].content` | string | メッセージ内容（Markdown を含む場合あり） |
| `data.messages[].created_at` | string | 作成日時（ISO 8601 UTC） |
| `data.has_more` | boolean | さらに古いメッセージがある場合 true |

### 5.4 エラーレスポンス

| HTTP ステータス | error_code | 発生条件 |
|---|---|---|
| 400 | `INVALID_CONVERSATION_ID` | `id` が UUID 形式でない |
| 404 | `CONVERSATION_NOT_FOUND` | 指定した会話 ID が存在しない |
| 500 | `INTERNAL_SERVER_ERROR` | 予期しないサーバーエラー |

---

## 6. 共通仕様

### 6.1 ベース URL

```
http://localhost:8000
```

### 6.2 共通レスポンスヘッダ

| ヘッダ | 値 | 説明 |
|---|---|---|
| `Content-Type` | `application/json` | 通常のレスポンス |
| `Content-Type` | `text/event-stream; charset=utf-8` | SSE レスポンス |
| `Access-Control-Allow-Origin` | `http://localhost:3000` | CORS（FastAPI CORS ミドルウェア） |

### 6.3 共通エラーレスポンス形式

```json
{
  "error": {
    "code": "ERROR_CODE_STRING",
    "message": "人間が読めるエラーメッセージ（日本語）",
    "details": [
      {
        "field": "フィールド名（バリデーションエラーの場合）",
        "message": "詳細メッセージ"
      }
    ]
  }
}
```

### 6.4 タイムゾーン

すべての日時フィールドは UTC（ISO 8601 形式）で返す。
- 正: `"2026-03-03T10:00:00Z"`
- 誤: `"2026-03-03T19:00:00+09:00"`

---

## 7. FastAPI 実装設計

### 7.1 GET /api/v1/tasks の実装

```python
# app/api/v1/tasks.py
from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field, field_validator
from datetime import date

from app.application.task.task_search_service import TaskSearchService
from app.infra.redmine.redmine_adapter import RedmineAdapter
from app.config import get_settings
from app.domain.exceptions import RedmineConnectionError, RedmineAuthError

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["tasks"])


class TaskResponse(BaseModel):
    """タスク情報レスポンスモデル。"""
    id: str
    title: str
    description: str | None
    status: str
    priority: str
    due_date: str | None
    project_id: int | None
    project_name: str
    url: str
    created_at: str
    updated_at: str


class PaginationResponse(BaseModel):
    """ページネーション情報レスポンスモデル。"""
    total_count: int
    page: int
    per_page: int
    total_pages: int


class TaskListData(BaseModel):
    """タスク一覧レスポンスのデータ部。"""
    tasks: list[TaskResponse]
    pagination: PaginationResponse


class TaskListResponse(BaseModel):
    """GET /api/v1/tasks のレスポンス。"""
    data: TaskListData


@router.get("/tasks", response_model=TaskListResponse)
async def get_tasks(
    status: Annotated[str, Query(pattern=r"^(open|closed|all)$")] = "open",
    due_date: Annotated[
        str | None,
        Query(pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD 形式"),
    ] = None,
    keyword: Annotated[
        str | None,
        Query(min_length=1, max_length=100, description="タイトル部分一致検索"),
    ] = None,
    project_id: Annotated[int | None, Query(ge=1, description="Redmine プロジェクト ID")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 25,
) -> TaskListResponse:
    """Redmine タスク一覧を取得する REST API。

    チャット（エージェント）を経由せず、直接タスクを取得する。
    """
    settings = get_settings()
    adapter = RedmineAdapter(
        base_url=settings.redmine_url,
        api_key=settings.redmine_api_key,
    )
    service = TaskSearchService(redmine_adapter=adapter)

    logger.info(
        "api_get_tasks_called",
        status=status,
        due_date=due_date,
        keyword=keyword[:30] if keyword else None,
        project_id=project_id,
        page=page,
        per_page=per_page,
    )

    try:
        # offset 計算
        offset = (page - 1) * per_page

        # TaskSearchService 経由で Redmine から取得
        response = await adapter.list_issues(
            project_id=project_id,
            status_id={"open": "open", "closed": "closed", "all": "*"}.get(status, "open"),
            due_date=due_date,
            subject_like=keyword,
            limit=per_page,
            offset=offset,
        )

        raw_issues = response.get("issues", [])
        total_count = response.get("total_count", len(raw_issues))

        # 内部形式に変換
        tasks = [service._format_task(issue) for issue in raw_issues]

        total_pages = max(1, (total_count + per_page - 1) // per_page)

        logger.info(
            "api_get_tasks_succeeded",
            result_count=len(tasks),
            total_count=total_count,
        )

        return TaskListResponse(
            data=TaskListData(
                tasks=[TaskResponse(**task) for task in tasks],
                pagination=PaginationResponse(
                    total_count=total_count,
                    page=page,
                    per_page=per_page,
                    total_pages=total_pages,
                ),
            )
        )

    except RedmineConnectionError as e:
        logger.error("api_get_tasks_redmine_connection_error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "REDMINE_UNAVAILABLE",
                    "message": "Redmine サーバーへの接続に失敗しました。Redmine が起動しているか確認してください。",
                    "details": [],
                }
            },
        ) from e

    except RedmineAuthError as e:
        logger.error("api_get_tasks_redmine_auth_error", error=str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "REDMINE_AUTH_ERROR",
                    "message": "Redmine API キーの設定を確認してください。",
                    "details": [],
                }
            },
        ) from e

    except Exception as e:
        logger.error("api_get_tasks_unexpected_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "サーバー内部エラーが発生しました。",
                    "details": [],
                }
            },
        ) from e
```

### 7.2 GET /api/v1/conversations/{id}/messages の実装

```python
# app/api/v1/conversations.py（追加エンドポイント）
import uuid

from fastapi import APIRouter, Depends, Query, HTTPException, Path
from pydantic import BaseModel
import structlog

from app.infra.database.conversation_repository import ConversationRepository
from app.infra.database.session import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["conversations"])


class MessageItemResponse(BaseModel):
    """メッセージ 1 件のレスポンス。"""
    id: str
    role: str
    content: str
    created_at: str


class ConversationMessagesData(BaseModel):
    """会話メッセージ一覧レスポンスのデータ部。"""
    conversation_id: str
    messages: list[MessageItemResponse]
    has_more: bool


class ConversationMessagesResponse(BaseModel):
    """GET /api/v1/conversations/{id}/messages のレスポンス。"""
    data: ConversationMessagesData


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=ConversationMessagesResponse,
)
async def get_conversation_messages(
    conversation_id: str = Path(description="会話 ID（UUID 形式）"),
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    before: Annotated[str | None, Query(description="このメッセージ ID より古いメッセージを取得")] = None,
    db: AsyncSession = Depends(get_db_session),
) -> ConversationMessagesResponse:
    """会話のメッセージ履歴を取得する。

    ページリロード後のチャット履歴復元に使用する。
    """
    # UUID バリデーション
    try:
        uuid.UUID(conversation_id)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "code": "INVALID_CONVERSATION_ID",
                    "message": "conversation_id は UUID 形式で指定してください。",
                    "details": [],
                }
            },
        ) from e

    logger.info(
        "api_get_conversation_messages_called",
        conversation_id=conversation_id,
        limit=limit,
    )

    repo = ConversationRepository(db)

    # 会話の存在確認
    conversation = await repo.find_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": {
                    "code": "CONVERSATION_NOT_FOUND",
                    "message": f"会話 ID '{conversation_id}' が見つかりません。",
                    "details": [],
                }
            },
        )

    # メッセージ取得（limit + 1 件取得して has_more を判定）
    messages = await repo.get_messages(
        conversation_id=conversation_id,
        limit=limit + 1,
        before_message_id=before,
    )

    has_more = len(messages) > limit
    if has_more:
        messages = messages[:limit]

    logger.info(
        "api_get_conversation_messages_succeeded",
        conversation_id=conversation_id,
        message_count=len(messages),
        has_more=has_more,
    )

    return ConversationMessagesResponse(
        data=ConversationMessagesData(
            conversation_id=conversation_id,
            messages=[
                MessageItemResponse(
                    id=str(msg.id),
                    role=msg.role,
                    content=msg.content or "",
                    created_at=msg.created_at.isoformat() + "Z",
                )
                for msg in messages
            ],
            has_more=has_more,
        )
    )
```

### 7.3 ルーター登録（main.py）

```python
# app/main.py（FEAT-002 で追加するルーター登録）
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import conversations, tasks   # tasks ルーターを追加

app = FastAPI(title="Personal Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(conversations.router)
app.include_router(tasks.router)   # FEAT-002 で追加
```

---

## 8. バリデーション設計

### 8.1 GET /api/v1/tasks クエリパラメータバリデーション

| パラメータ | バリデーションルール | エラー時のレスポンス |
|---|---|---|
| `status` | `open` / `closed` / `all` のいずれか | 400 `INVALID_QUERY_PARAMETER` |
| `due_date` | `YYYY-MM-DD` 形式（正規表現チェック） | 400 `INVALID_QUERY_PARAMETER` |
| `keyword` | 1〜100 文字 | 400 `INVALID_QUERY_PARAMETER` |
| `project_id` | 1 以上の整数 | 400 `INVALID_QUERY_PARAMETER` |
| `page` | 1 以上の整数 | 400 `INVALID_QUERY_PARAMETER` |
| `per_page` | 1〜100 の整数 | 400 `INVALID_QUERY_PARAMETER` |

### 8.2 FastAPI によるバリデーションエラーレスポンス

FastAPI の組み込み `RequestValidationError` を共通エラーフォーマットに変換する。

```python
# app/main.py
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    details = [
        {"field": ".".join(str(loc) for loc in error["loc"]), "message": error["msg"]}
        for error in exc.errors()
    ]
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "INVALID_QUERY_PARAMETER",
                "message": "リクエストパラメータが正しくありません。",
                "details": details,
            }
        },
    )
```

#### バリデーションエラーレスポンス例

```json
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": {
    "code": "INVALID_QUERY_PARAMETER",
    "message": "リクエストパラメータが正しくありません。",
    "details": [
      {
        "field": "query.status",
        "message": "String should match pattern '^(open|closed|all)$'"
      }
    ]
  }
}
```

---

## 9. エラーレスポンス設計

### 9.1 エラーコード一覧

| error_code | HTTP ステータス | 発生エンドポイント | 説明 |
|---|---|---|---|
| `INVALID_QUERY_PARAMETER` | 400 | GET /api/v1/tasks | クエリパラメータ不正 |
| `INVALID_CONVERSATION_ID` | 400 | GET /api/v1/conversations/{id}/messages | 会話 ID が UUID 形式でない |
| `CONVERSATION_NOT_FOUND` | 404 | GET /api/v1/conversations/{id}/messages | 会話 ID が存在しない |
| `REDMINE_UNAVAILABLE` | 503 | GET /api/v1/tasks | Redmine 接続失敗 |
| `REDMINE_AUTH_ERROR` | 503 | GET /api/v1/tasks | Redmine 認証失敗 |
| `INTERNAL_SERVER_ERROR` | 500 | 全エンドポイント | 予期しないサーバーエラー |

### 9.2 各エラーレスポンス例

```json
// 400 INVALID_QUERY_PARAMETER（due_date フォーマット不正）
{
  "error": {
    "code": "INVALID_QUERY_PARAMETER",
    "message": "リクエストパラメータが正しくありません。",
    "details": [
      {"field": "query.due_date", "message": "String should match pattern '^\\d{4}-\\d{2}-\\d{2}$'"}
    ]
  }
}

// 404 CONVERSATION_NOT_FOUND
{
  "error": {
    "code": "CONVERSATION_NOT_FOUND",
    "message": "会話 ID '123e4567-...' が見つかりません。",
    "details": []
  }
}

// 503 REDMINE_UNAVAILABLE
{
  "error": {
    "code": "REDMINE_UNAVAILABLE",
    "message": "Redmine サーバーへの接続に失敗しました。Redmine が起動しているか確認してください。",
    "details": []
  }
}
```

---

## 10. OpenAPI スキーマ

### 10.1 GET /api/v1/tasks の OpenAPI YAML

```yaml
/api/v1/tasks:
  get:
    summary: タスク一覧取得
    description: >
      Redmine からタスク（チケット）一覧を取得する。
      チャット（エージェント）を経由せず直接取得する REST API。
    operationId: get_tasks
    tags:
      - tasks
    parameters:
      - name: status
        in: query
        required: false
        schema:
          type: string
          enum: [open, closed, all]
          default: open
        description: タスクのステータスフィルタ
      - name: due_date
        in: query
        required: false
        schema:
          type: string
          pattern: '^\d{4}-\d{2}-\d{2}$'
          example: "2026-03-03"
        description: 期日でフィルタ（YYYY-MM-DD 形式、完全一致）
      - name: keyword
        in: query
        required: false
        schema:
          type: string
          minLength: 1
          maxLength: 100
        description: タイトルの部分一致検索
      - name: project_id
        in: query
        required: false
        schema:
          type: integer
          minimum: 1
        description: Redmine プロジェクト ID でフィルタ
      - name: page
        in: query
        required: false
        schema:
          type: integer
          minimum: 1
          default: 1
        description: ページ番号
      - name: per_page
        in: query
        required: false
        schema:
          type: integer
          minimum: 1
          maximum: 100
          default: 25
        description: 1 ページあたりの件数
    responses:
      "200":
        description: 成功
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskListResponse'
      "400":
        description: クエリパラメータ不正
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ErrorResponse'
      "503":
        description: Redmine 接続失敗
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ErrorResponse'
      "500":
        description: サーバー内部エラー
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ErrorResponse'

components:
  schemas:
    TaskResponse:
      type: object
      required: [id, title, status, priority, project_id, project_name, url, created_at, updated_at]
      properties:
        id:
          type: string
          description: Redmine チケット ID
          example: "123"
        title:
          type: string
          description: チケットタイトル
          example: "設計書レビュー"
        description:
          type: string
          nullable: true
          description: チケット説明
        status:
          type: string
          description: ステータス名（Redmine の表示名）
          example: "新規"
        priority:
          type: string
          enum: [low, normal, high, urgent]
          description: 優先度
          example: "high"
        due_date:
          type: string
          nullable: true
          pattern: '^\d{4}-\d{2}-\d{2}$'
          description: 期日（YYYY-MM-DD 形式）
          example: "2026-03-03"
        project_id:
          type: integer
          nullable: true
          description: Redmine プロジェクト ID
          example: 1
        project_name:
          type: string
          description: Redmine プロジェクト名
          example: "パーソナルエージェント開発"
        url:
          type: string
          format: uri
          description: Redmine チケット詳細ページ URL
          example: "http://localhost:8080/issues/123"
        created_at:
          type: string
          format: date-time
          description: 作成日時（ISO 8601 UTC）
        updated_at:
          type: string
          format: date-time
          description: 更新日時（ISO 8601 UTC）

    PaginationResponse:
      type: object
      required: [total_count, page, per_page, total_pages]
      properties:
        total_count:
          type: integer
          description: 条件に一致する全件数
          example: 3
        page:
          type: integer
          description: 現在のページ番号
          example: 1
        per_page:
          type: integer
          description: 1 ページあたりの件数
          example: 25
        total_pages:
          type: integer
          description: 総ページ数
          example: 1

    TaskListResponse:
      type: object
      required: [data]
      properties:
        data:
          type: object
          required: [tasks, pagination]
          properties:
            tasks:
              type: array
              items:
                $ref: '#/components/schemas/TaskResponse'
            pagination:
              $ref: '#/components/schemas/PaginationResponse'

    ErrorDetail:
      type: object
      properties:
        field:
          type: string
          description: エラーが発生したフィールド名
        message:
          type: string
          description: 詳細エラーメッセージ

    ErrorResponse:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message, details]
          properties:
            code:
              type: string
              description: エラーコード
              example: "INVALID_QUERY_PARAMETER"
            message:
              type: string
              description: エラーメッセージ（日本語）
              example: "リクエストパラメータが正しくありません。"
            details:
              type: array
              items:
                $ref: '#/components/schemas/ErrorDetail'
```

---

## 11. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| DSD-008_FEAT-002 | GET /api/v1/tasks エンドポイントの単体テスト設計（バリデーション・エラーハンドリング） |
| IMP-001_FEAT-002 | バックエンド実装報告書: GET /api/v1/tasks・GET /api/v1/conversations/{id}/messages の実装詳細 |
| IT-001_FEAT-002 | 結合テスト: GET /api/v1/tasks のエンドツーエンドテスト（Redmine Docker 連携） |
| IT-002 | API 結合テスト仕様書: 全エンドポイントの実動作確認 |
