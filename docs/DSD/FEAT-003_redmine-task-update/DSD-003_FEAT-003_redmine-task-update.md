# DSD-003_FEAT-003 API詳細設計書（Redmineタスク更新・進捗報告）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-003_FEAT-003 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-003 |
| 機能名 | Redmineタスク更新・進捗報告 |
| 入力元 | BSD-005, BSD-007, REQ-005 |
| ステータス | 初版 |

---

## 目次

1. API設計方針
2. エンドポイント一覧
3. エンドポイント詳細仕様
4. バリデーション仕様
5. SSEストリーミング仕様
6. エラーレスポンス仕様
7. OpenAPIスキーマ定義
8. 後続フェーズへの影響

---

## 1. API設計方針

### 1.1 基本方針

FEAT-003（タスク更新・進捗報告）に関連するAPIエンドポイントは以下の2つである:

1. **POST `/api/v1/conversations/{id}/messages`**: チャットメッセージ送信。エージェントが自然言語を解析し `update_task_status` または `add_task_comment` ツールを呼び出す。SSEで応答をストリーミング返却する。
2. **PUT `/api/v1/tasks/{id}`**: タスク直接更新API。チャット経由ではなくタスク詳細画面（SCR-005）からの直接操作に使用する。

### 1.2 共通仕様（BSD-005参照）

- ベースURL: `http://localhost:8000/api/v1`（ローカル環境）
- リクエスト形式: `application/json`
- レスポンス形式（非SSE）: `application/json`
- レスポンス形式（SSE）: `text/event-stream`
- エンコーディング: UTF-8
- バージョニング: URLパス方式 `/api/v1/`

---

## 2. エンドポイント一覧

| No. | メソッド | エンドポイント | 機能概要 | 認証 | SSE |
|---|---|---|---|---|---|
| 1 | POST | `/api/v1/conversations/{id}/messages` | チャットメッセージ送信（エージェント実行） | 不要（フェーズ1） | ○ |
| 2 | PUT | `/api/v1/tasks/{id}` | タスク更新（ステータス・コメント・優先度・期日） | 不要（フェーズ1） | × |

---

## 3. エンドポイント詳細仕様

### 3.1 POST `/api/v1/conversations/{id}/messages`

**概要**: 指定した会話にメッセージを送信し、LangGraphエージェントを実行する。FEAT-003では「#123を完了にして」「#45にコメントを追加して」等の指示を処理する。応答はSSEで返す。

**HTTPメソッド**: POST

**パスパラメータ**:

| パラメータ名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | string (UUID) | 必須 | 会話ID |

**リクエストヘッダー**:

| ヘッダー | 値 | 必須 | 説明 |
|---|---|---|---|
| `Content-Type` | `application/json` | 必須 | リクエストボディの形式 |
| `Accept` | `text/event-stream` | 必須 | SSEレスポンスを要求する |

**リクエストボディ**:

| フィールド | 型 | 必須 | 説明 | 制約 |
|---|---|---|---|---|
| `content` | string | 必須 | ユーザーメッセージ | 1文字以上・4000文字以内。空文字・スペースのみ不可 |

**リクエスト例**:

```json
{
  "content": "#123を完了にして"
}
```

```json
{
  "content": "#45に「設計レビュー完了、明日マージ予定」とコメントして"
}
```

**レスポンス（成功）**:

HTTP 200 OK、`text/event-stream`形式でSSEストリームを返す。詳細は[セクション5: SSEストリーミング仕様]を参照。

**エラーレスポンス**:

| HTTPステータス | エラーコード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | `content` が未入力・4000文字超過・スペースのみ |
| 404 | `NOT_FOUND` | 指定 `id` の会話が存在しない |
| 422 | `UNPROCESSABLE_ENTITY` | エージェントが操作を実行できない（削除操作要求など） |
| 503 | `SERVICE_UNAVAILABLE` | Claude API / Redmine への接続失敗 |

**FastAPI実装スケルトン**:

```python
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1", tags=["conversations"])

class SendMessageRequest(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=4000,
        description="ユーザーメッセージ（1〜4000文字）",
    )

    @validator("content")
    def content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("メッセージは空にできません")
        return v

@router.post(
    "/conversations/{conversation_id}/messages",
    summary="メッセージ送信（エージェント実行）",
    response_description="SSEストリーミングレスポンス",
)
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    agent_service: AgentService = Depends(get_agent_service),
) -> StreamingResponse:
    """
    チャットメッセージを送信し、LangGraphエージェントを実行する。
    応答はSSE（Server-Sent Events）形式でストリーミング返却する。
    """
    # 会話の存在確認
    conversation = await conversation_repository.find_by_id(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "会話が見つかりません"}})

    return StreamingResponse(
        agent_service.run_stream(
            conversation_id=conversation_id,
            user_message=request.content,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginxのバッファリング無効化
        },
    )
```

---

### 3.2 PUT `/api/v1/tasks/{id}`

**概要**: 指定したRedmineタスクの情報を更新する。FEAT-003ではステータス変更（status）とコメント追加（notes）を処理する。タスク詳細画面（SCR-005）からの直接操作に使用する。

**HTTPメソッド**: PUT

**パスパラメータ**:

| パラメータ名 | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | string | 必須 | Redmine Issue ID（整数を文字列として表現） |

**リクエストヘッダー**:

| ヘッダー | 値 | 必須 |
|---|---|---|
| `Content-Type` | `application/json` | 必須 |

**リクエストボディ**:

| フィールド | 型 | 必須 | 説明 | 制約 |
|---|---|---|---|---|
| `status` | string | 任意 | ステータス名または内部コード | `open`, `in_progress`, `closed`, `rejected` のいずれか |
| `status_id` | integer | 任意 | ステータスID（直接指定） | {1, 2, 3, 5}のいずれか。`status` と排他 |
| `notes` | string | 任意 | コメント追加（Journal） | 1〜65535文字。空文字不可 |
| `priority` | string | 任意 | 優先度名（FEAT-004で使用） | `low`, `normal`, `high`, `urgent`, `immediate` |
| `due_date` | string | 任意 | 期日（FEAT-004で使用） | ISO 8601形式 `YYYY-MM-DD` |
| `title` | string | 任意 | タイトル変更 | 1〜200文字 |
| `description` | string | 任意 | 説明変更 | 65535文字以内 |

**注意**: FEAT-003ではprimarilyに `status` / `status_id` および `notes` を使用する。`priority` / `due_date` はFEAT-004で使用する。

**リクエスト例（ステータス更新）**:

```json
{
  "status_id": 3
}
```

```json
{
  "status": "closed",
  "notes": "設計レビューが完了したため完了に変更"
}
```

**リクエスト例（コメントのみ追加）**:

```json
{
  "notes": "進捗報告: フロントエンド実装完了。バックエンドは85%完了。"
}
```

**レスポンス（成功 200 OK）**:

```json
{
  "data": {
    "id": "123",
    "title": "設計書作成",
    "status": "closed",
    "status_name": "完了",
    "priority": "normal",
    "priority_name": "通常",
    "assignee": {
      "id": "1",
      "name": "山田 太郎"
    },
    "due_date": "2026-03-31",
    "updated_at": "2026-03-03T15:30:00+09:00"
  }
}
```

**エラーレスポンス**:

| HTTPステータス | エラーコード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | バリデーションエラー（無効なstatus_id、notesが空文字等） |
| 404 | `NOT_FOUND` | 指定IDのタスクが存在しない |
| 422 | `FORBIDDEN_OPERATION` | 削除操作の試行（BR-02） |
| 503 | `SERVICE_UNAVAILABLE` | Redmineへの接続失敗 |

**FastAPI実装スケルトン**:

```python
from pydantic import BaseModel, Field, validator
from typing import Optional

class UpdateTaskRequest(BaseModel):
    """タスク更新リクエストボディ。"""
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200,
        description="タスクタイトル（1〜200文字）",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=65535,
        description="タスク説明",
    )
    status: Optional[str] = Field(
        default=None,
        description="ステータス名（open/in_progress/closed/rejected）",
    )
    status_id: Optional[int] = Field(
        default=None,
        ge=1,
        description="ステータスID（環境変数 REDMINE_STATUS_ID_* で設定した値のいずれか）",
    )
    notes: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=65535,
        description="コメント追加（Journal）",
    )
    priority: Optional[str] = Field(
        default=None,
        description="優先度名（low/normal/high/urgent/immediate）",
    )
    due_date: Optional[str] = Field(
        default=None,
        description="期日（YYYY-MM-DD形式）",
    )

    @validator("status_id")
    def validate_status_id(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not TaskStatus.validate_id(v):
            valid_ids = list(TaskStatus._status_map().keys())
            raise ValueError(
                f"無効なステータスID: {v}。有効値: {valid_ids}（環境変数 REDMINE_STATUS_ID_* で設定）"
            )
        return v

    @validator("status")
    def validate_status_name(cls, v: Optional[str]) -> Optional[str]:
        valid_statuses = {"open", "in_progress", "closed", "rejected"}
        if v is not None and v not in valid_statuses:
            raise ValueError(
                f"無効なステータス名: {v}。有効値: {', '.join(sorted(valid_statuses))}"
            )
        return v

    @validator("notes")
    def validate_notes_not_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("コメントは空にできません")
        return v

    @validator("due_date")
    def validate_due_date_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            try:
                from datetime import date
                date.fromisoformat(v)
            except ValueError:
                raise ValueError("期日はYYYY-MM-DD形式で指定してください")
        return v

    @validator("priority")
    def validate_priority_name(cls, v: Optional[str]) -> Optional[str]:
        valid_priorities = {"low", "normal", "high", "urgent", "immediate"}
        if v is not None and v not in valid_priorities:
            raise ValueError(
                f"無効な優先度名: {v}。有効値: {', '.join(sorted(valid_priorities))}"
            )
        return v


@router.put(
    "/tasks/{task_id}",
    summary="タスク更新",
    response_description="更新後のタスク情報",
)
async def update_task(
    task_id: str,
    request: UpdateTaskRequest,
    task_service: TaskUpdateService = Depends(get_task_service),
) -> dict:
    """
    指定したRedmineタスクを更新する。
    ステータス変更・コメント追加・優先度変更・期日変更が可能。
    タスクの削除操作はBR-02により禁止。
    """
    try:
        result = await task_service.update_task_from_api(task_id, request)
        return {"data": result}
    except TaskNotFoundError as e:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": str(e)}})
    except TaskDeleteOperationForbiddenError as e:
        raise HTTPException(status_code=422, detail={"error": {"code": "FORBIDDEN_OPERATION", "message": str(e)}})
    except InvalidStatusIdError as e:
        raise HTTPException(status_code=400, detail={"error": {"code": "VALIDATION_ERROR", "message": str(e)}})
    except RedmineConnectionError as e:
        raise HTTPException(status_code=503, detail={"error": {"code": "SERVICE_UNAVAILABLE", "message": str(e)}})
```

---

## 4. バリデーション仕様

### 4.1 POST `/api/v1/conversations/{id}/messages` のバリデーション

| フィールド | バリデーションルール | エラーメッセージ |
|---|---|---|
| `content` | 必須 | 「contentは必須項目です」 |
| `content` | 1文字以上 | 「メッセージは空にできません」 |
| `content` | スペース・改行のみ不可 | 「メッセージは空にできません」 |
| `content` | 4000文字以内 | 「メッセージは4000文字以内で入力してください」 |
| パスパラメータ `id` | UUID形式 | 「会話IDの形式が不正です」 |

### 4.2 PUT `/api/v1/tasks/{id}` のバリデーション

| フィールド | バリデーションルール | エラーコード | エラーメッセージ |
|---|---|---|---|
| `status_id` | 環境変数 `REDMINE_STATUS_ID_*` で設定した有効値のいずれか | `VALIDATION_ERROR` | 「無効なステータスID: {value}。有効値: {valid_ids}（環境変数 REDMINE_STATUS_ID_* で設定）」 |
| `status` | `open`, `in_progress`, `closed`, `rejected`のいずれか | `VALIDATION_ERROR` | 「無効なステータス名: {value}」 |
| `status` と `status_id` | 同時指定不可 | `VALIDATION_ERROR` | 「statusとstatus_idは同時に指定できません」 |
| `notes` | 空文字・スペースのみ不可 | `VALIDATION_ERROR` | 「コメントは空にできません」 |
| `notes` | 65535文字以内 | `VALIDATION_ERROR` | 「コメントは65535文字以内で入力してください」 |
| `due_date` | YYYY-MM-DD形式 | `VALIDATION_ERROR` | 「期日はYYYY-MM-DD形式で指定してください」 |
| `title` | 1〜200文字 | `VALIDATION_ERROR` | 「タイトルは1〜200文字で入力してください」 |
| ボディ全体 | 少なくとも1フィールド必須 | `VALIDATION_ERROR` | 「更新するフィールドを1つ以上指定してください」 |

### 4.3 ステータスID・名称の対応表

| status_id | status（名称コード） | 表示名（日本語） |
|---|---|---|
| 1 | `open` | 未着手 |
| 2 | `in_progress` | 進行中 |
| 3 | `closed` | 完了 |
| 5 | `rejected` | 却下 |

---

## 5. SSEストリーミング仕様

### 5.1 概要

POST `/api/v1/conversations/{id}/messages` のレスポンスは Server-Sent Events（SSE）形式で返す。各イベントは以下の形式:

```
data: {JSONペイロード}\n\n
```

### 5.2 SSEイベント一覧

| イベントタイプ | ペイロード | 発火タイミング |
|---|---|---|
| `message_start` | `{"type": "message_start", "message_id": "msg_xxx"}` | ストリーミング開始時 |
| `content_delta` | `{"type": "content_delta", "delta": "文字列"}` | エージェント応答テキストの差分 |
| `tool_call` | `{"type": "tool_call", "tool_call_id": "xxx", "tool": "update_task_status", "input": {...}}` | ツール呼び出し開始時 |
| `tool_result` | `{"type": "tool_result", "tool_call_id": "xxx", "tool": "update_task_status", "output": "...", "success": true}` | ツール実行完了時 |
| `message_end` | `{"type": "message_end", "total_tokens": 1024}` | ストリーミング終了時 |
| `error` | `{"type": "error", "code": "ERROR_CODE", "message": "エラーメッセージ"}` | エラー発生時 |

### 5.3 tool_call イベントの詳細ペイロード

**update_task_status の tool_call イベント**:

```
data: {"type": "tool_call", "tool_call_id": "toolu_01", "tool": "update_task_status", "input": {"issue_id": 123, "status_id": 3, "notes": null}}

```

**add_task_comment の tool_call イベント**:

```
data: {"type": "tool_call", "tool_call_id": "toolu_02", "tool": "add_task_comment", "input": {"issue_id": 45, "notes": "設計レビュー完了"}}

```

### 5.4 tool_result イベントの詳細ペイロード

**update_task_status の tool_result イベント（成功）**:

```
data: {"type": "tool_result", "tool_call_id": "toolu_01", "tool": "update_task_status", "output": "{\"issue_id\": 123, \"title\": \"設計書作成\", \"new_status\": \"完了\", \"redmine_url\": \"http://localhost:8080/issues/123\"}", "success": true}

```

**update_task_status の tool_result イベント（失敗）**:

```
data: {"type": "tool_result", "tool_call_id": "toolu_01", "tool": "update_task_status", "output": "エラー: タスク #9999 は存在しません", "success": false}

```

### 5.5 ストリーミングシナリオ例

**シナリオ: 「#123を完了にして」**

```
data: {"type": "message_start", "message_id": "msg_abc123"}

data: {"type": "tool_call", "tool_call_id": "toolu_01", "tool": "update_task_status", "input": {"issue_id": 123, "status_id": 3}}

data: {"type": "tool_result", "tool_call_id": "toolu_01", "tool": "update_task_status", "output": "{\"issue_id\": 123, \"title\": \"設計書作成\", \"new_status\": \"完了\", \"redmine_url\": \"http://localhost:8080/issues/123\"}", "success": true}

data: {"type": "content_delta", "delta": "タスク "}

data: {"type": "content_delta", "delta": "#123「設計書作成」"}

data: {"type": "content_delta", "delta": "を**完了**に更新しました！"}

data: {"type": "message_end", "total_tokens": 512}

```

### 5.6 FastAPIでのSSEストリーム生成

```python
import json
from typing import AsyncGenerator

async def generate_sse_stream(
    agent_service: AgentService,
    conversation_id: str,
    user_message: str,
) -> AsyncGenerator[str, None]:
    """SSEストリームジェネレータ。"""

    async for event in agent_service.run_stream(conversation_id, user_message):
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    yield "data: [DONE]\n\n"
```

---

## 6. エラーレスポンス仕様

### 6.1 共通エラーレスポンス形式（BSD-005準拠）

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーの説明（日本語）",
    "details": [
      {
        "field": "フィールド名（バリデーションエラー時）",
        "message": "フィールドレベルのエラーメッセージ"
      }
    ]
  }
}
```

### 6.2 FEAT-003固有のエラーコード

| エラーコード | HTTPステータス | 説明 | 例 |
|---|---|---|---|
| `VALIDATION_ERROR` | 400 | 入力バリデーション失敗 | status_idが無効、notesが空文字 |
| `NOT_FOUND` | 404 | リソース未存在 | 指定IssueIDのチケットが存在しない |
| `FORBIDDEN_OPERATION` | 422 | ビジネスルール違反 | タスク削除操作の試行（BR-02） |
| `SERVICE_UNAVAILABLE` | 503 | 外部システム接続失敗 | Redmine接続エラー、Claude API接続エラー |

### 6.3 エラーレスポンス例

**バリデーションエラー（status_idが無効）**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "status_id",
        "message": "無効なステータスID: 10。有効値: 1=未着手, 2=進行中, 3=完了, 5=却下"
      }
    ]
  }
}
```

**リソース未存在（チケットID不存在）**:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "タスク #9999 は存在しません"
  }
}
```

**ビジネスルール違反（削除操作試行）**:
```json
{
  "error": {
    "code": "FORBIDDEN_OPERATION",
    "message": "エージェント経由のタスク削除操作は禁止されています（BR-02）。削除はRedmine Web UIから行ってください。"
  }
}
```

**Redmine接続エラー**:
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Redmineとの接続に失敗しました。Redmineが起動しているか確認してください。"
  }
}
```

---

## 7. OpenAPIスキーマ定義

### 7.1 UpdateTaskRequest スキーマ

```yaml
UpdateTaskRequest:
  type: object
  description: タスク更新リクエスト
  properties:
    title:
      type: string
      minLength: 1
      maxLength: 200
      description: タスクタイトル（変更する場合のみ指定）
    description:
      type: string
      maxLength: 65535
      description: タスク説明（変更する場合のみ指定）
    status:
      type: string
      enum: [open, in_progress, closed, rejected]
      description: |
        ステータス名（変更する場合のみ指定）。status_idと排他。
        - open: 未着手
        - in_progress: 進行中
        - closed: 完了
        - rejected: 却下
    status_id:
      type: integer
      enum: [1, 2, 3, 5]
      description: |
        ステータスID（変更する場合のみ指定）。statusと排他。
        - 1: 未着手
        - 2: 進行中
        - 3: 完了
        - 5: 却下
    notes:
      type: string
      minLength: 1
      maxLength: 65535
      description: コメント追加（Journal）。ステータス変更と同時指定可。
    priority:
      type: string
      enum: [low, normal, high, urgent, immediate]
      description: 優先度名（変更する場合のみ指定）
    due_date:
      type: string
      format: date
      description: 期日（YYYY-MM-DD形式）
  additionalProperties: false
  # 少なくとも1フィールドが必要
  minProperties: 1
```

### 7.2 TaskResponse スキーマ

```yaml
TaskResponse:
  type: object
  properties:
    id:
      type: string
      description: Redmine Issue ID
    title:
      type: string
      description: タスクタイトル
    status:
      type: string
      enum: [open, in_progress, closed, rejected]
      description: ステータス（内部コード）
    status_name:
      type: string
      description: ステータス表示名（日本語）
    priority:
      type: string
      enum: [low, normal, high, urgent, immediate]
      description: 優先度（内部コード）
    priority_name:
      type: string
      description: 優先度表示名（日本語）
    assignee:
      type: object
      nullable: true
      properties:
        id:
          type: string
        name:
          type: string
    due_date:
      type: string
      format: date
      nullable: true
    updated_at:
      type: string
      format: date-time
      description: 最終更新日時（ISO 8601、JST）
  required: [id, title, status, status_name, priority, priority_name, updated_at]
```

### 7.3 SendMessageRequest スキーマ

```yaml
SendMessageRequest:
  type: object
  required: [content]
  properties:
    content:
      type: string
      minLength: 1
      maxLength: 4000
      description: ユーザーメッセージ（1〜4000文字）
  additionalProperties: false
```

---

## 8. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| DSD-001_FEAT-003 | FastAPIルーターの実装詳細（バリデーション・エラーハンドリング）との整合確認 |
| DSD-005_FEAT-003 | RedmineアダプターとのAPIインターフェース（status_idマッピング・notesフィールド）の整合確認 |
| DSD-008_FEAT-003 | APIバリデーションのテストケース設計 |
| IMP-001_FEAT-003 | FastAPIルーターの実装（SendMessageRequest・UpdateTaskRequestのバリデーション） |
| IT-002 | API結合テスト: PUT /api/v1/tasks/{id}・POST /api/v1/conversations/{id}/messages の結合確認 |
