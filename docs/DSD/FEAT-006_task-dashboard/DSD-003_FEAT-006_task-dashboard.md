# DSD-003_FEAT-006 API詳細設計書（タスク一覧ダッシュボード）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-003_FEAT-006 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-006 |
| 機能名 | タスク一覧ダッシュボード（task-dashboard） |
| 入力元 | BSD-005, REQ-005（UC-009） |
| ステータス | 初版 |

---

## 目次

1. API設計方針
2. エンドポイント一覧
3. エンドポイント詳細仕様
4. レスポンスフィールド定義
5. バリデーションルール
6. エラーレスポンス仕様
7. OpenAPIスキーマ概要
8. 後続フェーズへの影響

---

## 1. API設計方針

BSD-005の設計方針を継承する。

| 項目 | 仕様 |
|---|---|
| アーキテクチャスタイル | REST（RESTful API） |
| ベースURL | `http://localhost:8000/api/v1` |
| レスポンス形式 | `application/json` |
| 認証 | なし（フェーズ1） |
| 文字コード | UTF-8 |
| 日時形式 | ISO 8601形式（Redmineのタイムゾーン設定に準拠） |

---

## 2. エンドポイント一覧

| No. | HTTPメソッド | エンドポイント | 機能概要 |
|---|---|---|---|
| 1 | GET | `/api/v1/tasks` | タスク一覧取得（urgency・status_label付き） |

---

## 3. エンドポイント詳細仕様

### 3.1 GET `/api/v1/tasks` — タスク一覧取得

**概要**: Redmineから全タスク（Issue）を取得し、urgency・status_labelを付加して返す。ダッシュボード画面のデータソースとして使用する。

**認証**: なし（フェーズ1）

**Redmine接続**: バックエンドがMCP経由でRedmine REST APIを呼び出す。フロントエンドはRedmineに直接接続しない。

#### リクエスト

**クエリパラメータ:**

| パラメータ | 型 | 必須 | デフォルト | 許容値 | 説明 |
|---|---|---|---|---|---|
| `status` | string | × | なし（全ステータス） | `new`, `in_progress`, `feedback`, `resolved`, `closed`, `rejected`, `all` | ステータスフィルタ |
| `urgency` | string | × | なし（全緊急度） | `overdue`, `high`, `medium`, `normal` | 緊急度フィルタ |

**リクエスト例:**

```
# 全タスク取得
GET /api/v1/tasks

# 進行中のタスクのみ
GET /api/v1/tasks?status=in_progress

# 期限超過のタスクのみ
GET /api/v1/tasks?urgency=overdue

# 組み合わせ（進行中 + 期日迫る）
GET /api/v1/tasks?status=in_progress&urgency=high
```

#### レスポンス

**成功 200 OK:**

```json
{
  "data": [
    {
      "id": 123,
      "title": "API基本設計書の作成",
      "status": "in_progress",
      "status_label": "進行中",
      "priority": "high",
      "priority_label": "高",
      "assignee_name": "山田 太郎",
      "due_date": "2026-03-06",
      "urgency": "high",
      "redmine_url": "http://localhost:8080/issues/123",
      "created_at": "2026-03-01T09:00:00Z",
      "updated_at": "2026-03-03T10:30:00Z"
    },
    {
      "id": 124,
      "title": "データベース設計",
      "status": "in_progress",
      "status_label": "進行中",
      "priority": "normal",
      "priority_label": "通常",
      "assignee_name": null,
      "due_date": null,
      "urgency": "normal",
      "redmine_url": "http://localhost:8080/issues/124",
      "created_at": "2026-03-02T14:00:00Z",
      "updated_at": "2026-03-03T09:00:00Z"
    },
    {
      "id": 120,
      "title": "要件定義書レビュー",
      "status": "new",
      "status_label": "新規",
      "priority": "urgent",
      "priority_label": "緊急",
      "assignee_name": "田中 花子",
      "due_date": "2026-03-01",
      "urgency": "overdue",
      "redmine_url": "http://localhost:8080/issues/120",
      "created_at": "2026-02-28T10:00:00Z",
      "updated_at": "2026-03-03T08:00:00Z"
    }
  ],
  "meta": {
    "total": 3,
    "urgency_summary": {
      "overdue": 1,
      "high": 1,
      "medium": 0,
      "normal": 1
    }
  }
}
```

---

## 4. レスポンスフィールド定義

### 4.1 data配列の各要素（TaskSummary）

| フィールド | 型 | 必須 | 説明 | 値の例 |
|---|---|---|---|---|
| `id` | integer | ○ | RedmineのIssue ID（Redmineが採番） | `123` |
| `title` | string | ○ | タスクタイトル（Redmineの subject フィールド） | `"API基本設計書の作成"` |
| `status` | string | ○ | 内部ステータスコード（snake_case） | `"in_progress"` |
| `status_label` | string | ○ | 日本語ステータス名 | `"進行中"` |
| `priority` | string | ○ | 優先度コード（小文字） | `"high"` |
| `priority_label` | string | ○ | 日本語優先度名 | `"高"` |
| `assignee_name` | string \| null | ○ | 担当者名（未設定の場合はnull） | `"山田 太郎"`, `null` |
| `due_date` | string \| null | ○ | 期日（"YYYY-MM-DD"形式。未設定はnull） | `"2026-03-06"`, `null` |
| `urgency` | string | ○ | 緊急度（期日チェックで算出） | `"overdue"`, `"high"`, `"medium"`, `"normal"` |
| `redmine_url` | string | ○ | RedmineのチケットページURL | `"http://localhost:8080/issues/123"` |
| `created_at` | string | ○ | 作成日時（Redmineの created_on、ISO 8601形式） | `"2026-03-01T09:00:00Z"` |
| `updated_at` | string | ○ | 最終更新日時（Redmineの updated_on） | `"2026-03-03T10:30:00Z"` |

### 4.2 statusフィールドの値一覧

| `status`値 | `status_label`値 | 説明 |
|---|---|---|
| `"new"` | `"新規"` | 未着手・新規登録されたタスク |
| `"in_progress"` | `"進行中"` | 作業中のタスク |
| `"feedback"` | `"フィードバック"` | フィードバック待ちのタスク |
| `"resolved"` | `"解決済み"` | 解決済みだが承認待ちのタスク |
| `"closed"` | `"完了"` | 完了・クローズされたタスク |
| `"rejected"` | `"却下"` | 却下されたタスク |

**注意**: Redmineのステータスはユーザーがカスタマイズ可能なため、上記以外のステータスが存在する場合はRedmineのステータス名（英語）をそのまま`status`に使用し、`status_label`も英語のまま返す。

### 4.3 priorityフィールドの値一覧

| `priority`値 | `priority_label`値 | 説明 |
|---|---|---|
| `"low"` | `"低"` | 低優先度 |
| `"normal"` | `"通常"` | 通常優先度（デフォルト） |
| `"high"` | `"高"` | 高優先度 |
| `"urgent"` | `"緊急"` | 緊急優先度 |
| `"immediate"` | `"即時"` | 即時対応が必要な最高優先度 |

### 4.4 urgencyフィールドの値一覧

期日（`due_date`）と今日の日付（サーバーサイドで取得）を比較して算出する。

| `urgency`値 | 算出条件 | 表示色（フロントエンド） | 説明 |
|---|---|---|---|
| `"overdue"` | `due_date < today` | 赤（Red 600） | 期限超過 |
| `"high"` | `today <= due_date <= today + 3日` | 黄橙（Amber 500） | 期日迫る（3日以内） |
| `"medium"` | `today + 4日 <= due_date <= today + 7日` | 黄（Yellow 600） | 今週中 |
| `"normal"` | `due_date > today + 7日` または `due_date == null` | グレー（Gray 500） | 通常・期日未設定 |

### 4.5 meta オブジェクト

| フィールド | 型 | 説明 |
|---|---|---|
| `total` | integer | フィルタリング後の合計件数 |
| `urgency_summary.overdue` | integer | urgency="overdue"のタスク件数 |
| `urgency_summary.high` | integer | urgency="high"のタスク件数 |
| `urgency_summary.medium` | integer | urgency="medium"のタスク件数 |
| `urgency_summary.normal` | integer | urgency="normal"のタスク件数 |

**urgency_summaryはフィルタリング後の件数ではなく、全タスクの内訳を返す。**

---

## 5. バリデーションルール

| パラメータ | ルール | エラーメッセージ |
|---|---|---|
| `status` | 許容値リスト内（new/in_progress/feedback/resolved/closed/rejected/all）または省略 | 「statusは new, in_progress, feedback, resolved, closed, rejected, all のいずれかを指定してください」 |
| `urgency` | 許容値リスト内（overdue/high/medium/normal）または省略 | 「urgencyは overdue, high, medium, normal のいずれかを指定してください」 |

---

## 6. エラーレスポンス仕様

### 6.1 エラーコード一覧（FEAT-006固有）

| HTTPステータス | エラーコード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | status/urgencyパラメータが許容値外 |
| 503 | `SERVICE_UNAVAILABLE` | Redmineへの接続失敗（3回リトライ後） |
| 500 | `INTERNAL_ERROR` | サーバ内部エラー |

### 6.2 エラーレスポンス例

**400 VALIDATION_ERROR:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "status",
        "message": "statusは new, in_progress, feedback, resolved, closed, rejected, all のいずれかを指定してください"
      }
    ]
  }
}
```

**503 SERVICE_UNAVAILABLE（Redmine接続失敗）:**
```json
{
  "error": {
    "code": "SERVICE_UNAVAILABLE",
    "message": "Redmineへの接続に失敗しました。しばらく後に再試行してください。",
    "details": []
  }
}
```

---

## 7. OpenAPIスキーマ概要

```yaml
# OpenAPI 3.1.0 スキーマ（抜粋）
/api/v1/tasks:
  get:
    summary: タスク一覧取得
    description: Redmineから全タスクを取得し、urgency・status_labelを付加して返す。
    parameters:
      - name: status
        in: query
        required: false
        schema:
          type: string
          enum: [new, in_progress, feedback, resolved, closed, rejected, all]
      - name: urgency
        in: query
        required: false
        schema:
          type: string
          enum: [overdue, high, medium, normal]
    responses:
      '200':
        description: タスク一覧取得成功
        content:
          application/json:
            schema:
              type: object
              properties:
                data:
                  type: array
                  items:
                    $ref: '#/components/schemas/TaskSummary'
                meta:
                  $ref: '#/components/schemas/TaskListMeta'
      '400':
        $ref: '#/components/responses/ValidationError'
      '503':
        $ref: '#/components/responses/ServiceUnavailable'

components:
  schemas:
    TaskSummary:
      type: object
      required: [id, title, status, status_label, priority, priority_label, urgency, redmine_url, created_at, updated_at]
      properties:
        id:
          type: integer
          description: Redmine Issue ID
          example: 123
        title:
          type: string
          description: タスクタイトル
          example: "API基本設計書の作成"
        status:
          type: string
          description: 内部ステータスコード
          enum: [new, in_progress, feedback, resolved, closed, rejected]
          example: "in_progress"
        status_label:
          type: string
          description: 日本語ステータス名
          example: "進行中"
        priority:
          type: string
          description: 優先度コード
          enum: [low, normal, high, urgent, immediate]
          example: "high"
        priority_label:
          type: string
          description: 日本語優先度名
          example: "高"
        assignee_name:
          type: string
          nullable: true
          description: 担当者名
          example: "山田 太郎"
        due_date:
          type: string
          nullable: true
          pattern: '^\d{4}-\d{2}-\d{2}$'
          description: 期日（YYYY-MM-DD形式）
          example: "2026-03-06"
        urgency:
          type: string
          enum: [overdue, high, medium, normal]
          description: 緊急度（サーバーサイドで期日から算出）
          example: "high"
        redmine_url:
          type: string
          format: uri
          description: RedmineチケットページのURL
          example: "http://localhost:8080/issues/123"
        created_at:
          type: string
          format: date-time
          description: 作成日時
        updated_at:
          type: string
          format: date-time
          description: 最終更新日時

    TaskListMeta:
      type: object
      required: [total, urgency_summary]
      properties:
        total:
          type: integer
          description: フィルタリング後の合計件数
        urgency_summary:
          type: object
          required: [overdue, high, medium, normal]
          properties:
            overdue:
              type: integer
            high:
              type: integer
            medium:
              type: integer
            normal:
              type: integer
```

---

## 8. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-001_FEAT-006 | FastAPI ルーター・Pydantic スキーマ実装の参照仕様 |
| IMP-002_FEAT-006 | フロントエンドAPIクライアント実装の参照仕様（useTasks フックのfetch URLとレスポンス型定義） |
| DSD-008_FEAT-006 | GET /api/v1/tasks のAPIテストケース設計 |
| IT-001_FEAT-006 | 結合テストにおけるAPIレスポンス確認項目（urgency・status_labelの正確性） |
| IT-002 | API結合テスト仕様書のエンドポイント一覧（GET /api/v1/tasks） |
