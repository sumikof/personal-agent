# BSD-007 外部インターフェース基本設計書

| 項目 | 内容 |
|---|---|
| ドキュメントID | BSD-007 |
| バージョン | 1.1 |
| 作成日 | 2026-03-03 |
| 更新日 | 2026-03-03 |
| 入力元 | REQ-007 |
| ステータス | レビュー修正済（REV-001 ISS-003対応） |
| プロジェクト | PRJ-001 personal-agent |

---

## 1. 外部インターフェース設計方針

### 1.1 対象外部システム

personal-agent が連携する外部システムは以下の2つである:

1. **Redmine**: タスク管理システム。MCP（Model Context Protocol）を介して連携する
2. **Anthropic Claude API**: LLM 推論・エージェント実行基盤。HTTPS 経由で直接連携する

### 1.2 共通方針

- タイムアウト設定: 接続タイムアウト 10秒・読み取りタイムアウト 60秒（エージェント実行は長時間になる場合があるため長めに設定）
- リトライ方針: 接続エラー・5xx エラー時に最大3回リトライ（1回目: 1秒後・2回目: 2秒後・3回目: 4秒後の指数バックオフ）
- サーキットブレーカー: 採用（将来的に実装。初期フェーズはリトライ上限で代替。要確認）
- エラー通知: 外部システム接続が3回のリトライ後もすべて失敗した場合、ログ記録 + ユーザーへのエラーメッセージ表示

---

## 2. 外部システム一覧

| 外部システムID | システム名 | 役割 | 通信方向 | プロトコル |
|---|---|---|---|---|
| EXT-001 | Redmine | タスク（Issue）管理。タスクの CRUD・ステータス管理 | 双方向（送信: タスク操作・受信: タスクデータ） | HTTPS / REST（MCP 経由） |
| EXT-002 | Anthropic Claude API | LLM 推論・自然言語理解・エージェント思考 | 送信（リクエスト）・受信（推論結果） | HTTPS / REST |

---

## 3. 外部インターフェース詳細

### 3.1 EXT-001: Redmine

**概要**: タスク管理システム。本システムは MCP（Model Context Protocol）を介してエージェントが Redmine の Issue を操作する。Redmine REST API を MCP ツールとしてラップし、エージェントが自然言語の指示から適切なタスク操作を実行できるようにする。

**提供元/提供先**: Redmine サーバー（ユーザーが別途セットアップ）

**通信方向**: 双方向（本システム → Redmine: タスク操作リクエスト / Redmine → 本システム: タスクデータ）

**接続情報:**

| 項目 | 内容 |
|---|---|
| エンドポイント | `${REDMINE_URL}`（環境変数で設定）例: `http://redmine.example.com` |
| プロトコル | HTTPS（HTTP も許容するが本番環境では HTTPS 必須） |
| 認証方式 | API キー（`X-Redmine-API-Key` ヘッダー）。値は `${REDMINE_API_KEY}` 環境変数 |
| データフォーマット | JSON |
| 文字コード | UTF-8 |

**インターフェース一覧（MCP ツールとして実装）:**

| No. | MCP ツール名 | Redmine API エンドポイント | 概要 | タイムアウト |
|---|---|---|---|---|
| 1 | `list_issues` | GET `/issues.json` | タスク（Issue）一覧取得。フィルタ・ページネーション対応 | 30秒 |
| 2 | `get_issue` | GET `/issues/{id}.json` | タスク詳細取得 | 15秒 |
| 3 | `create_issue` | POST `/issues.json` | 新規タスク作成 | 30秒 |
| 4 | `update_issue` | PUT `/issues/{id}.json` | タスク更新（ステータス・内容・担当者等） | 30秒 |
| 5 | `delete_issue` | DELETE `/issues/{id}.json` | タスク削除 ⚠️ **このツールはエージェントから直接呼び出してはならない（BR-02準拠）。Redmine Web UI からの手動操作専用** | 15秒 |
| 6 | `list_projects` | GET `/projects.json` | プロジェクト一覧取得 | 15秒 |
| 7 | `list_users` | GET `/users.json` | ユーザー一覧取得（担当者候補） | 15秒 |

**データフォーマット概要（リクエスト - タスク作成）:**
```json
{
  "issue": {
    "project_id": 1,
    "subject": "タスクタイトル",
    "description": "タスクの説明",
    "priority_id": 2,
    "status_id": 1,
    "assigned_to_id": 3,
    "due_date": "2026-03-31"
  }
}
```

**データフォーマット概要（レスポンス - タスク詳細）:**
```json
{
  "issue": {
    "id": 123,
    "project": { "id": 1, "name": "プロジェクト名" },
    "subject": "タスクタイトル",
    "description": "タスクの説明",
    "status": { "id": 2, "name": "進行中" },
    "priority": { "id": 2, "name": "通常" },
    "assigned_to": { "id": 3, "name": "山田 太郎" },
    "due_date": "2026-03-31",
    "created_on": "2026-03-01T00:00:00Z",
    "updated_on": "2026-03-03T10:00:00Z"
  }
}
```

**ACL（Anti-Corruption Layer）変換マッピング:**

| Redmine フィールド | 内部ドメインモデル | 変換ルール |
|---|---|---|
| `id`（整数） | `Task.redmine_issue_id`（文字列） | 整数→文字列変換 |
| `status.id`（整数） | `TaskStatus`（値オブジェクト） | ID→ステータス名称変換（要Redmine設定確認） |
| `priority.id`（整数） | `TaskPriority`（値オブジェクト） | ID→優先度名称変換（要Redmine設定確認） |
| `created_on`（UTC文字列） | `created_at`（TIMESTAMPTZ） | ISO 8601 パース・タイムゾーン正規化 |

**エラー処理方針:**

| エラー種別 | HTTPステータス | 対処方法 |
|---|---|---|
| 接続タイムアウト | - | リトライ（最大3回・指数バックオフ）後、`SERVICE_UNAVAILABLE` をユーザーに返す |
| 認証エラー | 401 | API キー設定エラーとして管理者に通知。ユーザーには「設定エラー」メッセージを表示 |
| リソース未存在 | 404 | `NOT_FOUND` エラーをユーザーに返す（リトライなし） |
| サーバエラー | 5xx | リトライ（最大3回）後、`SERVICE_UNAVAILABLE` をユーザーに返す |
| ビジネスエラー | 422 | エラー内容をログに記録し、Redmine のエラーメッセージをユーザーに返す |

**連携頻度・データ量:**
- 呼び出し頻度: ユーザー操作時（タスク画面表示・チャットでの指示実行時）
- 想定データ量/回: 1〜100件（一覧取得時）・1件（単一操作時）

---

### 3.2 EXT-002: Anthropic Claude API

**概要**: LangGraph エージェントの推論・判断エンジンとなる LLM（大規模言語モデル）。ユーザーの自然言語入力を解釈し、適切なアクション（ツール呼び出し）を選択する。会話のコンテキスト管理・テキスト生成も担う。

**提供元/提供先**: Anthropic（外部 SaaS）
**通信方向**: 送信（プロンプト・会話履歴） → 受信（推論結果・ツール呼び出し指示・生成テキスト）

**接続情報:**

| 項目 | 内容 |
|---|---|
| エンドポイント | `https://api.anthropic.com/v1/messages` |
| プロトコル | HTTPS / REST |
| 認証方式 | API キー（`x-api-key` ヘッダー）。値は `${ANTHROPIC_API_KEY}` 環境変数 |
| データフォーマット | JSON |
| 文字コード | UTF-8 |

**インターフェース一覧:**

| No. | メソッド | エンドポイント | 概要 | タイムアウト |
|---|---|---|---|---|
| 1 | POST | `/v1/messages` | テキスト生成・ツール呼び出し（非ストリーミング） | 60秒 |
| 2 | POST | `/v1/messages`（stream=true） | テキスト生成ストリーミング（SSE 形式） | 120秒（接続維持） |

**使用モデル:**
- 推奨: `claude-sonnet-4-6`（現在の標準モデル）
- 代替: `claude-opus-4-6`（高精度が必要な場合。要確認：コスト増）

**データフォーマット概要（リクエスト）:**
```json
{
  "model": "claude-sonnet-4-6",
  "max_tokens": 4096,
  "system": "あなたはパーソナルエージェントです...",
  "messages": [
    { "role": "user", "content": "タスクを作成してください" },
    { "role": "assistant", "content": "..." }
  ],
  "tools": [
    {
      "name": "create_issue",
      "description": "Redmine にタスクを作成します",
      "input_schema": {
        "type": "object",
        "properties": {
          "title": { "type": "string" },
          "description": { "type": "string" }
        },
        "required": ["title"]
      }
    }
  ]
}
```

**データフォーマット概要（レスポンス）:**
```json
{
  "id": "msg_xxx",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "タスクを作成します。"
    },
    {
      "type": "tool_use",
      "id": "toolu_xxx",
      "name": "create_issue",
      "input": { "title": "新規タスク", "description": "..." }
    }
  ],
  "stop_reason": "tool_use",
  "usage": {
    "input_tokens": 512,
    "output_tokens": 128
  }
}
```

**エラー処理方針:**

| エラー種別 | HTTPステータス | 対処方法 |
|---|---|---|
| 接続タイムアウト | - | リトライ（最大3回）後、ユーザーに「処理に失敗しました」を表示 |
| 認証エラー | 401 | API キー設定エラーとして管理者に通知 |
| レート制限 | 429 | 指数バックオフで待機後リトライ（最大3回）|
| サーバエラー | 5xx | リトライ（最大3回）後、ユーザーにエラー通知 |
| コンテンツポリシー違反 | 400（type: invalid_request_error） | ユーザーに「この内容は処理できません」メッセージを表示 |

**連携頻度・データ量:**
- 呼び出し頻度: ユーザーがチャットでメッセージを送信するたびに呼び出す（1ターンにつき1回以上）
- 想定データ量/回: 入力 1,000〜8,000 トークン・出力 100〜4,096 トークン（要確認：使用状況に依存）
- コスト管理: `agent_executions.checkpoint_data` にトークン使用量を記録し、使用量を追跡する（要確認：コスト上限アラートは将来実装）

---

## 4. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| DSD-005 | Redmine MCP アダプター・Anthropic API クライアントの詳細実装仕様（全パラメータ・エラーハンドリング・変換ルール） |
| DSD-001 | FastAPI バックエンドにおける外部 API 呼び出しレイヤー（インフラ層）の設計 |
| IT-001 | Redmine・Anthropic API 連携の結合テスト（モック使用）・E2E テスト |
| IMP-003 | 環境変数（REDMINE_URL・REDMINE_API_KEY・ANTHROPIC_API_KEY）の設定手順 |
