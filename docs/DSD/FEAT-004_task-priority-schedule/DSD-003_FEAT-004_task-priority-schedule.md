# DSD-003_FEAT-004 API詳細設計書（タスク優先度・スケジュール調整）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-003_FEAT-004 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-004 |
| 機能名 | タスク優先度・スケジュール調整 |
| 入力元 | BSD-005, BSD-007, REQ-005 |
| ステータス | 初版 |

---

## 目次

1. API設計方針
2. エンドポイント一覧
3. エンドポイント詳細仕様
4. バリデーション仕様
5. SSEストリーミング仕様（FEAT-004対応追加）
6. エラーレスポンス仕様
7. OpenAPIスキーマ定義
8. 後続フェーズへの影響

---

## 1. API設計方針

### 1.1 基本方針

FEAT-004（タスク優先度・スケジュール調整）に関連するAPIエンドポイントは以下の2つである:

1. **POST `/api/v1/conversations/{id}/messages`**: FEAT-003と共用。「#123を緊急にして」「今日何をすればいい？」等の指示を処理する
2. **PUT `/api/v1/tasks/{id}`**: FEAT-003と共用エンドポイント。FEAT-004では `priority`・`due_date` フィールドの更新に対応する
3. **GET `/api/v1/tasks`**: タスク一覧取得。FEAT-004の `get_priority_report` ツールが内部で使用する（直接フロントエンドからは呼び出さない場合が多い）

### 1.2 FEAT-003との共有設計

PUT `/api/v1/tasks/{id}` は FEAT-003・FEAT-004 で共用する。`UpdateTaskRequest` にFEAT-004用フィールド（`priority`・`due_date`）がすでに定義されている（DSD-003_FEAT-003参照）。本ドキュメントではFEAT-004固有の拡張仕様を記述する。

---

## 2. エンドポイント一覧

| No. | メソッド | エンドポイント | 機能概要 | FEAT-004での用途 |
|---|---|---|---|---|
| 1 | POST | `/api/v1/conversations/{id}/messages` | チャットメッセージ送信（エージェント実行） | UC-005/UC-006/UC-007のチャット経由操作 |
| 2 | PUT | `/api/v1/tasks/{id}` | タスク更新 | UC-005（優先度変更）・UC-006（期日変更）の直接更新 |
| 3 | GET | `/api/v1/tasks` | タスク一覧取得 | UC-007（優先タスクレポート）の内部利用 |

---

## 3. エンドポイント詳細仕様

### 3.1 PUT `/api/v1/tasks/{id}`（FEAT-004拡張仕様）

**概要**: FEAT-003（DSD-003_FEAT-003）で定義したエンドポイントのFEAT-004固有の拡張仕様。`priority`（優先度）と `due_date`（期日）フィールドのバリデーション詳細を追加する。

**HTTPメソッド**: PUT

**パスパラメータ**: FEAT-003と同一（`id`: Redmine Issue ID）

**リクエストボディ（FEAT-004フィールド）**:

| フィールド | 型 | 必須 | 説明 | FEAT-004検証ルール |
|---|---|---|---|---|
| `priority` | string | 任意 | 優先度名 | `low`, `normal`, `high`, `urgent`, `immediate` のいずれか |
| `priority_id` | integer | 任意 | 優先度ID（直接指定） | {1, 2, 3, 4, 5} のいずれか。`priority` と排他 |
| `due_date` | string | 任意 | 期日（YYYY-MM-DD形式） | ISO 8601日付形式。過去の日付は警告するが登録は許容 |

**リクエスト例（優先度変更）**:

```json
{
  "priority": "urgent"
}
```

```json
{
  "priority_id": 4
}
```

**リクエスト例（期日変更）**:

```json
{
  "due_date": "2026-03-13"
}
```

**リクエスト例（優先度と期日を同時変更）**:

```json
{
  "priority": "high",
  "due_date": "2026-03-20"
}
```

**レスポンス（成功 200 OK）**:

```json
{
  "data": {
    "id": "123",
    "title": "設計書作成",
    "status": "in_progress",
    "status_name": "進行中",
    "priority": "urgent",
    "priority_name": "緊急",
    "priority_id": 4,
    "assignee": {
      "id": "1",
      "name": "山田 太郎"
    },
    "due_date": "2026-03-13",
    "updated_at": "2026-03-03T15:30:00+09:00",
    "warnings": []
  }
}
```

**`warnings` フィールド**: 警告が存在する場合（例: 過去の期日）に配列でメッセージを返す。エラーではなく警告として処理する。

```json
{
  "data": {
    "id": "123",
    "due_date": "2026-02-01",
    "warnings": [
      "指定された期日（2026-02-01）は過去の日付です。"
    ]
  }
}
```

---

### 3.2 GET `/api/v1/tasks`（FEAT-004利用仕様）

**概要**: Redmineのタスク一覧を取得する。FEAT-004では `get_priority_report` ツールが内部で `status=open` フィルターを使って未完了タスクを全件取得するために使用する。フロントエンドのタスク一覧画面（SCR-004）からも使用する共用エンドポイント。

**HTTPメソッド**: GET

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 | デフォルト |
|---|---|---|---|---|
| `status` | string | 任意 | ステータスフィルター | `open`（未完了のみ） |
| `priority` | string | 任意 | 優先度フィルター | なし（全優先度） |
| `assignee` | string | 任意 | 担当者フィルター（ユーザーID） | なし |
| `keyword` | string | 任意 | タイトル・説明でのキーワード検索 | なし |
| `page` | integer | 任意 | ページ番号（1始まり） | 1 |
| `per_page` | integer | 任意 | 1ページあたりの件数（最大100） | 20 |
| `sort` | string | 任意 | ソート順（`due_date`, `priority`, `updated_at`） | `updated_at` |
| `order` | string | 任意 | ソート方向（`asc`, `desc`） | `desc` |

**statusフィルターの値一覧**:

| 値 | 説明 |
|---|---|
| `open` | 未完了タスクのみ（Redmineの `status_id=open` に対応） |
| `closed` | 完了タスクのみ（Redmineの `status_id=closed` に対応） |
| `all` | 全ステータス |
| `*` | 全ステータス（`all` と同義） |

**FEAT-004での使用例**:

```http
GET /api/v1/tasks?status=open&per_page=100&page=1
GET /api/v1/tasks?status=open&per_page=100&page=2
```

`PriorityReportService._fetch_open_tasks()` は全件取得のためにページネーションを繰り返す。

**レスポンス（成功 200 OK）**:

```json
{
  "data": [
    {
      "id": "123",
      "title": "設計書作成",
      "status": "in_progress",
      "status_name": "進行中",
      "priority": "urgent",
      "priority_name": "緊急",
      "priority_id": 4,
      "assignee": {
        "id": "1",
        "name": "山田 太郎"
      },
      "due_date": "2026-03-06",
      "created_at": "2026-03-01T09:00:00+09:00",
      "updated_at": "2026-03-03T10:00:00+09:00"
    },
    {
      "id": "45",
      "title": "コードレビュー",
      "status": "open",
      "status_name": "未着手",
      "priority": "normal",
      "priority_name": "通常",
      "priority_id": 2,
      "assignee": null,
      "due_date": null,
      "created_at": "2026-02-28T09:00:00+09:00",
      "updated_at": "2026-03-01T10:00:00+09:00"
    }
  ],
  "meta": {
    "total": 15,
    "page": 1,
    "per_page": 100,
    "has_next": false
  }
}
```

**FastAPI実装スケルトン**:

```python
from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/v1", tags=["tasks"])

@router.get(
    "/tasks",
    summary="タスク一覧取得",
    response_description="タスク一覧とページネーション情報",
)
async def list_tasks(
    status: str = Query(default="open", description="ステータスフィルター"),
    priority: Optional[str] = Query(default=None, description="優先度フィルター"),
    assignee: Optional[str] = Query(default=None, description="担当者ユーザーID"),
    keyword: Optional[str] = Query(default=None, description="キーワード検索"),
    page: int = Query(default=1, ge=1, description="ページ番号"),
    per_page: int = Query(default=20, ge=1, le=100, description="1ページあたりの件数"),
    sort: str = Query(default="updated_at", description="ソートフィールド"),
    order: str = Query(default="desc", description="ソート方向（asc/desc）"),
    task_query_service: TaskQueryService = Depends(get_task_query_service),
) -> dict:
    """
    Redmineのタスク一覧を取得する。
    FEAT-004ではget_priority_reportツールが内部でstatus=openで全件取得する。
    """
    result = await task_query_service.list_tasks(
        status=status,
        priority=priority,
        assignee=assignee,
        keyword=keyword,
        page=page,
        per_page=per_page,
        sort=sort,
        order=order,
    )
    return {
        "data": result.items,
        "meta": {
            "total": result.total,
            "page": result.page,
            "per_page": result.per_page,
            "has_next": result.has_next,
        },
    }
```

---

## 4. バリデーション仕様

### 4.1 PUT `/api/v1/tasks/{id}` のFEAT-004バリデーション

| フィールド | バリデーションルール | エラーコード | エラーメッセージ |
|---|---|---|---|
| `priority` | `low`, `normal`, `high`, `urgent`, `immediate` のいずれか | `VALIDATION_ERROR` | 「無効な優先度名: {value}。有効値: low, normal, high, urgent, immediate」 |
| `priority_id` | {1, 2, 3, 4, 5} のいずれか | `VALIDATION_ERROR` | 「無効な優先度ID: {value}。有効値: 1=低, 2=通常, 3=高, 4=緊急, 5=即座に」 |
| `priority` と `priority_id` | 同時指定不可 | `VALIDATION_ERROR` | 「priorityとpriority_idは同時に指定できません」 |
| `due_date` | ISO 8601形式（YYYY-MM-DD） | `VALIDATION_ERROR` | 「期日はYYYY-MM-DD形式で指定してください」 |
| `due_date` | 存在する日付のみ（例: 2/30は不可） | `VALIDATION_ERROR` | 「存在しない日付です: {value}」 |
| `due_date`（過去の日付） | エラーにはしない（警告のみ） | N/A | レスポンスの `warnings` フィールドに「過去の日付が指定されました」を返す |

### 4.2 GET `/api/v1/tasks` のバリデーション

| パラメータ | バリデーションルール | エラーコード | エラーメッセージ |
|---|---|---|---|
| `status` | `open`, `closed`, `all`, `*` のいずれか | `VALIDATION_ERROR` | 「無効なステータス値: {value}」 |
| `priority` | `low`, `normal`, `high`, `urgent`, `immediate` または数値 | `VALIDATION_ERROR` | 「無効な優先度フィルター: {value}」 |
| `page` | 1以上の整数 | `VALIDATION_ERROR` | 「ページ番号は1以上の整数で指定してください」 |
| `per_page` | 1〜100の整数 | `VALIDATION_ERROR` | 「per_pageは1〜100の範囲で指定してください」 |
| `sort` | `due_date`, `priority`, `updated_at`, `created_at` のいずれか | `VALIDATION_ERROR` | 「無効なソートフィールド: {value}」 |
| `order` | `asc`, `desc` のいずれか | `VALIDATION_ERROR` | 「無効なソート方向。有効値: asc, desc」 |

### 4.3 優先度ID・名称の対応表（FEAT-004）

| priority_id | priority（名称コード） | 表示名（日本語） |
|---|---|---|
| 1 | `low` | 低 |
| 2 | `normal` | 通常 |
| 3 | `high` | 高 |
| 4 | `urgent` | 緊急 |
| 5 | `immediate` | 即座に |

---

## 5. SSEストリーミング仕様（FEAT-004対応追加）

### 5.1 FEAT-004のtool_call・tool_resultイベント

**update_task_priority の tool_call イベント**:

```
data: {"type": "tool_call", "tool_call_id": "toolu_03", "tool": "update_task_priority", "input": {"issue_id": 123, "priority_id": 4}}

```

**update_task_priority の tool_result イベント（成功）**:

```
data: {"type": "tool_result", "tool_call_id": "toolu_03", "tool": "update_task_priority", "output": "{\"issue_id\": 123, \"title\": \"設計書作成\", \"new_priority\": \"緊急\", \"new_priority_id\": 4, \"redmine_url\": \"http://localhost:8080/issues/123\"}", "success": true}

```

**update_task_due_date の tool_call イベント**:

```
data: {"type": "tool_call", "tool_call_id": "toolu_04", "tool": "update_task_due_date", "input": {"issue_id": 123, "due_date": "2026-03-13"}}

```

**update_task_due_date の tool_result イベント（成功）**:

```
data: {"type": "tool_result", "tool_call_id": "toolu_04", "tool": "update_task_due_date", "output": "{\"issue_id\": 123, \"title\": \"設計書作成\", \"new_due_date_iso\": \"2026-03-13\", \"new_due_date_display\": \"2026年03月13日\", \"redmine_url\": \"http://localhost:8080/issues/123\"}", "success": true}

```

**get_priority_report の tool_call イベント**:

```
data: {"type": "tool_call", "tool_call_id": "toolu_05", "tool": "get_priority_report", "input": {"as_of": null}}

```

**get_priority_report の tool_result イベント（成功）**:

```
data: {"type": "tool_result", "tool_call_id": "toolu_05", "tool": "get_priority_report", "output": "## 優先タスクレポート（2026年03月03日時点）\n未完了タスク数: 8件\n...", "success": true}

```

### 5.2 ストリーミングシナリオ例

**シナリオ: 「今日何をすればいい？」**

```
data: {"type": "message_start", "message_id": "msg_xyz789"}

data: {"type": "tool_call", "tool_call_id": "toolu_05", "tool": "get_priority_report", "input": {"as_of": null}}

data: {"type": "tool_result", "tool_call_id": "toolu_05", "tool": "get_priority_report", "output": "## 優先タスクレポート...", "success": true}

data: {"type": "content_delta", "delta": "今日は以下の順で対応することをお勧めします：\n\n"}

data: {"type": "content_delta", "delta": "## 優先タスクレポート（2026年03月03日時点）\n"}

data: {"type": "content_delta", "delta": "未完了タスク数: 8件\n\n### 🚨 期限超過..."}

data: {"type": "message_end", "total_tokens": 1024}

```

---

## 6. エラーレスポンス仕様

### 6.1 FEAT-004固有のエラーコード

| エラーコード | HTTPステータス | 説明 | 例 |
|---|---|---|---|
| `VALIDATION_ERROR` | 400 | 入力バリデーション失敗 | 無効な優先度ID、不正な日付形式 |
| `NOT_FOUND` | 404 | リソース未存在 | 指定IssueIDのチケットが存在しない |
| `SERVICE_UNAVAILABLE` | 503 | 外部システム接続失敗 | Redmine接続エラー |

### 6.2 エラーレスポンス例

**バリデーションエラー（無効な優先度ID）**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "priority_id",
        "message": "無効な優先度ID: 10。有効値: 1=低, 2=通常, 3=高, 4=緊急, 5=即座に"
      }
    ]
  }
}
```

**バリデーションエラー（不正な日付形式）**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "due_date",
        "message": "期日はYYYY-MM-DD形式で指定してください（例: 2026-03-13）"
      }
    ]
  }
}
```

**成功レスポンス（過去の期日を設定した場合）**:
```json
{
  "data": {
    "id": "123",
    "due_date": "2026-02-01",
    "updated_at": "2026-03-03T15:30:00+09:00"
  },
  "warnings": [
    "指定された期日（2026-02-01）は過去の日付です。意図した設定であれば問題ありません。"
  ]
}
```

---

## 7. OpenAPIスキーマ定義

### 7.1 TaskListQueryParams スキーマ

```yaml
TaskListQueryParams:
  type: object
  properties:
    status:
      type: string
      enum: [open, closed, all, "*"]
      default: open
      description: ステータスフィルター
    priority:
      type: string
      enum: [low, normal, high, urgent, immediate]
      description: 優先度フィルター（省略時は全優先度）
    assignee:
      type: string
      description: 担当者ユーザーID（省略時は全担当者）
    keyword:
      type: string
      description: タイトル・説明でのキーワード検索
    page:
      type: integer
      minimum: 1
      default: 1
    per_page:
      type: integer
      minimum: 1
      maximum: 100
      default: 20
    sort:
      type: string
      enum: [due_date, priority, updated_at, created_at]
      default: updated_at
    order:
      type: string
      enum: [asc, desc]
      default: desc
```

### 7.2 TaskResponse スキーマ（FEAT-004拡張）

```yaml
TaskResponse:
  type: object
  properties:
    id:
      type: string
      description: Redmine Issue ID
    title:
      type: string
    status:
      type: string
      enum: [open, in_progress, closed, rejected]
    status_name:
      type: string
    priority:
      type: string
      enum: [low, normal, high, urgent, immediate]
    priority_name:
      type: string
    priority_id:
      type: integer
      enum: [1, 2, 3, 4, 5]
      description: Redmineの優先度ID
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
    created_at:
      type: string
      format: date-time
    updated_at:
      type: string
      format: date-time
  required: [id, title, status, status_name, priority, priority_name, priority_id, updated_at]
```

### 7.3 TaskListResponse スキーマ

```yaml
TaskListResponse:
  type: object
  properties:
    data:
      type: array
      items:
        $ref: "#/components/schemas/TaskResponse"
    meta:
      type: object
      properties:
        total:
          type: integer
          description: 総件数
        page:
          type: integer
        per_page:
          type: integer
        has_next:
          type: boolean
          description: 次のページが存在するか
  required: [data, meta]
```

---

## 8. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| DSD-001_FEAT-004 | TaskScheduleService・PriorityReportServiceとのAPIインターフェース（priority_id・due_dateフィールド）の整合確認 |
| DSD-005_FEAT-004 | Redmine GET /issues.json のpriority_idマッピング・due_dateフィールドの整合確認 |
| DSD-008_FEAT-004 | APIバリデーションのテストケース設計 |
| IMP-001_FEAT-004 | FastAPIルーターの実装（UpdateTaskRequest priority/due_date対応・GET /tasksルーター） |
| IT-002 | API結合テスト: GET /api/v1/tasks?status=open・PUT /api/v1/tasks/{id}（priority/due_date） の動作確認 |
