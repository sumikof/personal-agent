# REV-002 BSD→DSD フェーズ間レビュー報告書

| 項目 | 値 |
|---|---|
| ドキュメントID | REV-002 |
| レビュー種別 | BSD-DSD |
| 対象プロジェクト | PRJ-001 personal-agent |
| レビュー実施日 | 2026-03-04 |
| レビュアー | Senior Review Engineer |
| 入力ドキュメント | BSD-001〜BSD-007, BSD-009, DSD-007 (_common), DSD-001〜DSD-008 (FEAT-001〜FEAT-006), REQ-005 |
| 出力先 | projects/PRJ-001_personal-agent/REV/REV-002_bsd-to-dsd.md |

---

## 目次

1. レビューサマリー
2. FEAT-IDトレーサビリティマトリクス
3. BSD→DSD 整合性チェック
4. DSD 内部整合性チェック
5. 実装実現性チェック
6. 指摘事項一覧
7. 判定結果

---

## 1. レビューサマリー

### 1.1 レビュー概要

本レビューは、BSD（基本設計）フェーズの成果物（BSD-001〜BSD-007, BSD-009）と、DSDフェーズの成果物（DSD-007 共通コーディング規約 + FEAT-001〜FEAT-006の各詳細設計書）との整合性を検証し、IMPフェーズへの移行可否を判定するものである。

### 1.2 DSD成果物の網羅性確認

| FEAT-ID | DSD-001 | DSD-002 | DSD-003 | DSD-004 | DSD-005 | DSD-006 | DSD-007 | DSD-008 |
|---|---|---|---|---|---|---|---|---|
| FEAT-001 | ○ | ○ | ○ | ○ | ○ | - | (共通) | ○ |
| FEAT-002 | ○ | ○ | ○ | - | ○ | - | (共通) | ○ |
| FEAT-003 | ○ | ○ | ○ | - | ○ | - | (共通) | ○ |
| FEAT-004 | ○ | ○ | ○ | - | ○ | - | (共通) | ○ |
| FEAT-005 | ○ | ○ | ○ | ○ | - | - | (共通) | ○ |
| FEAT-006 | ○ | ○ | ○ | - | ○ | - | (共通) | ○ |
| _common | - | - | - | - | - | - | ○ | - |

**凡例**: ○=存在, -=該当なし（適用外）

**補足**: DSD-004（DB詳細設計書）はFEAT-001とFEAT-005のみ存在する。FEAT-002〜004・006はDB新規テーブルを持たないため省略が正当化される（RedmineはバックエンドのみでローカルDBには会話関連テーブルのみ保持する設計）。ただしFEAT-003の `DSD-004` が明示的に存在しない点は後述のマイナー指摘事項として記録する。

### 1.3 総合所見

DSD全体を通じて、BSデザイン設計の意図を忠実に詳細化しており、品質水準は高い。FastAPI/LangGraph/Next.js/PostgreSQLのアーキテクチャ一貫性が維持されており、SSEストリーミング設計はFEAT-001〜004間で統一されている。TDD設計書（DSD-008）は全FEATに存在し、Given-When-Thenベースのテストケースが体系的に定義されている。

一方、以下の点でIMPフェーズ開始前に確認・対処すべき事項が存在する。

- **Critical（致命的）**: 0件
- **Major（重大）**: 3件
- **Minor（軽微）**: 5件

---

## 2. FEAT-IDトレーサビリティマトリクス

### 2.1 REQ-005 → DSD トレーサビリティ

REQ-005で定義されたユースケース（UC-001〜UC-009）とFEAT-IDのDSDドキュメントの対応を検証する。

| UC-ID | ユースケース名 | FEAT-ID | DSD-001 | DSD-002 | DSD-003 | DSD-008 | 判定 |
|---|---|---|---|---|---|---|---|
| UC-001 | チャットからタスクを作成する | FEAT-001 | ○ | ○ | ○ | ○ | PASS |
| UC-002 | タスクを検索・一覧表示する | FEAT-002 | ○ | ○ | ○ | ○ | PASS |
| UC-003 | タスクのステータスを更新する | FEAT-003 | ○ | ○ | ○ | ○ | PASS |
| UC-004 | タスクに進捗コメントを追加する | FEAT-003 | ○ | ○ | ○ | ○ | PASS |
| UC-005 | タスクの優先度を変更する | FEAT-004 | ○ | ○ | ○ | ○ | PASS |
| UC-006 | タスクの期日を変更する | FEAT-004 | ○ | ○ | ○ | ○ | PASS |
| UC-007 | 優先タスクのレポートを受け取る | FEAT-004 | ○ | ○ | ○ | ○ | PASS |
| UC-008 | チャットUI基盤を利用する | FEAT-005 | ○ | ○ | ○ | ○ | PASS |
| UC-009 | タスク一覧ダッシュボードを閲覧する | FEAT-006 | ○ | ○ | ○ | ○ | PASS |

**判定: 全UC完全カバー。トレーサビリティに欠落なし。**

### 2.2 FEAT-ID別ドキュメント入力元トレーサビリティ

各DSDドキュメントの「入力元」に記載されたBSD文書参照を検証する。

| FEAT-ID | DSD文書 | 記載入力元 | 妥当性 | 摘要 |
|---|---|---|---|---|
| FEAT-001 | DSD-001 | BSD-001, BSD-002, BSD-004, BSD-009, REQ-005 | ○ | 正当 |
| FEAT-001 | DSD-002 | BSD-003, BSD-004, BSD-001 | ○ | 正当 |
| FEAT-001 | DSD-003 | BSD-005, REQ-005 | △ | BSD-007（外部IF設計書）の参照漏れ（Minor #1） |
| FEAT-001 | DSD-004 | BSD-006, BSD-009 | ○ | 正当 |
| FEAT-001 | DSD-005 | BSD-007, BSD-009 | ○ | 正当 |
| FEAT-001 | DSD-008 | DSD-001, DSD-002, DSD-003 | ○ | 正当 |
| FEAT-002 | DSD-001 | BSD-001, BSD-002, BSD-004, BSD-009, REQ-005 | ○ | 正当 |
| FEAT-002 | DSD-005 | BSD-007, BSD-009 | ○ | 正当 |
| FEAT-003 | DSD-001 | BSD-001, BSD-002, BSD-004, BSD-009, REQ-005 | ○ | 正当 |
| FEAT-003 | DSD-005 | BSD-007, BSD-009 | ○ | 正当 |
| FEAT-004 | DSD-001 | BSD-001, BSD-002, BSD-004, BSD-009, REQ-005 | ○ | 正当 |
| FEAT-004 | DSD-005 | BSD-007, BSD-009, DSD-005_FEAT-003 | ○ | FEAT-003からの継承も明示。正当 |
| FEAT-005 | DSD-001 | BSD-001, BSD-002, BSD-004, BSD-009, REQ-005 | ○ | 正当 |
| FEAT-005 | DSD-004 | BSD-006, BSD-009, REQ-005 | ○ | 正当 |
| FEAT-006 | DSD-001 | BSD-001, BSD-004, BSD-005, BSD-009, REQ-005 | △ | BSD-007参照なし（FEAT-006もRedmine外部IFあり。Minor #2） |
| FEAT-006 | DSD-005 | BSD-007, BSD-005, REQ-005 | ○ | 正当 |

---

## 3. BSD→DSD 整合性チェック

### 3.1 BSD-001（アーキテクチャ）→ DSD整合性

**BSD-001の主要設計決定事項**:
- FastAPI（バックエンド）+ Next.js App Router（フロントエンド）
- LangGraph for エージェントワークフロー
- PostgreSQL（会話・メッセージ永続化）
- MCPクライアント経由でRedmine REST API連携
- レイヤードアーキテクチャ（Presentation / Application / Domain / Infrastructure）

| 確認項目 | DSD記載内容 | 整合性 | 摘要 |
|---|---|---|---|
| FastAPI使用 | 全FEAT DSD-001/DSD-003にFastAPIルーター実装が記載 | ○ | 一貫 |
| Next.js App Router使用 | 全FEAT DSD-002にApp Routerディレクトリ構成（app/）が記載 | ○ | 一貫 |
| LangGraph使用 | FEAT-001〜005のDSD-001にLangGraphワークフロー設計が記載 | ○ | 一貫 |
| PostgreSQL使用 | DSD-004_FEAT-001, DSD-004_FEAT-005でPostgreSQL 15+を指定 | ○ | 一貫 |
| MCP経由Redmine | 全FEAT DSD-005にMCPクライアント経由の記載あり | ○ | 一貫 |
| レイヤードアーキテクチャ | 全FEAT DSD-001にPresentation/Application/Domain/Infrastructureの4層が明示 | ○ | 一貫 |
| SSEストリーミング | FEAT-001〜005のDSD-003にSSEイベント仕様が記載 | ○ | 一貫 |

**判定: BSD-001との整合性は高い。全DSD文書でアーキテクチャ設計を忠実に踏襲している。**

### 3.2 BSD-002（セキュリティ設計）→ DSD整合性

**BSD-002の主要設計決定事項**:
- APIキー管理（環境変数）
- BR-02: タスク削除禁止（エージェント経由）
- ログにAPIキー・個人情報を含めない
- フェーズ1: 認証なし（シングルユーザー・ローカル環境）

| 確認項目 | DSD記載内容 | 整合性 | 摘要 |
|---|---|---|---|
| Redmine APIキーを環境変数管理 | DSD-005_FEAT-001〜004で `REDMINE_API_KEY` 環境変数参照を明示 | ○ | 一貫 |
| BR-02タスク削除禁止 | DSD-001_FEAT-003で3層防御（ツール定義除外・システムプロンプト・サービス層検出）を設計 | ○ | 充実した実装設計あり |
| ログ内秘匿情報除外 | DSD-001/005_FEAT-003/004でAPIキー・notes内容をログ除外対象として明示 | ○ | 一貫 |
| フェーズ1認証なし | 全DSD-003でAuthを「不要（フェーズ1）」と明示 | ○ | 一貫 |
| Claude APIキー管理 | DSD-001_FEAT-001/005で `ANTHROPIC_API_KEY` 環境変数を参照 | ○ | 一貫 |

**判定: BSD-002との整合性は高い。BR-02の多層防御設計は特に評価できる。**

### 3.3 BSD-003（画面設計）→ DSD整合性

**BSD-003の主要画面定義**:
- SCR-001: ログイン画面
- SCR-002: ダッシュボード（KanbanBoard）
- SCR-003: チャット画面
- SCR-004: タスク一覧
- SCR-005: タスク詳細
- SCR-006: タスク作成フォーム
- SCR-007: タスク検索結果

| 確認項目 | DSD記載内容 | 整合性 | 摘要 |
|---|---|---|---|
| SCR-003チャット画面のコンポーネント | FEAT-001 DSD-002でChatWindow/MessageList/MessageBubble/MessageInput/AgentStatusBarを定義。FEAT-003 DSD-002ではChatContainer/ChatMessageList/ChatMessage/ChatInputを定義 | △ | コンポーネント名の差異あり（Major #1） |
| SCR-002ダッシュボードKanbanBoard | FEAT-006 DSD-002でKanbanスタイルの3カラム表示を定義 | ○ | 整合 |
| SCR-006タスク作成フォーム | FEAT-001 DSD-002にTaskCreateFormコンポーネントの設計あり | ○ | 整合 |
| SCR-007タスク検索結果 | FEAT-002 DSD-002にTaskSearchResults/TaskListコンポーネントが定義 | ○ | 整合 |

**判定: SCR-003（チャット画面）でコンポーネント名の不一致が複数FEATにまたがって発生している（後述Major #1）。**

### 3.4 BSD-004（業務フロー）→ DSD整合性

**BSD-004の主要フロー定義**:
- チャット経由タスク作成フロー
- タスク検索・表示フロー
- エージェント実行フロー（SSEストリーミング）

| 確認項目 | DSD記載内容 | 整合性 | 摘要 |
|---|---|---|---|
| エージェント実行フロー | 全FEAT DSD-001にLangGraphワークフロー（agent_node → tool_node → agent_node）のシーケンス図が記載 | ○ | 一貫したフロー設計 |
| SSEストリーミングフロー | 全FEAT DSD-003でSSEイベントシーケンスが定義 | ○ | 一貫 |
| Redmine操作フロー | FEAT-001〜004のDSD-001/005で詳細なシーケンス図が記載 | ○ | 充実 |
| 優先タスクレポートフロー | FEAT-004 DSD-001でPriorityReportServiceのソートロジック・レポートフローを設計 | ○ | BR-06の実装方針が明確 |

**判定: BSD-004との整合性は高い。**

### 3.5 BSD-005（API基本設計）→ DSD整合性

**BSD-005の主要エンドポイント**:
- POST `/api/v1/conversations/{id}/messages` (SSE)
- POST `/api/v1/conversations` (新規会話作成)
- GET `/api/v1/conversations/{id}` (会話取得)
- POST `/api/v1/tasks` (タスク作成)
- GET `/api/v1/tasks` (タスク一覧)
- PUT `/api/v1/tasks/{id}` (タスク更新)

| 確認項目 | DSD記載内容 | 整合性 | 摘要 |
|---|---|---|---|
| POST /conversations/{id}/messages | FEAT-001/003/004/005 DSD-003で詳細仕様定義済み | ○ | 一貫 |
| POST /tasks | FEAT-001 DSD-003で201 Createdレスポンスを含む詳細仕様定義済み | ○ | 整合 |
| GET /tasks | FEAT-002 DSD-003でフィルター・ページネーション付き仕様定義済み | ○ | 整合。FEAT-004でも参照 |
| PUT /tasks/{id} | FEAT-003 DSD-003で全フィールド（status/notes/priority/due_date）を定義。FEAT-004で拡張 | ○ | FEATをまたいだ段階的設計が明確 |
| POST /conversations | FEAT-005 DSD-003で新規会話作成エンドポイントが定義 | ○ | 整合 |
| GET /conversations/{id} | FEAT-005 DSD-003で会話取得エンドポイントが定義 | ○ | 整合 |
| エラーレスポンス形式 | 全FEAT DSD-003で `{"error": {"code": "...", "message": "...", "details": [...]}}` 形式を踏襲 | ○ | BSD-005準拠 |
| SSEイベント形式 | 全FEAT DSD-003でSSEイベント（message_start/content_delta/tool_call/tool_result/message_end/error）が統一 | ○ | 一貫 |

**判定: BSD-005との整合性は高い。**

### 3.6 BSD-006（データベース設計）→ DSD整合性

**BSD-006の主要テーブル**:
- conversations（UUID主キー、論理削除）
- messages（UUID主キー、role/content/token_count）
- agent_executions（LangGraph実行記録）
- agent_tool_calls（ツール呼び出し記録）

| 確認項目 | DSD記載内容 | 整合性 | 摘要 |
|---|---|---|---|
| conversationsテーブル定義 | DSD-004_FEAT-001/005でUUID主キー・論理削除(deleted_at)付きで定義 | ○ | BSD-006準拠 |
| messagesテーブル定義 | DSD-004_FEAT-001/005でrole/content/token_count等が定義 | ○ | BSD-006準拠 |
| agent_tool_callsテーブル | DSD-004_FEAT-005でtool_name/input_json/output_json/status付きで定義 | ○ | BSD-006準拠 |
| agent_executionsテーブル | DSD-004_FEAT-001にagent_executionsテーブルが定義済み | ○ | BSD-006準拠 |
| TIMESTAMPTZ使用 | DSD-004_FEAT-001/005で全日時フィールドにTIMESTAMPTZ(UTC)を使用 | ○ | BSD-006準拠 |
| SQLAlchemy非同期ORM | DSD-004_FEAT-001/005でasyncpgベースの非同期ORMモデルが設計 | ○ | BSD-001/006準拠 |
| Alembicマイグレーション | DSD-004_FEAT-001/005でAlembicマイグレーションSQLが記載 | ○ | 充実 |

**注意**: BSD-006には `agent_executions` テーブルの定義があるが、DSD-004_FEAT-005では同テーブルが定義されていない（DSD-004_FEAT-001のみに定義）。これはFEAT単位の分割設計の結果であり、IMP-004（DB初期データ・マイグレーション手順書）でFEAT間の依存順序を明示する必要がある（Minor #3）。

**判定: BSD-006との整合性は良好。**

### 3.7 BSD-007（外部インターフェース設計）→ DSD整合性

**BSD-007の主要設計事項**:
- Redmine REST API（GET /issues.json, POST /issues.json, PUT /issues/{id}.json, GET /issues/{id}.json）
- 認証: X-Redmine-API-Key ヘッダー
- タイムアウト: 接続10秒・読み取り30秒
- リトライ: 最大3回・指数バックオフ（1→2→4秒）

| 確認項目 | DSD記載内容 | 整合性 | 摘要 |
|---|---|---|---|
| X-Redmine-API-Keyヘッダー認証 | 全FEAT DSD-005で `X-Redmine-API-Key` ヘッダーを使用 | ○ | BSD-007準拠 |
| 接続タイムアウト10秒 | DSD-005_FEAT-001/003/004で接続タイムアウト10秒を明示 | ○ | BSD-007準拠 |
| 読み取りタイムアウト30秒 | DSD-005_FEAT-001/003/004で読み取りタイムアウト30秒を明示 | ○ | BSD-007準拠 |
| リトライ3回・指数バックオフ | DSD-005_FEAT-001/003/004でリトライ仕様（1→2→4秒）を明示 | ○ | BSD-007準拠 |
| ACL（Anti-Corruption Layer）パターン | DSD-005_FEAT-003/004でACLマッピング（Redmineモデル→内部ドメインモデル変換）が設計 | ○ | 充実 |
| Redmineステータスマッピング | DSD-005_FEAT-003でステータスID（1/2/3/5）と内部名称のマッピング表を定義 | △ | Redmineデフォルトステータス(id=3はResolved、id=5はClosed)と本システムマッピング(id=3=完了、id=5=却下)が不一致。Major #2 |

**判定: BSD-007との整合性は概ね良好だが、Redmineステータスマッピングに重大な不整合あり（Major #2）。**

### 3.8 BSD-009（ドメインモデル）→ DSD整合性

**BSD-009の主要設計事項**:
- CTX-001: タスク管理コンテキスト（Task, TaskStatus, TaskPriority, TaskUrgency）
- CTX-002: エージェントコンテキスト（Conversation, Message, AgentExecution, ToolCall）
- CTX-003: 認証コンテキスト（User, AccessToken, RefreshToken）
- コンテキスト間統合: ACL（Anti-Corruption Layer）パターン

| 確認項目 | DSD記載内容 | 整合性 | 摘要 |
|---|---|---|---|
| CTX-001 Taskエンティティ | DSD-001_FEAT-001/003/004でTask dataclass（redmine_issue_id, title, status, priority, assignee, due_date, updated_at）が定義 | ○ | BSD-009準拠 |
| CTX-001 TaskStatus値オブジェクト | DSD-001_FEAT-001/003/004でTaskStatus frozen dataclass（id, name）が定義 | ○ | BSD-009準拠 |
| CTX-001 TaskPriority値オブジェクト | DSD-001_FEAT-003/004でTaskPriority frozen dataclass（id, name）が定義 | ○ | BSD-009準拠 |
| CTX-002 Conversationエンティティ | DSD-004_FEAT-005でconversationsテーブル+ORMモデルが定義 | ○ | BSD-009準拠 |
| CTX-002 Messageエンティティ | DSD-004_FEAT-005でmessagesテーブル+ORMモデルが定義 | ○ | BSD-009準拠 |
| CTX-002 AgentExecutionエンティティ | DSD-004_FEAT-001でagent_executionsテーブル+ORMモデルが定義 | ○ | BSD-009準拠 |
| CTX-002 ToolCallエンティティ | DSD-004_FEAT-001/005でagent_tool_callsテーブル+ORMモデルが定義 | ○ | BSD-009準拠 |
| CTX-003認証 | フェーズ1は認証なし（DSD全文で認証不要と明示） | ○ | フェーズ1スコープとして整合 |
| コンテキスト間ACL | DSD-005_FEAT-003/004でRedmineモデル↔内部ドメインモデル変換のACLマッピングが詳細設計 | ○ | 充実 |

**注意**: DSD-001_FEAT-006ではTaskSummaryという別DTOが定義されており（`app/task/domain/models.py`）、FEAT-001〜004のTaskエンティティ（`app/domain/task/entities.py`）とパスが異なる。同一CTX-001内での二重定義となる可能性がある（Major #3）。

**判定: BSD-009との整合性は概ね良好だが、TaskエンティティとTaskSummaryの重複定義について整理が必要（Major #3）。**

---

## 4. DSD 内部整合性チェック

### 4.1 SSEイベント仕様の一貫性

全FEAT-001〜005にわたりSSEイベント仕様を確認した。

| SSEイベントタイプ | FEAT-001 | FEAT-002 | FEAT-003 | FEAT-004 | FEAT-005 | 一貫性 |
|---|---|---|---|---|---|---|
| `message_start` | ○ | ○ | ○ | ○ | ○ | 統一 |
| `content_delta` | ○ | ○ | ○ | ○ | ○ | 統一 |
| `tool_call` | ○ | ○ | ○ | ○ | ○ | 統一 |
| `tool_result` | ○ | ○ | ○ | ○ | ○ | 統一 |
| `message_end` | ○ | ○ | ○ | ○ | ○ | 統一 |
| `error` | ○ | ○ | ○ | ○ | ○ | 統一 |

**判定: SSEイベント仕様は全FEAT間で完全に一貫している。**

ただし、DSD-002_FEAT-001の `SSEEvent` TypeScript型定義と DSD-002_FEAT-003の `handleSSEEvent` 関数の `tool_call` イベントのpayloadフィールド名に微差がある:

- DSD-002_FEAT-001: `{ type: "tool_call"; tool_call_id: string; tool: string; input: Record<string, unknown> }`
- DSD-002_FEAT-003: `event.tool_call_id`, `event.tool`, `event.input`（同一フィールド）

実質的に同一であり問題なし。

### 4.2 RedmineAdapter クラスの設計一貫性

| メソッド | FEAT-001 DSD-005 | FEAT-002 DSD-005 | FEAT-003 DSD-005 | FEAT-004 DSD-005 | 一貫性 |
|---|---|---|---|---|---|
| `create_issue` | ○定義 | - | - | - | FEAT-001のみ（適切） |
| `list_issues` | ○定義 | ○定義 | - | ○拡張 | 設計継承が明確 |
| `get_issue` | ○定義 | - | ○定義 | ○継承 | 設計継承が明確 |
| `update_issue` | - | - | ○定義 | ○継承 | 設計継承が明確 |
| タイムアウト設定 | 接続10s/読取30s | 接続10s/読取30s | 接続10s/読取30s | FEAT-003継承 | 統一 |
| リトライ設定 | 3回・指数バックオフ | 3回・指数バックオフ | 3回・指数バックオフ | FEAT-003継承 | 統一 |

**問題点**: FEAT-001〜004でそれぞれ `RedmineAdapter` クラスを定義しているが、実装時に1つの `RedmineAdapter` クラスに統合する必要がある。DSD設計はFEATごとに分離されているが、実装では共有クラスとなる。これはDSDの記述方法（FEAT単位で独立記述）によるものであり設計不整合ではないが、IMP-001時の統合方針を明確にすべきである（Minor #4）。

### 4.3 フロントエンドコンポーネント命名の一貫性

| コンポーネント | DSD-002_FEAT-001 | DSD-002_FEAT-003 | DSD-002_FEAT-005 | 一貫性 |
|---|---|---|---|---|
| チャットコンテナ | `ChatWindow` | `ChatContainer` | `ChatPage` | **不一致** |
| メッセージ一覧 | `MessageList` | `ChatMessageList` | `ChatMessageList` | **不一致** |
| メッセージ表示 | `MessageBubble` | `ChatMessage` | `ChatMessage` | **不一致** |
| 入力欄 | `MessageInput` | `ChatInput` | `MessageInput` | **不一致** |
| useChathook | `useChat` | `useChat` | `useChat` | 一致 |

**コンポーネント命名の不一致は実装時の混乱を招く。IMP-002着手前に確定が必要（Major #1として後述）。**

### 4.4 タスクエンティティ定義の整合性

| エンティティ | 定義FEAT | モジュールパス | フィールド |
|---|---|---|---|
| `Task` dataclass | FEAT-001/003/004 | `app/domain/task/entities.py` | redmine_issue_id, title, status, priority, assignee, due_date, notes, updated_at |
| `TaskSummary` dataclass | FEAT-006 | `app/task/domain/models.py` | id, title, status, status_label, priority, urgency, due_date, assignee, redmine_url |
| `TaskCreateInput` | FEAT-001 | `app/domain/task/value_objects.py` | title, description, project_id, priority, due_date, assignee_id |

`Task` と `TaskSummary` はどちらもRedmine Issueを表現するが、異なるモジュールパスと異なるフィールドセットを持つ。このCTX-001内での重複はDDD上のコンテキスト分離（TaskDashboardはCTX-001の読み取り専用ビュー）として説明可能だが、設計書上で明確に説明されていない（Major #3として後述）。

### 4.5 DSD-008（TDD起点テスト設計書）の質確認

| FEAT-ID | TDD方針記載 | Given-When-Then形式 | カバレッジ目標 | フレームワーク指定 | 判定 |
|---|---|---|---|---|---|
| FEAT-001 | ○ | ○（27テストケース定義） | BE 80%+ / FE 80%+ | pytest-asyncio + Vitest | ○ |
| FEAT-002 | ○ | ○（DSD-008_FEAT-002に詳細あり） | BE 80%+ / FE 80%+ | pytest-asyncio + Vitest | ○ |
| FEAT-003 | ○ | ○（7コンポーネント対象） | BE 80%+ / FE 80%+ | pytest-asyncio + Vitest | ○ |
| FEAT-004 | ○ | ○（freezegun使用によるdatetime固定） | BE 80%+ / FE 80%+ | pytest-asyncio + Vitest | ○ |
| FEAT-005 | ○ | ○（SSEストリーミングテストを含む） | BE 80%+ / FE 80%+ | pytest-asyncio + Vitest | ○ |
| FEAT-006 | ○ | ○ | BE 80%+ / FE 80%+ | FEAT-005と同一フレームワーク | ○ |

**判定: DSD-008は全FEATで良質に設計されており、TDD起点として十分な品質を持つ。**

### 4.6 エラーハンドリングの一貫性

| エラー種別 | FEAT-001 | FEAT-003 | FEAT-004 | 一貫性 |
|---|---|---|---|---|
| Redmine接続エラー | `RedmineConnectionError` → 503 | `RedmineConnectionError` → 503 | `RedmineConnectionError` → 503 | 統一 |
| タスク未存在 | `TaskNotFoundError` → 404 | `TaskNotFoundError` → 404 | `TaskNotFoundError` → 404 | 統一 |
| バリデーションエラー | `VALIDATION_ERROR` → 400 | `VALIDATION_ERROR` → 400 | `VALIDATION_ERROR` → 400 | 統一 |
| タスク削除試行 | - | `FORBIDDEN_OPERATION` → 422 | `FORBIDDEN_OPERATION` → 422 | 統一（FEAT-003以降） |

**判定: エラーハンドリング方針は全FEAT間で高い一貫性を保っている。**

---

## 5. 実装実現性チェック

### 5.1 技術的実現可能性

| 確認項目 | 実現可否 | 摘要 |
|---|---|---|
| FastAPI + LangGraph統合 | ○ | 実績あるパターン。DSD-001_FEAT-005でToolRegistryによる統合設計が明確 |
| LangGraph + Claude API | ○ | Anthropic公式サポート。`langchain-anthropic` ライブラリ経由 |
| FastAPI + SSEストリーミング | ○ | `StreamingResponse` + `AsyncGenerator` で実現可能。DSD-003_FEAT-001/005に実装例あり |
| Next.js + SSE受信 | ○ | Fetch API + ReadableStream で実現可能。DSD-002_FEAT-003に詳細実装設計あり |
| SQLAlchemy非同期 + PostgreSQL | ○ | asyncpg + SQLAlchemy 2.x で実現可能 |
| Alembicマイグレーション | ○ | 標準的パターン。DSD-004_FEAT-001/005にDDLが完全定義 |
| pytest + pytest-asyncio | ○ | 標準的。DSD-008_FEAT-001〜006でフレームワーク指定 |
| respx（httpxモック） | ○ | pytest-httpxまたはrespxどちらも利用可能 |
| Vitest + React Testing Library | ○ | Next.jsプロジェクトでの標準的テストスタック |
| MSW（Mock Service Worker） | ○ | APIモックの標準的手段 |

**判定: 全技術要素について実現可能性に問題なし。**

### 5.2 パフォーマンス観点の懸念

| 確認項目 | 懸念度 | 摘要 |
|---|---|---|
| タスク更新前のGET確認（2回のHTTPリクエスト） | 低 | DSD-005_FEAT-003でPUT後にGETで最新状態取得する設計。ローカル環境では許容範囲内 |
| 優先タスクレポート（全タスク取得） | 低〜中 | DSD-001_FEAT-004でRedmineから全未完了タスクを取得してソート。タスク数が多い場合に遅延の可能性あり。REQ-006の非機能要件（3秒以内）を担保できるか監視が必要 |
| FEAT-006ダッシュボード30秒ポーリング | 低 | ローカル環境での個人利用であれば問題なし |
| LangGraph + SSEのメモリ管理 | 低 | FEAT-005 DSD-001でConversation集約のライフサイクル管理が設計 |

### 5.3 Redmineステータスマッピングの実装リスク

DSD-005_FEAT-003で以下の注意書きがある:
> 「実際のRedmine環境のステータス設定は `GET /issue_statuses.json` で確認し、環境変数またはコンフィグファイルでマッピングを設定すること」

この注意書きが存在するにもかかわらず、DSD-001_FEAT-003のTaskStatus値オブジェクトではstatus_idが `{1, 2, 3, 5}` とハードコードされている。Redmineのデフォルトでは id=3 は "Resolved"（解決済み）であり id=5 が "Closed"（完了）である。本システムでは id=3 を「完了」id=5 を「却下」として扱っており、Redmineデフォルト環境との不一致がある。これは **Major #2** として記録する。

---

## 6. 指摘事項一覧

### Critical（致命的）: 0件

Critical指摘事項なし。

---

### Major（重大）: 3件

#### ISSUE-M01: チャット画面コンポーネント命名の不一致
- **重大度**: Major
- **対象ドキュメント**: DSD-002_FEAT-001, DSD-002_FEAT-003, DSD-002_FEAT-005
- **内容**: チャット画面の主要コンポーネント（ChatWindow/ChatContainer/ChatPage、MessageList/ChatMessageList等）の命名がFEAT間で統一されていない。IMP-002を複数FEATが並行して実装する際に、同一コンポーネントを重複実装または矛盾する実装を行うリスクがある。
- **影響**: IMP-002_FEAT-001/003/005での実装衝突リスク
- **対応指示**: IMP着手前に、チャットUIコンポーネントの正式命名を DSD-007（コーディング規約）またはDSD-002_FEAT-005（FEAT-005がチャットUIの主機能担当）に一元的に定義し、他FEATのDSD-002を参照方式に変更すること。具体的には以下の名称を確定させること:
  - チャットコンテナ: `ChatPage` または `ChatContainer`（どちらか1つ）
  - メッセージ一覧: `ChatMessageList` または `MessageList`
  - 個別メッセージ: `ChatMessage` または `MessageBubble`
  - 入力欄: `ChatInput` または `MessageInput`

#### ISSUE-M02: Redmineステータスマッピングのハードコード問題
- **重大度**: Major
- **対象ドキュメント**: DSD-001_FEAT-003（TaskStatus値オブジェクト）、DSD-005_FEAT-003
- **内容**: 本システムの内部ステータスID（1=未着手, 2=進行中, 3=完了, 5=却下）が、Redmineのデフォルトステータス（id=3=Resolved, id=4=Feedback, id=5=Closed, id=6=Rejected）と一致しない。DSD-005_FEAT-003では「環境変数またはコンフィグファイルで設定すること」と注記しているが、DSD-001_FEAT-003のTaskStatus値オブジェクトでは `VALID_STATUS_IDS = {1, 2, 3, 5}` とハードコードされており、設定方式が矛盾している。
- **影響**: 実際のRedmine環境でステータス更新が動作しないリスク
- **対応指示**: 以下のいずれかの方針を選択し、関連DSD文書を更新すること:
  1. （推奨）環境変数 `REDMINE_STATUS_MAP_OPEN=1`, `REDMINE_STATUS_MAP_IN_PROGRESS=2`, `REDMINE_STATUS_MAP_CLOSED=3`, `REDMINE_STATUS_MAP_REJECTED=5` などで外部設定可能にし、TaskStatusをconfigurable設計に変更する
  2. Redmineデフォルトの `GET /issue_statuses.json` を起動時に1回取得して動的マッピングする方式に変更する

  選択した方針をDSD-001_FEAT-003（TaskStatus）、DSD-003_FEAT-003（UpdateTaskRequest）、DSD-005_FEAT-003（RedmineAdapter）に反映すること。

#### ISSUE-M03: FEAT-006のTaskSummaryとFEAT-001〜004のTaskエンティティの関係未定義
- **重大度**: Major
- **対象ドキュメント**: DSD-001_FEAT-001/003/004（Task dataclass）、DSD-001_FEAT-006（TaskSummary dataclass）
- **内容**: FEAT-001〜004では `app/domain/task/entities.py` に `Task` エンティティを定義しているが、FEAT-006では `app/task/domain/models.py` に `TaskSummary` を定義している。両者はRedmine Issueを表現するが異なるパスに存在し、CTX-001内での役割分担が設計書上で説明されていない。
- **影響**: 実装時の二重定義またはどちらを使うべきかの混乱
- **対応指示**: DSD-001_FEAT-006（または共通ドキュメント）に以下を明記すること:
  - `Task`: CTX-001の主エンティティ。FEAT-001〜005でのエージェント操作用（読み書き両用）
  - `TaskSummary`: CTX-001の読み取り専用ビューオブジェクト（DTO）。FEAT-006のダッシュボード表示専用
  - あるいは `Task` に urgency/status_label/redmine_url フィールドを追加してFEAT-006でも使用する方針

---

### Minor（軽微）: 5件

#### ISSUE-m01: DSD-003_FEAT-001の入力元にBSD-007が未記載
- **重大度**: Minor
- **対象ドキュメント**: DSD-003_FEAT-001（API詳細設計書）
- **内容**: DSD-003_FEAT-001の入力元は `BSD-005, REQ-005` のみで、外部インターフェース仕様の根拠となるBSD-007が記載されていない。
- **対応指示**: DSD-003_FEAT-001のヘッダー「入力元」に `BSD-007` を追記すること。

#### ISSUE-m02: DSD-001_FEAT-006の入力元にBSD-007が未記載
- **重大度**: Minor
- **対象ドキュメント**: DSD-001_FEAT-006（バックエンド機能詳細設計書）
- **内容**: DSD-001_FEAT-006の入力元は `BSD-001, BSD-004, BSD-005, BSD-009, REQ-005` で、FEAT-006もRedmine外部IFを使用するが `BSD-007` が記載されていない。DSD-005_FEAT-006では `BSD-007` を参照しているため不整合がある。
- **対応指示**: DSD-001_FEAT-006のヘッダー「入力元」に `BSD-007` を追記すること。

#### ISSUE-m03: FEAT-001〜005のマイグレーション実行順序未定義
- **重大度**: Minor
- **対象ドキュメント**: DSD-004_FEAT-001、DSD-004_FEAT-005
- **内容**: DSD-004_FEAT-001でconversations/messages/agent_executionsテーブルが定義され、DSD-004_FEAT-005でも同テーブルが再定義されている（重複）。IMP-004（DBマイグレーション手順書）作成時にどちらのマイグレーションを先に実行するかが明確でない。
- **対応指示**: IMP-004またはDSD-004のいずれかに「マイグレーションはFEAT-001 → FEAT-005の順に実行すること」または「FEAT-005 DSD-004がマスタ定義であり、FEAT-001 DSD-004の定義を廃止する」旨を明記すること。

#### ISSUE-m04: RedmineAdapterの実装ファイルパスがFEATによって異なる
- **重大度**: Minor
- **対象ドキュメント**: DSD-001_FEAT-001/003/004、DSD-005_FEAT-001/003/004
- **内容**: 各FEATで `RedmineAdapter` の実装パスが異なっている（例: `app/infrastructure/redmine/redmine_adapter.py`）。実装時は1つのクラスに統合されるはずだが、DSD上では明示的に「共有クラス」であることが書かれていない。
- **対応指示**: DSD-007（コーディング規約）または共通ガイドラインに、`RedmineAdapter` は単一の共有クラスとして実装することを明記すること。具体的なパスは `app/infrastructure/redmine/adapter.py` として確定させること。

#### ISSUE-m05: DSD-004_FEAT-005でagent_executionsテーブルが未定義
- **重大度**: Minor
- **対象ドキュメント**: DSD-004_FEAT-005（データベース詳細設計書）
- **内容**: BSD-006で定義されている `agent_executions` テーブルが DSD-004_FEAT-005 には含まれておらず、DSD-004_FEAT-001にのみ存在する。FEAT-005がチャットUIの主担当FEATであるため、agent_executionsテーブルの定義も本書に含めるべきかどうかが不明確。
- **対応指示**: DSD-004_FEAT-005に「agent_executionsテーブルはDSD-004_FEAT-001で定義済みのため本書では省略する」旨を明記すること。または、agent_executionsテーブルの定義をDSD-004_FEAT-005に移動し、DSD-004_FEAT-001から参照する方式に変更すること。

---

## 7. 判定結果

### 7.1 判定

```
判定: CONDITIONAL PASS（条件付き合格）
```

### 7.2 判定根拠

全体として、DSDフェーズの成果物はBSDフェーズの設計意図を高い精度で詳細化しており、技術スタックの一貫性・SSEストリーミング設計の統一性・TDD設計書の質のいずれも十分な水準にある。Critical指摘事項はゼロであり、実装フェーズへの移行は概ね可能な状態にある。

ただし、以下の3件のMajor指摘事項については、IMP-002（フロントエンド実装）およびIMP-001（バックエンド実装）の着手前に対処することを条件とする。

### 7.3 次フェーズ移行条件

**以下の条件をすべて満たした後、IMPフェーズへ移行すること。**

| 条件 | 対象指摘 | 対応期限 |
|---|---|---|
| チャット画面コンポーネント命名を全FEAT間で統一し、DSD-002_FEAT-001/003/005を更新すること | ISSUE-M01 | IMP-002_FEAT-001/003/005着手前 |
| Redmineステータスマッピング方式を選択・確定し、DSD-001/003/005_FEAT-003を更新すること | ISSUE-M02 | IMP-001_FEAT-003着手前 |
| TaskとTaskSummaryの役割分担をDSDに明記すること | ISSUE-M03 | IMP-001_FEAT-006着手前 |

Minor指摘事項（ISSUE-m01〜m05）は、対応可能なものから順次対処することを推奨するが、IMP移行の必須条件としない。

### 7.4 承認

| 項目 | 内容 |
|---|---|
| レビュー完了日 | 2026-03-04 |
| 判定 | CONDITIONAL PASS |
| 条件付き承認事項 | ISSUE-M01, ISSUE-M02, ISSUE-M03の解決（IMP着手前） |
| 次フェーズ | IMP（実装・TDD）— 上記条件解決後に開始可能 |
