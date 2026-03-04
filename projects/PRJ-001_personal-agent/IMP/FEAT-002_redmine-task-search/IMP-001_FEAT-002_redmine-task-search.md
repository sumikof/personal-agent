# IMP-001_FEAT-002 バックエンド実装・単体テスト完了報告書（Redmineタスク検索・一覧表示）

| 項目 | 値 |
|---|---|
| ドキュメントID | IMP-001_FEAT-002 |
| バージョン | 1.0 |
| 作成日 | 2026-03-04 |
| 機能ID | FEAT-002 |
| 機能名 | Redmineタスク検索・一覧表示（redmine-task-search） |
| 入力元 | DSD-001_FEAT-002, DSD-003_FEAT-002, DSD-004_FEAT-002, DSD-008_FEAT-002 |
| ステータス | 完了 |

---

## 1. 実装概要

### 1.1 実装済み機能

| 機能 | 実装ファイル | 状態 |
|---|---|---|
| Redmine タスク検索ツール関数 | `app/agent/tools/search_tasks_tool.py` | ✅ 完了 |
| タスク検索アプリケーションサービス | `app/application/task/task_search_service.py` | ✅ 完了 |
| タスク一覧取得 REST API エンドポイント | `app/api/v1/tasks.py` | ✅ 完了 |
| Redmine Issue 一覧取得（`list_issues`） | `app/infra/redmine/redmine_adapter.py` | ✅ 完了 |
| FastAPI エントリポイント | `app/main.py` | ✅ 完了 |

### 1.2 DSD との対応

| DSD ドキュメント | 実装内容 | 実装ファイル |
|---|---|---|
| DSD-001_FEAT-002 | バックエンド機能詳細設計 | `search_tasks_tool.py`, `task_search_service.py`, `redmine_adapter.py` |
| DSD-003_FEAT-002 | API 詳細設計（GET /api/v1/tasks） | `app/api/v1/tasks.py`, `app/main.py` |
| DSD-008_FEAT-002 | 単体テスト設計（TDD 起点） | `tests/agent/tools/test_search_tasks_tool.py`, `tests/application/task/test_task_search_service.py`, `tests/infra/redmine/test_redmine_adapter_list.py`, `tests/api/v1/test_tasks_api.py` |

---

## 2. 実装詳細

### 2.1 `app/agent/tools/search_tasks_tool.py`

LangGraph エージェントに登録する `search_tasks_tool` ツール関数を実装。

- `@tool` デコレータで LangChain ツールとして定義
- 引数: `status`, `due_date`, `keyword`, `project_id`, `limit`
- `TaskSearchService` を経由して Redmine タスクを検索
- 結果を `_format_markdown_list` で Markdown 形式に変換
- エラー時は例外を上げず、エラーメッセージ文字列を返す（LLM へのフォールバック）
- `limit` は最大 100 件にクランプ

### 2.2 `app/application/task/task_search_service.py`

タスク検索のユースケースを実装するアプリケーションサービス。

- `search_tasks()`: ステータス・期日・キーワード・プロジェクト ID・件数でフィルタ
- `_build_redmine_params()`: 内部パラメータ → Redmine API パラメータへの変換
  - `status="open"` → `status_id="open"`
  - `status="all"` → `status_id="*"`
  - `limit` は最大 100 件にクランプ
- `_format_task()`: Redmine Issue → 内部辞書形式への変換（URL 生成含む）

### 2.3 `app/infra/redmine/redmine_adapter.py`（`list_issues` メソッド追加）

Redmine REST API の `GET /issues.json` を呼び出すメソッドを追加。

- 引数: `status_id`, `limit`, `offset`, `due_date`, `subject_like`, `project_id`
- 既存の `_retry_request` を使用（最大 3 回リトライ）
- 5xx エラー発生時は `RedmineConnectionError` を raise（FEAT-002 で動作を統一）

**注意**: 5xx エラーを `RedmineConnectionError` として扱う変更により、FEAT-001 の既存テスト `test_create_issue_server_error_retries_three_times` を `RedmineAPIError → RedmineConnectionError` に更新した。

### 2.4 `app/api/v1/tasks.py`

`GET /api/v1/tasks` REST エンドポイントを実装。

- クエリパラメータ: `status` (open/closed/all), `due_date`, `keyword`, `project_id`, `page`, `per_page`
- `status` パターンバリデーション（FastAPI Query パラメータ）
- ページネーション: `page`, `per_page` → offset 計算 → `pagination` レスポンスフィールド
- エラーハンドリング:
  - `RedmineConnectionError` → HTTP 503
  - `RedmineAuthError` → HTTP 503
  - その他 → HTTP 500

### 2.5 `app/main.py`

FastAPI アプリケーションのエントリポイント。

- `chat_router`（`/api/v1/conversations`）を登録
- `tasks_router`（`/api/v1/tasks`）を登録

---

## 3. TDD テストコード・テスト結果

### 3.1 テストファイル一覧

| テストファイル | テスト対象 | テスト数 |
|---|---|---|
| `tests/agent/tools/test_search_tasks_tool.py` | `search_tasks_tool`, `_format_markdown_list` | 9件 |
| `tests/application/task/test_task_search_service.py` | `TaskSearchService` | 11件 |
| `tests/infra/redmine/test_redmine_adapter_list.py` | `RedmineAdapter.list_issues` | 8件 |
| `tests/api/v1/test_tasks_api.py` | `GET /api/v1/tasks` | 5件 |

### 3.2 テスト実行結果

```
============================= test session starts ==============================
platform linux -- Python 3.11.14, pytest-9.0.2
collected 280 items

280 passed in 16.44s
```

**全テスト PASS**（プロジェクト全体 280 件中 280 件成功）

### 3.3 カバレッジ

| モジュール | カバレッジ |
|---|---|
| `app/agent/tools/search_tasks_tool.py` | 96% |
| `app/application/task/task_search_service.py` | 100% |
| `app/infra/redmine/redmine_adapter.py` | 95% |
| `app/api/v1/tasks.py` | 90% |
| `app/main.py` | 100% |
| **全体** | **82%** |

---

## 4. 設計差異一覧

| # | 設計書 | 設計内容 | 実装内容 | 差異理由 |
|---|---|---|---|---|
| 1 | DSD-001_FEAT-002 | `structlog` を使用 | `logging` を使用 | 既存コードベースとの一貫性（プロジェクト全体で `logging` を使用） |
| 2 | DSD-001_FEAT-002 | `_format_markdown_list` に `immediate` 優先度なし | `immediate` 優先度を追加 | `PRIORITY_ID_TO_NAME` に `5: "immediate"` が定義されているため対応 |
| 3 | DSD-008_FEAT-002 | `tests/unit/test_redmine_adapter.py::TestCreateIssueRetry` が `RedmineAPIError` を期待 | `RedmineConnectionError` に更新 | FEAT-002 で `_retry_request` の 5xx エラー処理を `RedmineConnectionError` に変更したため |

---

## 5. 既知の制限事項

| # | 内容 | 対応方針 |
|---|---|---|
| 1 | `GET /api/v1/tasks`（FEAT-002）と FEAT-006 のダッシュボード API が同じパスで異なるスキーマを持つ | FEAT-006 の統合時にエンドポイント仕様を統一する（IT フェーズで対応） |
| 2 | `search_tasks_tool` はエージェントグラフ（`app/agent/workflow.py`）への登録が未実施 | IT フェーズでエージェント統合テストを実施する |

---

## 6. 関連ドキュメント

- DSD-001_FEAT-002_redmine-task-search.md
- DSD-003_FEAT-002_redmine-task-search.md
- DSD-008_FEAT-002_redmine-task-search.md
- IMP-005_tdd-defect-list.md
