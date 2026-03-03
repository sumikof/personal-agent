# BSD-005 API基本設計書

| 項目 | 内容 |
|---|---|
| ドキュメントID | BSD-005 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 入力元 | REQ-003, REQ-005, REQ-007 |
| ステータス | 初版 |
| プロジェクト | PRJ-001 personal-agent |

---

## 1. API設計方針

### 1.1 アーキテクチャスタイル

- アーキテクチャスタイル: REST（RESTful API）
- APIバージョニング方針: URL パス方式 `/api/v1/`（バージョンアップ時は `/api/v2/` を新設し、旧バージョンは一定期間並行運用する）
- ベースURL: `https://{ドメイン}/api/v1`
- ドキュメント: FastAPI の自動生成 OpenAPI（Swagger UI）を `/docs` で提供する
- ストリーミング: エージェント実行レスポンスは Server-Sent Events（SSE）または WebSocket で返す

### 1.2 共通仕様

**リクエストヘッダー:**

| ヘッダー | 説明 | 必須 |
|---|---|---|
| `Content-Type` | `application/json` | ○（POST/PUT/PATCH 時） |
| `Authorization` | `Bearer {access_token}` | ○（認証必須エンドポイント） |
| `Accept` | `application/json` または `text/event-stream`（SSE 時） | - |

**レスポンス形式（成功）:**
```json
{
  "data": { ... },
  "meta": {
    "total": 100,
    "page": 1,
    "per_page": 20
  }
}
```

**レスポンス形式（エラー）:**
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

**共通エラーコード:**

| HTTPステータス | エラーコード | 説明 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | バリデーションエラー（必須項目未入力・形式不正） |
| 401 | `UNAUTHORIZED` | 認証エラー（トークン未提供・無効・期限切れ） |
| 403 | `FORBIDDEN` | 権限エラー（ロール不足・他ユーザーリソースへのアクセス） |
| 404 | `NOT_FOUND` | リソース未存在 |
| 409 | `CONFLICT` | 競合エラー（重複登録等） |
| 422 | `UNPROCESSABLE_ENTITY` | ビジネスロジックエラー |
| 429 | `RATE_LIMIT_EXCEEDED` | レート制限超過 |
| 500 | `INTERNAL_ERROR` | サーバ内部エラー |
| 503 | `SERVICE_UNAVAILABLE` | 外部システム（Redmine/Claude API）接続エラー |

---

## 2. エンドポイント一覧

| No. | HTTPメソッド | エンドポイント | 機能概要 | 認証要否 | 関連コンテキスト |
|---|---|---|---|---|---|
| 1 | POST | `/api/v1/auth/login` | ログイン（JWT発行） | 不要 | CTX-003 |
| 2 | POST | `/api/v1/auth/logout` | ログアウト（トークン無効化） | 要 | CTX-003 |
| 3 | POST | `/api/v1/auth/refresh` | アクセストークン更新 | 不要（リフレッシュトークン必要） | CTX-003 |
| 4 | GET | `/api/v1/users/me` | ログインユーザー情報取得 | 要 | CTX-003 |
| 5 | PUT | `/api/v1/users/me` | ログインユーザー情報更新 | 要 | CTX-003 |
| 6 | GET | `/api/v1/tasks` | タスク一覧取得 | 要 | CTX-001 |
| 7 | POST | `/api/v1/tasks` | タスク作成 | 要 | CTX-001 |
| 8 | GET | `/api/v1/tasks/{id}` | タスク詳細取得 | 要 | CTX-001 |
| 9 | PUT | `/api/v1/tasks/{id}` | タスク更新 | 要 | CTX-001 |
| 10 | DELETE | `/api/v1/tasks/{id}` | タスク削除 | 要 | CTX-001 |
| 11 | GET | `/api/v1/conversations` | 会話一覧取得 | 要 | CTX-002 |
| 12 | POST | `/api/v1/conversations` | 新規会話開始 | 要 | CTX-002 |
| 13 | GET | `/api/v1/conversations/{id}` | 会話詳細・メッセージ履歴取得 | 要 | CTX-002 |
| 14 | POST | `/api/v1/conversations/{id}/messages` | メッセージ送信（エージェント実行） | 要 | CTX-002 |
| 15 | DELETE | `/api/v1/conversations/{id}` | 会話削除 | 要 | CTX-002 |
| 16 | GET | `/api/v1/health` | ヘルスチェック | 不要 | システム |

---

## 3. エンドポイント詳細

### 1. POST `/api/v1/auth/login`

**概要**: メールアドレスとパスワードによるログイン認証を行い、JWT アクセストークンとリフレッシュトークンを発行する
**認証**: 不要
**権限**: なし

**リクエスト:**

| パラメータ | 種別 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `email` | リクエストボディ | string | ○ | ユーザーのメールアドレス |
| `password` | リクエストボディ | string | ○ | パスワード（平文）|

**リクエスト例:**
```json
{
  "email": "user@example.com",
  "password": "secret_password"
}
```

**レスポンス（成功 200）:**
```json
{
  "data": {
    "access_token": "eyJhbGci...",
    "refresh_token": "eyJhbGci...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**エラーレスポンス:**

| ステータス | コード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | メールアドレス形式不正・必須項目未入力 |
| 401 | `UNAUTHORIZED` | パスワード不一致 |
| 403 | `FORBIDDEN` | アカウントロック中 |

---

### 6. GET `/api/v1/tasks`

**概要**: Redmine のタスク（Issue）一覧を取得する。フィルタリングとページネーションに対応する
**認証**: 要
**権限**: user 以上

**リクエスト:**

| パラメータ | 種別 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `status` | クエリパラメータ | string | × | タスクステータス（`open`/`closed`/`all`）デフォルト: `open` |
| `priority` | クエリパラメータ | string | × | 優先度（`low`/`normal`/`high`/`urgent`） |
| `assignee` | クエリパラメータ | string | × | 担当者ユーザーID |
| `keyword` | クエリパラメータ | string | × | タイトル・説明での全文検索キーワード |
| `page` | クエリパラメータ | integer | × | ページ番号（デフォルト: 1） |
| `per_page` | クエリパラメータ | integer | × | 1ページあたりの件数（デフォルト: 20・最大: 100） |

**レスポンス（成功 200）:**
```json
{
  "data": [
    {
      "id": "123",
      "title": "タスクタイトル",
      "description": "タスクの説明",
      "status": "open",
      "priority": "high",
      "assignee": {
        "id": "1",
        "name": "山田 太郎"
      },
      "due_date": "2026-03-31",
      "created_at": "2026-03-01T09:00:00+09:00",
      "updated_at": "2026-03-03T10:00:00+09:00"
    }
  ],
  "meta": {
    "total": 45,
    "page": 1,
    "per_page": 20
  }
}
```

---

### 7. POST `/api/v1/tasks`

**概要**: 新規タスクを作成して Redmine に登録する
**認証**: 要
**権限**: user 以上

**リクエスト:**

| パラメータ | 種別 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `title` | リクエストボディ | string | ○ | タスクタイトル（最大200文字） |
| `description` | リクエストボディ | string | × | タスク説明 |
| `priority` | リクエストボディ | string | × | 優先度（`low`/`normal`/`high`/`urgent`）デフォルト: `normal` |
| `assignee_id` | リクエストボディ | string | × | 担当者ユーザーID |
| `due_date` | リクエストボディ | string | × | 期日（ISO 8601 形式: `YYYY-MM-DD`） |

**レスポンス（成功 201）:**
```json
{
  "data": {
    "id": "124",
    "title": "新規タスク",
    "status": "open",
    "priority": "normal",
    "created_at": "2026-03-03T10:00:00+09:00"
  }
}
```

**エラーレスポンス:**

| ステータス | コード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | タイトル未入力・200文字超過 |
| 503 | `SERVICE_UNAVAILABLE` | Redmine への接続失敗 |

---

### 8. GET `/api/v1/tasks/{id}`

**概要**: 指定した ID のタスク詳細を取得する
**認証**: 要
**権限**: user 以上

**リクエスト:**

| パラメータ | 種別 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `id` | パスパラメータ | string | ○ | Redmine Issue ID |

**エラーレスポンス:**

| ステータス | コード | 発生条件 |
|---|---|---|
| 404 | `NOT_FOUND` | 指定 ID のタスクが存在しない |

---

### 9. PUT `/api/v1/tasks/{id}`

**概要**: 指定したタスクの情報を更新する（タイトル・説明・ステータス・優先度・担当者・期日）
**認証**: 要
**権限**: user 以上

**リクエスト:**

| パラメータ | 種別 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `id` | パスパラメータ | string | ○ | Redmine Issue ID |
| `title` | リクエストボディ | string | × | タスクタイトル |
| `description` | リクエストボディ | string | × | タスク説明 |
| `status` | リクエストボディ | string | × | ステータス |
| `priority` | リクエストボディ | string | × | 優先度 |
| `assignee_id` | リクエストボディ | string | × | 担当者ユーザーID |
| `due_date` | リクエストボディ | string | × | 期日（`YYYY-MM-DD`） |

---

### 14. POST `/api/v1/conversations/{id}/messages`

**概要**: 指定した会話にメッセージを送信し、LangGraph エージェントを実行する。応答はストリーミング（SSE）で返す
**認証**: 要
**権限**: user 以上

**リクエスト:**

| パラメータ | 種別 | 型 | 必須 | 説明 |
|---|---|---|---|---|
| `id` | パスパラメータ | string | ○ | 会話 ID |
| `content` | リクエストボディ | string | ○ | ユーザーメッセージ（最大4000文字） |

**リクエストヘッダー（SSE 利用時）:**
```
Accept: text/event-stream
```

**レスポンス（SSE ストリーム）:**
```
data: {"type": "message_start", "message_id": "msg_xxx"}

data: {"type": "content_delta", "delta": "タスクを"}

data: {"type": "content_delta", "delta": "作成します..."}

data: {"type": "tool_call", "tool": "create_issue", "input": {...}}

data: {"type": "tool_result", "tool": "create_issue", "output": {...}}

data: {"type": "message_end", "total_tokens": 1024}
```

**エラーレスポンス:**

| ステータス | コード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | メッセージ未入力・4000文字超過 |
| 404 | `NOT_FOUND` | 指定 ID の会話が存在しない |
| 503 | `SERVICE_UNAVAILABLE` | Claude API / Redmine への接続失敗 |

---

### 16. GET `/api/v1/health`

**概要**: システムのヘルスチェック。ロードバランサ・監視システムからの死活監視に使用する
**認証**: 不要

**レスポンス（成功 200）:**
```json
{
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "services": {
      "database": "healthy",
      "redis": "healthy",
      "redmine": "healthy",
      "anthropic": "healthy"
    },
    "timestamp": "2026-03-03T10:00:00+09:00"
  }
}
```

---

## 4. 外部API連携

| 外部システム | エンドポイント | 用途 | 認証方式 |
|---|---|---|---|
| Redmine API | `{REDMINE_URL}/issues.json` 等 | タスク（Issue）CRUD 操作 | APIキー（`X-Redmine-API-Key` ヘッダー） |
| Anthropic Claude API | `https://api.anthropic.com/v1/messages` | LLM 推論・エージェント実行 | APIキー（`x-api-key` ヘッダー） |

> 詳細は BSD-007（外部インターフェース基本設計書）を参照。

---

## 5. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| DSD-003 | 各エンドポイントの詳細仕様（全パラメータ・バリデーションルール・OpenAPI スキーマ定義） |
| DSD-001 | FastAPI ルーター・依存性注入・ミドルウェアの実装設計 |
| IT-002 | API 結合テストの確認対象エンドポイント一覧 |
