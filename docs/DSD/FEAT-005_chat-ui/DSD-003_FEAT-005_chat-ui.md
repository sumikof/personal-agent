# DSD-003_FEAT-005 API詳細設計書（チャットUI）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-003_FEAT-005 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-005 |
| 機能名 | チャットUI（chat-ui） |
| 入力元 | BSD-005, BSD-001, REQ-005（UC-008） |
| ステータス | 初版 |

---

## 目次

1. API設計方針
2. エンドポイント一覧
3. エンドポイント詳細仕様
4. SSEイベント仕様
5. バリデーションルール
6. エラーレスポンス仕様
7. OpenAPIスキーマ概要
8. 後続フェーズへの影響

---

## 1. API設計方針

### 1.1 基本方針

BSD-005の設計方針を継承する。

| 項目 | 仕様 |
|---|---|
| アーキテクチャスタイル | REST（RESTful API） |
| ベースURL | `http://localhost:8000/api/v1` |
| APIバージョニング | URLパス方式 `/api/v1/` |
| レスポンス形式 | `application/json`（通常）/ `text/event-stream`（SSE） |
| 認証 | なし（フェーズ1: シングルユーザー・ローカル環境） |
| 文字コード | UTF-8 |
| 日時形式 | ISO 8601形式（UTC: `2026-03-03T10:00:00Z`） |

### 1.2 共通リクエストヘッダー

| ヘッダー | 値 | 必須 | 備考 |
|---|---|---|---|
| `Content-Type` | `application/json` | POST/PUT時必須 | |
| `Accept` | `text/event-stream` | SSEエンドポイント時必須 | メッセージ送信エンドポイントのみ |

### 1.3 共通レスポンス形式

**成功（単一リソース）:**
```json
{
  "data": { ... }
}
```

**成功（リスト）:**
```json
{
  "data": [ ... ],
  "meta": {
    "total": 10,
    "limit": 20,
    "offset": 0
  }
}
```

**エラー:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "content",
        "message": "メッセージは必須です"
      }
    ]
  }
}
```

---

## 2. エンドポイント一覧

| No. | HTTPメソッド | エンドポイント | 機能概要 | レスポンス形式 |
|---|---|---|---|---|
| 1 | POST | `/api/v1/conversations` | 会話新規開始 | `application/json` |
| 2 | GET | `/api/v1/conversations` | 会話一覧取得 | `application/json` |
| 3 | GET | `/api/v1/conversations/{id}` | 会話・メッセージ履歴取得 | `application/json` |
| 4 | POST | `/api/v1/conversations/{id}/messages` | メッセージ送信（エージェント実行・SSE） | `text/event-stream` |
| 5 | DELETE | `/api/v1/conversations/{id}` | 会話削除（論理削除） | `application/json` |

---

## 3. エンドポイント詳細仕様

### 3.1 POST `/api/v1/conversations` — 会話新規開始

**概要**: 新しいチャット会話セッションを作成する。会話IDを生成してDBに保存し、返却する。

**認証**: なし（フェーズ1）

#### リクエスト

**リクエストボディ:**

| フィールド | 型 | 必須 | バリデーション | 説明 |
|---|---|---|---|---|
| `title` | string \| null | × | 最大200文字 | 会話タイトル（省略時はnull。最初のメッセージから自動生成予定） |

**リクエスト例:**
```json
{}
```
または
```json
{
  "title": "Redmineタスク管理"
}
```

#### レスポンス

**成功 201 Created:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": null,
    "created_at": "2026-03-03T10:00:00Z",
    "updated_at": "2026-03-03T10:00:00Z"
  }
}
```

**レスポンスフィールド:**

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | string (UUID v4) | 会話の一意識別子 |
| `title` | string \| null | 会話タイトル |
| `created_at` | string (ISO 8601) | 作成日時（UTC） |
| `updated_at` | string (ISO 8601) | 最終更新日時（UTC） |

**エラーレスポンス:**

| HTTPステータス | エラーコード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | titleが200文字超過 |
| 500 | `INTERNAL_ERROR` | DBエラー等のサーバ内部エラー |

---

### 3.2 GET `/api/v1/conversations` — 会話一覧取得

**概要**: 作成済みの会話一覧を更新日時の降順で取得する。論理削除済みの会話は含まない。

**認証**: なし（フェーズ1）

#### リクエスト

**クエリパラメータ:**

| パラメータ | 型 | 必須 | デフォルト | バリデーション | 説明 |
|---|---|---|---|---|---|
| `limit` | integer | × | 20 | 1〜100 | 取得件数の上限 |
| `offset` | integer | × | 0 | 0以上 | 取得開始位置（ページネーション用） |

**リクエスト例:**
```
GET /api/v1/conversations?limit=20&offset=0
```

#### レスポンス

**成功 200 OK:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "Redmineタスク管理",
      "created_at": "2026-03-03T10:00:00Z",
      "updated_at": "2026-03-03T11:30:00Z",
      "message_count": 12
    }
  ],
  "meta": {
    "total": 5,
    "limit": 20,
    "offset": 0
  }
}
```

**レスポンスフィールド（data配列の各要素）:**

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | string (UUID) | 会話ID |
| `title` | string \| null | 会話タイトル |
| `created_at` | string (ISO 8601) | 作成日時 |
| `updated_at` | string (ISO 8601) | 最終更新日時（最新メッセージ送信時刻） |
| `message_count` | integer | 会話内のメッセージ数 |

**エラーレスポンス:**

| HTTPステータス | エラーコード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | limit/offsetが範囲外 |
| 500 | `INTERNAL_ERROR` | DBエラー |

---

### 3.3 GET `/api/v1/conversations/{id}` — 会話・メッセージ履歴取得

**概要**: 指定した会話IDの会話情報と、その会話に含まれる全メッセージを取得する。

**認証**: なし（フェーズ1）

#### リクエスト

**パスパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | string (UUID) | ○ | 会話ID |

**リクエスト例:**
```
GET /api/v1/conversations/550e8400-e29b-41d4-a716-446655440000
```

#### レスポンス

**成功 200 OK:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Redmineタスク管理",
    "created_at": "2026-03-03T10:00:00Z",
    "updated_at": "2026-03-03T11:30:00Z",
    "messages": [
      {
        "id": "msg-001",
        "role": "user",
        "content": "タスクを作成して",
        "tool_calls": null,
        "created_at": "2026-03-03T10:01:00Z"
      },
      {
        "id": "msg-002",
        "role": "assistant",
        "content": "タスクを作成しました。チケット#123をご確認ください。",
        "tool_calls": [
          {
            "tool_name": "create_issue",
            "tool_input": {
              "title": "新しいタスク",
              "project_id": 1
            },
            "tool_output": {
              "id": 123,
              "title": "新しいタスク",
              "url": "http://localhost:8080/issues/123"
            },
            "created_at": "2026-03-03T10:01:05Z"
          }
        ],
        "created_at": "2026-03-03T10:01:10Z"
      }
    ]
  }
}
```

**レスポンスフィールド（messagesの各要素）:**

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | string (UUID) | メッセージID |
| `role` | `"user"` \| `"assistant"` | メッセージ送信者ロール |
| `content` | string | メッセージ本文 |
| `tool_calls` | ToolCallObject[] \| null | ツール呼び出し情報（エージェントメッセージのみ） |
| `created_at` | string (ISO 8601) | メッセージ送信日時 |

**ToolCallObjectフィールド:**

| フィールド | 型 | 説明 |
|---|---|---|
| `tool_name` | string | ツール名（例: `create_issue`） |
| `tool_input` | object | ツール呼び出し入力パラメータ |
| `tool_output` | object | ツール実行結果 |
| `created_at` | string (ISO 8601) | ツール呼び出し日時 |

**エラーレスポンス:**

| HTTPステータス | エラーコード | 発生条件 |
|---|---|---|
| 404 | `NOT_FOUND` | 指定IDの会話が存在しない、または論理削除済み |
| 500 | `INTERNAL_ERROR` | DBエラー |

---

### 3.4 POST `/api/v1/conversations/{id}/messages` — メッセージ送信（SSE）

**概要**: 指定した会話にユーザーメッセージを送信し、LangGraphエージェントを実行する。応答はSSE（Server-Sent Events）形式のストリームで返す。

**認証**: なし（フェーズ1）

**重要**: このエンドポイントはSSEを使用するため、必ず `Accept: text/event-stream` ヘッダーを付与すること。

#### リクエスト

**パスパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | string (UUID) | ○ | 会話ID |

**リクエストボディ:**

| フィールド | 型 | 必須 | バリデーション | 説明 |
|---|---|---|---|---|
| `content` | string | ○ | 1文字以上・4000文字以下・空白のみ不可 | ユーザーのメッセージ本文 |

**リクエストヘッダー:**
```
Content-Type: application/json
Accept: text/event-stream
```

**リクエスト例:**
```json
{
  "content": "今日の未完了タスクを教えて"
}
```

#### レスポンス（SSEストリーム）

**レスポンスヘッダー:**
```
Content-Type: text/event-stream
Cache-Control: no-cache
X-Accel-Buffering: no
```

**SSEストリームフォーマット:**

各イベントは以下の形式で送信される。
```
data: {JSONオブジェクト}\n\n
```

ストリームの終端は以下で示す。
```
data: [DONE]\n\n
```

#### SSEイベント詳細仕様

**イベント1: message_start**

エージェント応答の開始を示す。

```
data: {"type": "message_start", "message_id": "msg-003"}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `type` | `"message_start"` | イベント種別 |
| `message_id` | string | 生成されるエージェントメッセージのID |

---

**イベント2: chunk**

エージェントの応答テキストのチャンク（断片）。複数回送信される。

```
data: {"type": "chunk", "content": "未完了タスクを確認します"}

data: {"type": "chunk", "content": "ね。"}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `type` | `"chunk"` | イベント種別 |
| `content` | string | テキストチャンク（部分的な応答テキスト） |

---

**イベント3: tool_call**

エージェントがツールを呼び出す直前に送信される。

```
data: {"type": "tool_call", "tool": "get_issues", "input": {"status_id": "open", "limit": 25}}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `type` | `"tool_call"` | イベント種別 |
| `tool` | string | ツール名（例: `create_issue`, `get_issues`） |
| `input` | object | ツール呼び出しの入力パラメータ |

---

**イベント4: tool_result**

ツールの実行結果。tool_callイベントの後に送信される。

```
data: {"type": "tool_result", "tool": "get_issues", "result": {"issues": [{"id": 1, "title": "設計書作成", "status": "In Progress"}], "total_count": 1}}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `type` | `"tool_result"` | イベント種別 |
| `tool` | string | ツール名 |
| `result` | object | ツール実行結果 |

---

**イベント5: done**

エージェント応答の完了を示す。このイベントの後に `[DONE]` が送信される。

```
data: {"type": "done", "message_id": "msg-003"}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `type` | `"done"` | イベント種別 |
| `message_id` | string | 完了したエージェントメッセージのID |

---

**イベント6: error**

エージェント実行中のエラーを示す。このイベントの後に `[DONE]` が送信される。

```
data: {"type": "error", "error": "Claude APIへの接続に失敗しました"}
```

| フィールド | 型 | 説明 |
|---|---|---|
| `type` | `"error"` | イベント種別 |
| `error` | string | エラーメッセージ（ユーザー向け） |

---

**SSEストリーム全体の例（ツール呼び出しあり）:**

```
data: {"type": "message_start", "message_id": "msg-003"}

data: {"type": "chunk", "content": "未完了タスクを確認します"}

data: {"type": "tool_call", "tool": "get_issues", "input": {"status_id": "open", "limit": 25}}

data: {"type": "tool_result", "tool": "get_issues", "result": {"issues": [{"id": 1, "title": "設計書作成"}], "total_count": 1}}

data: {"type": "chunk", "content": "現在の未完了タスクは1件です。\n\n**設計書作成**（#1）"}

data: {"type": "done", "message_id": "msg-003"}

data: [DONE]
```

**SSEストリーム全体の例（ツール呼び出しなし）:**

```
data: {"type": "message_start", "message_id": "msg-004"}

data: {"type": "chunk", "content": "はい、"}

data: {"type": "chunk", "content": "どのようにお手伝いできますか？"}

data: {"type": "done", "message_id": "msg-004"}

data: [DONE]
```

#### エラーレスポンス（SSE接続前のエラー）

| HTTPステータス | エラーコード | 発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | contentが空・4000文字超過 |
| 404 | `NOT_FOUND` | 指定IDの会話が存在しない |
| 500 | `INTERNAL_ERROR` | サーバ内部エラー |

**注意**: SSEストリーミング開始後のエラーは HTTPステータスではなく `error` イベントとして返される（SSEの仕様上、接続確立後はHTTPステータスを変更できないため）。

---

### 3.5 DELETE `/api/v1/conversations/{id}` — 会話削除

**概要**: 指定した会話を論理削除する（`deleted_at` を設定）。物理削除は行わない。

**認証**: なし（フェーズ1）

#### リクエスト

**パスパラメータ:**

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | string (UUID) | ○ | 会話ID |

**リクエスト例:**
```
DELETE /api/v1/conversations/550e8400-e29b-41d4-a716-446655440000
```

#### レスポンス

**成功 204 No Content:**
```
（レスポンスボディなし）
```

**エラーレスポンス:**

| HTTPステータス | エラーコード | 発生条件 |
|---|---|---|
| 404 | `NOT_FOUND` | 指定IDの会話が存在しない、または論理削除済み |
| 500 | `INTERNAL_ERROR` | DBエラー |

---

## 4. SSEイベント仕様まとめ

### 4.1 イベントタイプ一覧

| イベントタイプ | 送信タイミング | 必須フィールド | 任意フィールド |
|---|---|---|---|
| `message_start` | エージェント応答開始時（1回） | `type`, `message_id` | |
| `chunk` | テキストチャンク受信時（複数回） | `type`, `content` | |
| `tool_call` | ツール呼び出し開始時（ツール数分） | `type`, `tool`, `input` | |
| `tool_result` | ツール実行完了時（ツール数分） | `type`, `tool`, `result` | |
| `done` | エージェント応答完了時（1回） | `type`, `message_id` | |
| `error` | エラー発生時（1回） | `type`, `error` | |

### 4.2 SSEイベント送信順序

```
message_start
  ↓
chunk (複数回 or 0回)
  ↓
[ツール呼び出しがある場合]
  tool_call → tool_result → chunk (複数回)
  ↓
[ツール呼び出しが複数の場合は繰り返し]
  ↓
done
  ↓
[DONE]
```

### 4.3 クライアント実装ガイドライン

フロントエンド実装において、SSEストリームを受信する際の注意事項:

1. `data: ` プレフィックスを除去してからJSONパースする
2. `[DONE]` を受信したらストリームを終了する
3. `error` イベントを受信した場合はエラーメッセージをUIに表示する
4. ネットワーク切断時はユーザーに通知し、再試行を促す
5. ツール呼び出しのresultは次のtool_callイベントより前に必ず到達する

---

## 5. バリデーションルール

### 5.1 会話作成（POST /conversations）

| フィールド | ルール | エラーメッセージ |
|---|---|---|
| `title` | 最大200文字 | 「タイトルは200文字以内で入力してください」 |

### 5.2 メッセージ送信（POST /conversations/{id}/messages）

| フィールド | ルール | エラーメッセージ |
|---|---|---|
| `content` | 必須 | 「メッセージは必須です」 |
| `content` | 1文字以上（空白のみ不可） | 「メッセージを入力してください」 |
| `content` | 最大4000文字 | 「メッセージは4000文字以内で入力してください」 |

### 5.3 一覧取得（GET /conversations）

| パラメータ | ルール | エラーメッセージ |
|---|---|---|
| `limit` | 1〜100の整数 | 「limitは1〜100の範囲で指定してください」 |
| `offset` | 0以上の整数 | 「offsetは0以上の値を指定してください」 |

---

## 6. エラーレスポンス仕様

### 6.1 共通エラーコード

BSD-005の定義を継承する。FEAT-005固有のエラーコードを追記する。

| HTTPステータス | エラーコード | FEAT-005での発生条件 |
|---|---|---|
| 400 | `VALIDATION_ERROR` | content未入力・文字数超過・title文字数超過 |
| 404 | `NOT_FOUND` | 指定IDの会話が存在しない |
| 500 | `INTERNAL_ERROR` | DBエラー等のサーバ内部エラー |
| 503 | `SERVICE_UNAVAILABLE` | Claude API接続失敗（SSE接続前のみ） |

### 6.2 エラーレスポンス例

**404 NOT_FOUND:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "指定された会話が見つかりません",
    "details": []
  }
}
```

**400 VALIDATION_ERROR:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "入力値が不正です",
    "details": [
      {
        "field": "content",
        "message": "メッセージは4000文字以内で入力してください"
      }
    ]
  }
}
```

---

## 7. OpenAPIスキーマ概要

FastAPIの自動生成OpenAPI（Swagger UI）は `/docs` で提供する。主要なスキーマ定義を以下に示す。

```yaml
# OpenAPI 3.1.0 スキーマ（抜粋）
components:
  schemas:
    ConversationCreate:
      type: object
      properties:
        title:
          type: string
          maxLength: 200
          nullable: true

    ConversationResponse:
      type: object
      required: [id, created_at, updated_at]
      properties:
        id:
          type: string
          format: uuid
        title:
          type: string
          nullable: true
        created_at:
          type: string
          format: date-time
        updated_at:
          type: string
          format: date-time

    MessageCreate:
      type: object
      required: [content]
      properties:
        content:
          type: string
          minLength: 1
          maxLength: 4000

    MessageResponse:
      type: object
      required: [id, role, content, created_at]
      properties:
        id:
          type: string
          format: uuid
        role:
          type: string
          enum: [user, assistant]
        content:
          type: string
        tool_calls:
          type: array
          items:
            $ref: '#/components/schemas/ToolCallRecord'
          nullable: true
        created_at:
          type: string
          format: date-time

    ToolCallRecord:
      type: object
      properties:
        tool_name:
          type: string
        tool_input:
          type: object
        tool_output:
          type: object
        created_at:
          type: string
          format: date-time

    ErrorResponse:
      type: object
      required: [error]
      properties:
        error:
          type: object
          required: [code, message]
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
| IMP-001_FEAT-005 | FastAPI ルーター・Pydantic スキーマ実装の参照仕様 |
| IMP-002_FEAT-005 | フロントエンドAPIクライアント実装の参照仕様 |
| DSD-008_FEAT-005 | SSEストリーミングテスト・APIエンドポイントテストのケース設計 |
| IT-001_FEAT-005 | 結合テストにおけるAPIエンドポイント確認項目 |
| IT-002 | API結合テスト仕様書のエンドポイント一覧（本文書のエンドポイントを対象とする） |
