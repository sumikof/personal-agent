# DSD-003_FEAT-001 API詳細設計書（Redmineタスク作成）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-003_FEAT-001 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-001 |
| 機能名 | Redmineタスク作成（redmine-task-create） |
| 入力元 | BSD-005 |
| ステータス | 初版 |

---

## 目次

1. 概要
2. エンドポイント一覧
3. エンドポイント詳細仕様
   - POST /api/v1/conversations/{id}/messages
   - POST /api/v1/tasks
4. バリデーション仕様
5. エラーコード一覧
6. SSE イベント仕様
7. OpenAPI スキーマ
8. 後続フェーズへの影響

---

## 1. 概要

### 1.1 対象エンドポイント

FEAT-001（Redmine タスク作成）に関わる API エンドポイントを定義する。

| No. | メソッド | エンドポイント | 概要 |
|---|---|---|---|
| 1 | POST | `/api/v1/conversations/{id}/messages` | チャット経由でエージェントにタスク作成を依頼する（SSE ストリーミング） |
| 2 | POST | `/api/v1/tasks` | フォーム画面から直接タスクを作成する（非ストリーミング） |

### 1.2 共通仕様

**ベース URL**: `http://localhost:8000`

**共通リクエストヘッダー:**

| ヘッダー | 値 | 必須 |
|---|---|---|
| `Content-Type` | `application/json` | ○（POST 時） |
| `Accept` | `application/json` または `text/event-stream`（SSE 利用時） | - |

**共通レスポンスヘッダー:**

| ヘッダー | 値 |
|---|---|
| `Content-Type` | `application/json` または `text/event-stream` |
| `X-Request-ID` | リクエスト追跡用 UUID |

---

## 2. エンドポイント一覧

| No. | メソッド | エンドポイント | HTTPステータス（正常） | 認証 | レート制限 |
|---|---|---|---|---|---|
| 1 | POST | `/api/v1/conversations/{id}/messages` | 200（SSE ストリーム開始） | 不要（フェーズ1） | なし（フェーズ1） |
| 2 | POST | `/api/v1/tasks` | 201 Created | 不要（フェーズ1） | なし（フェーズ1） |

---

## 3. エンドポイント詳細仕様

---

### 3.1 POST `/api/v1/conversations/{id}/messages`

**概要**: 指定した会話にユーザーメッセージを送信し、LangGraph エージェントを実行する。エージェントの思考過程・ツール呼び出し・応答テキストを SSE ストリーミングで返す。タスク作成の指示が含まれる場合、エージェントが自動的に `create_task_tool` を呼び出す。

**HTTPメソッド**: POST

**URL**: `/api/v1/conversations/{id}/messages`

#### パスパラメータ

| パラメータ名 | 型 | 必須 | 説明 | 例 |
|---|---|---|---|---|
| `id` | string (UUID) | ○ | 会話 ID | `550e8400-e29b-41d4-a716-446655440000` |

#### リクエストヘッダー

| ヘッダー | 値 | 必須 |
|---|---|---|
| `Content-Type` | `application/json` | ○ |
| `Accept` | `text/event-stream` | SSE を受信する場合は必須 |

#### リクエストボディ

| フィールド名 | 型 | 必須 | バリデーション | 説明 |
|---|---|---|---|---|
| `content` | string | ○ | 1〜4000 文字 | ユーザーのメッセージ内容 |

**リクエスト例:**
```json
{
  "content": "設計書レビューのタスクを作成してください。優先度は高で、期日は3月31日にしてください。"
}
```

#### レスポンス（SSE ストリーム: 200 OK）

**レスポンスヘッダー:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

**SSE イベント形式:**
```
data: {JSON}

data: {JSON}
```

各 JSON オブジェクトの型定義は以下の通り:

**message_start イベント:**
```json
{
  "type": "message_start",
  "message_id": "msg_01Mzx3...",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**content_delta イベント（テキスト生成）:**
```json
{
  "type": "content_delta",
  "delta": "タスクを作成します"
}
```

**tool_call イベント（ツール呼び出し開始）:**
```json
{
  "type": "tool_call",
  "tool_call_id": "toolu_01A09q90...",
  "tool": "create_task",
  "input": {
    "title": "設計書レビュー",
    "priority": "high",
    "due_date": "2026-03-31",
    "project_id": 1
  }
}
```

**tool_result イベント（ツール実行結果）:**
```json
{
  "type": "tool_result",
  "tool_call_id": "toolu_01A09q90...",
  "tool": "create_task",
  "output": "タスクを作成しました。\n- ID: 124\n- タイトル: 設計書レビュー\n- URL: http://localhost:8080/issues/124"
}
```

**message_end イベント:**
```json
{
  "type": "message_end",
  "total_tokens": 1024,
  "input_tokens": 800,
  "output_tokens": 224
}
```

**error イベント:**
```json
{
  "type": "error",
  "code": "SERVICE_UNAVAILABLE",
  "message": "Redmine への接続に失敗しました"
}
```

**SSE ストリーム全体の例（タスク作成成功）:**
```
data: {"type": "message_start", "message_id": "msg_01Mzx3", "conversation_id": "550e8400-..."}

data: {"type": "content_delta", "delta": "設計書レビューのタスクを作成します。"}

data: {"type": "tool_call", "tool_call_id": "toolu_01A09q90", "tool": "create_task", "input": {"title": "設計書レビュー", "priority": "high", "due_date": "2026-03-31", "project_id": 1}}

data: {"type": "tool_result", "tool_call_id": "toolu_01A09q90", "tool": "create_task", "output": "タスクを作成しました。\n- ID: 124\n- タイトル: 設計書レビュー\n- 優先度: 高\n- 期日: 2026-03-31\n- URL: http://localhost:8080/issues/124"}

data: {"type": "content_delta", "delta": "「設計書レビュー」タスクを作成しました！\n\n"}

data: {"type": "content_delta", "delta": "- **チケット番号**: #124\n"}

data: {"type": "content_delta", "delta": "- **優先度**: 高\n"}

data: {"type": "content_delta", "delta": "- **期日**: 2026年3月31日\n"}

data: {"type": "content_delta", "delta": "- **URL**: http://localhost:8080/issues/124\n"}

data: {"type": "message_end", "total_tokens": 1024, "input_tokens": 800, "output_tokens": 224}

data: [DONE]
```

#### エラーレスポンス

| HTTPステータス | エラーコード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | `content` が未入力または 4000 文字超 |
| 404 | `NOT_FOUND` | 指定 `id` の会話が存在しない |
| 503 | `SERVICE_UNAVAILABLE` | Claude API または Redmine への接続失敗 |
| 500 | `INTERNAL_ERROR` | 予期しないサーバーエラー |

**エラーレスポンス例（400）:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "content",
        "message": "メッセージは1文字以上4000文字以内で入力してください"
      }
    ]
  }
}
```

#### FastAPI 実装例

```python
# app/api/v1/conversations.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.application.agent.agent_service import AgentService
from app.api.dependencies import get_agent_service

router = APIRouter(prefix="/api/v1/conversations", tags=["conversations"])


class MessageRequest(BaseModel):
    """メッセージ送信リクエストスキーマ。"""
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="ユーザーメッセージ（1〜4000文字）",
    )


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    request: MessageRequest,
    service: AgentService = Depends(get_agent_service),
) -> StreamingResponse:
    """ユーザーメッセージを送信し、エージェントの応答を SSE で返す。"""
    async def event_generator():
        async for event in service.execute_stream(
            conversation_id=conversation_id,
            user_message=request.content,
        ):
            yield f"data: {event.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

---

### 3.2 POST `/api/v1/tasks`

**概要**: タスク作成フォーム（SCR-006）からの直接タスク作成。エージェントを経由せず、バックエンドが直接 Redmine MCP を呼び出す。

**HTTPメソッド**: POST

**URL**: `/api/v1/tasks`

#### リクエストボディ

| フィールド名 | 型 | 必須 | バリデーション | 説明 |
|---|---|---|---|---|
| `title` | string | ○ | 1〜200 文字、空白のみ不可 | タスクタイトル |
| `description` | string | × | 最大 10000 文字 | タスクの詳細説明 |
| `priority` | string | × | `"low"`, `"normal"`, `"high"`, `"urgent"` のいずれか | 優先度（デフォルト: `"normal"`） |
| `due_date` | string (date) | × | ISO 8601 形式 `"YYYY-MM-DD"`、過去日付は不可 | 期日 |
| `project_id` | integer | × | 1 以上の整数 | Redmine プロジェクト ID（デフォルト: 1） |

**リクエスト例:**
```json
{
  "title": "設計書レビュー",
  "description": "DSD-001 バックエンド詳細設計書のレビューを行う",
  "priority": "high",
  "due_date": "2026-03-31",
  "project_id": 1
}
```

#### レスポンス（成功: 201 Created）

| フィールド名 | 型 | 説明 |
|---|---|---|
| `data.id` | string | 作成されたタスクの Redmine Issue ID |
| `data.title` | string | タスクタイトル |
| `data.status` | string | タスクステータス（通常は `"new"`） |
| `data.priority` | string | 優先度 |
| `data.due_date` | string \| null | 期日（YYYY-MM-DD 形式） |
| `data.project_id` | integer | Redmine プロジェクト ID |
| `data.url` | string | Redmine チケット詳細ページの URL |
| `data.created_at` | string | 作成日時（ISO 8601 形式） |

**レスポンス例（成功）:**
```json
{
  "data": {
    "id": "124",
    "title": "設計書レビュー",
    "status": "new",
    "priority": "high",
    "due_date": "2026-03-31",
    "project_id": 1,
    "url": "http://localhost:8080/issues/124",
    "created_at": "2026-03-03T10:00:00+09:00"
  }
}
```

#### エラーレスポンス

| HTTPステータス | エラーコード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | タイトル未入力、200文字超、優先度値不正、日付形式不正 |
| 422 | `UNPROCESSABLE_ENTITY` | 過去日付の指定、存在しないプロジェクト ID |
| 503 | `SERVICE_UNAVAILABLE` | Redmine への接続失敗 |
| 500 | `INTERNAL_ERROR` | 予期しないサーバーエラー |

**エラーレスポンス例（400 - タイトル未入力）:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "title",
        "message": "タイトルは必須項目です"
      }
    ]
  }
}
```

**エラーレスポンス例（400 - タイトル文字数超過）:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "title",
        "message": "タイトルは200文字以内で入力してください（現在: 205文字）"
      }
    ]
  }
}
```

**エラーレスポンス例（503 - Redmine 接続失敗）:**
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Redmine との接続に失敗しました。Redmine が起動しているか確認してください。"
  }
}
```

#### FastAPI 実装例

```python
# app/api/v1/tasks.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from datetime import date
from app.application.task.task_create_service import TaskCreateService
from app.api.dependencies import get_task_create_service

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])


class TaskCreateRequest(BaseModel):
    """タスク作成リクエストスキーマ。"""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="タスクタイトル（1〜200文字）",
    )
    description: str | None = Field(
        default=None,
        max_length=10000,
        description="タスクの詳細説明（任意）",
    )
    priority: str = Field(
        default="normal",
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
    def title_not_blank(cls, v: str) -> str:
        """タイトルが空白のみでないことを検証する。"""
        if not v.strip():
            raise ValueError("タイトルは空白のみの文字列にできません")
        return v.strip()

    @field_validator("priority")
    @classmethod
    def priority_valid(cls, v: str) -> str:
        """優先度の値を検証する。"""
        valid_values = {"low", "normal", "high", "urgent"}
        if v not in valid_values:
            raise ValueError(
                f"優先度は {', '.join(sorted(valid_values))} のいずれかを指定してください"
            )
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_not_past(cls, v: date | None) -> date | None:
        """期日が過去日付でないことを検証する。"""
        if v is not None and v < date.today():
            raise ValueError("期日に過去の日付は指定できません")
        return v


class TaskResponse(BaseModel):
    """タスク作成レスポンスのデータ部分。"""
    id: str
    title: str
    status: str
    priority: str
    due_date: str | None = None
    project_id: int
    url: str
    created_at: str


class TaskCreateResponse(BaseModel):
    """タスク作成 API レスポンス。"""
    data: TaskResponse


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=TaskCreateResponse,
    summary="タスクを作成する",
    description="Redmine に新しいタスク（チケット）を作成する。",
)
async def create_task(
    request: TaskCreateRequest,
    service: TaskCreateService = Depends(get_task_create_service),
) -> TaskCreateResponse:
    """タスクを作成するエンドポイント。"""
    result = await service.create_task(
        title=request.title,
        description=request.description,
        priority=request.priority,
        due_date=str(request.due_date) if request.due_date else None,
        project_id=request.project_id,
    )

    return TaskCreateResponse(
        data=TaskResponse(**result)
    )
```

---

## 4. バリデーション仕様

### 4.1 POST /api/v1/conversations/{id}/messages バリデーション

| フィールド | バリデーションルール | エラーメッセージ |
|---|---|---|
| `id`（パスパラメータ） | UUID v4 形式 | 404 NOT_FOUND（存在しない会話 ID の場合） |
| `content` | 必須・1〜4000 文字 | 「メッセージは1文字以上4000文字以内で入力してください」 |
| `content` | 空白のみ不可 | 「メッセージの内容を入力してください」 |

### 4.2 POST /api/v1/tasks バリデーション

| フィールド | バリデーションルール | エラーメッセージ |
|---|---|---|
| `title` | 必須・1〜200 文字・空白のみ不可 | 「タイトルは必須項目です」「タイトルは200文字以内で入力してください」 |
| `description` | 任意・最大 10000 文字 | 「説明は10000文字以内で入力してください」 |
| `priority` | `"low"`, `"normal"`, `"high"`, `"urgent"` のいずれか | 「優先度は low/normal/high/urgent のいずれかを指定してください」 |
| `due_date` | ISO 8601 日付形式・過去日付不可 | 「期日の形式が不正です（YYYY-MM-DD）」「期日に過去の日付は指定できません」 |
| `project_id` | 1 以上の整数 | 「プロジェクト ID は 1 以上の整数を指定してください」 |

---

## 5. エラーコード一覧

| エラーコード | HTTPステータス | 説明 | 発生状況 |
|---|---|---|---|
| `VALIDATION_ERROR` | 400 | 入力バリデーションエラー | 必須項目未入力・形式不正・範囲外の値 |
| `NOT_FOUND` | 404 | リソース未存在 | 指定した会話 ID が存在しない |
| `UNPROCESSABLE_ENTITY` | 422 | ビジネスロジックエラー | 過去日付・存在しないプロジェクト ID |
| `SERVICE_UNAVAILABLE` | 503 | 外部サービス接続失敗 | Redmine / Claude API への接続失敗 |
| `INTERNAL_ERROR` | 500 | サーバー内部エラー | 予期しない例外 |

---

## 6. SSE イベント仕様

### 6.1 イベント型一覧

| イベント型 | 説明 | フロントエンドの処理 |
|---|---|---|
| `message_start` | エージェント応答開始 | エージェントメッセージをリストに追加（空の content） |
| `content_delta` | テキスト差分 | エージェントメッセージの content に `delta` を追記 |
| `tool_call` | ツール呼び出し開始 | AgentStatusBar を「ツール実行中」表示に更新 |
| `tool_result` | ツール実行結果 | AgentStatusBar を「考え中」に戻す |
| `message_end` | 応答完了 | isLoading を false に設定 |
| `error` | エラー発生 | エラーメッセージを表示 |

### 6.2 イベント JSON スキーマ

```typescript
// SSE イベントの TypeScript 型定義
type SSEEvent =
  | {
      type: "message_start";
      message_id: string;
      conversation_id: string;
    }
  | {
      type: "content_delta";
      delta: string;
    }
  | {
      type: "tool_call";
      tool_call_id: string;
      tool: string;
      input: Record<string, unknown>;
    }
  | {
      type: "tool_result";
      tool_call_id: string;
      tool: string;
      output: string;
    }
  | {
      type: "message_end";
      total_tokens: number;
      input_tokens: number;
      output_tokens: number;
    }
  | {
      type: "error";
      code: string;
      message: string;
    };
```

---

## 7. OpenAPI スキーマ（概要）

FastAPI の自動生成 OpenAPI ドキュメントは `/docs` で確認可能。以下は主要なスキーマの抜粋。

```yaml
# openapi.yml（抜粋）
paths:
  /api/v1/conversations/{id}/messages:
    post:
      summary: メッセージ送信（エージェント実行）
      operationId: send_message
      parameters:
        - name: id
          in: path
          required: true
          schema:
            type: string
            format: uuid
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageRequest'
      responses:
        '200':
          description: SSE ストリーム
          content:
            text/event-stream:
              schema:
                type: string
        '400':
          $ref: '#/components/responses/ValidationError'
        '404':
          $ref: '#/components/responses/NotFound'
        '503':
          $ref: '#/components/responses/ServiceUnavailable'

  /api/v1/tasks:
    post:
      summary: タスク作成
      operationId: create_task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskCreateRequest'
      responses:
        '201':
          description: タスク作成成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskCreateResponse'
        '400':
          $ref: '#/components/responses/ValidationError'
        '503':
          $ref: '#/components/responses/ServiceUnavailable'

components:
  schemas:
    MessageRequest:
      type: object
      required:
        - content
      properties:
        content:
          type: string
          minLength: 1
          maxLength: 4000
          description: ユーザーメッセージ
          example: 設計書レビューのタスクを作成してください

    TaskCreateRequest:
      type: object
      required:
        - title
      properties:
        title:
          type: string
          minLength: 1
          maxLength: 200
          description: タスクタイトル
          example: 設計書レビュー
        description:
          type: string
          maxLength: 10000
          nullable: true
        priority:
          type: string
          enum: [low, normal, high, urgent]
          default: normal
        due_date:
          type: string
          format: date
          nullable: true
          example: "2026-03-31"
        project_id:
          type: integer
          minimum: 1
          default: 1

    TaskCreateResponse:
      type: object
      properties:
        data:
          $ref: '#/components/schemas/TaskData'

    TaskData:
      type: object
      properties:
        id:
          type: string
          description: Redmine Issue ID
          example: "124"
        title:
          type: string
        status:
          type: string
          example: new
        priority:
          type: string
        due_date:
          type: string
          nullable: true
        project_id:
          type: integer
        url:
          type: string
          format: uri
          example: http://localhost:8080/issues/124
        created_at:
          type: string
          format: date-time

  responses:
    ValidationError:
      description: バリデーションエラー
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    NotFound:
      description: リソース未存在
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    ServiceUnavailable:
      description: 外部サービス接続失敗
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

    ErrorResponse:
      type: object
      properties:
        error:
          type: object
          properties:
            code:
              type: string
            message:
              type: string
            details:
              type: array
              items:
                type: object
                properties:
                  field:
                    type: string
                  message:
                    type: string
```

---

## 8. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-001_FEAT-001 | POST /api/v1/tasks エンドポイントの FastAPI 実装（バリデーション・エラーハンドリング含む） |
| IMP-002_FEAT-001 | フロントエンドの API クライアント実装（SSE 受信・エラーハンドリング） |
| DSD-008_FEAT-001 | API エンドポイントの結合テスト仕様（バリデーションエラーケース・SSE 受信テスト） |
| IT-002 | API 結合テスト仕様書（全エンドポイントの実動作確認） |
