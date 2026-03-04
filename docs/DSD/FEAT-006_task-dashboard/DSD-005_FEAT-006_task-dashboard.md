# DSD-005_FEAT-006 外部インターフェース詳細設計書（タスク一覧ダッシュボード）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-005_FEAT-006 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-006 |
| 機能名 | タスク一覧ダッシュボード（task-dashboard） |
| 入力元 | BSD-007, BSD-005, REQ-005（UC-009） |
| ステータス | 初版 |

---

## 目次

1. 外部インターフェース概要
2. Redmine REST API仕様
3. ページネーション処理
4. タイムアウト・リトライ仕様
5. データマッピング仕様
6. エラーハンドリング
7. テスト・モック方針
8. 後続フェーズへの影響

---

## 1. 外部インターフェース概要

### 1.1 連携先システム

| 項目 | 値 |
|---|---|
| 連携先システム名 | Redmine |
| 接続方式 | HTTP REST API（JSON形式） |
| 接続先URL | `${REDMINE_URL}/issues.json`（環境変数 `REDMINE_URL`、デフォルト: `http://localhost:8080`） |
| 認証方式 | `X-Redmine-API-Key` HTTPヘッダー（環境変数 `REDMINE_API_KEY`） |
| タイムアウト | 30秒（環境変数 `REDMINE_TIMEOUT_SECONDS`） |
| リトライ | 最大3回（指数バックオフ: 1秒 → 2秒 → 4秒） |

### 1.2 利用するAPIエンドポイント

FEAT-006（タスク一覧ダッシュボード）では、Redmineの以下のAPIエンドポイントを使用する。

| エンドポイント | HTTPメソッド | 用途 |
|---|---|---|
| `/issues.json` | GET | タスク（Issue）一覧取得 |

---

## 2. Redmine REST API仕様

### 2.1 GET `/issues.json` — Issue（タスク）一覧取得

**概要**: Redmineに登録されたIssue（チケット）の一覧を取得する。FEAT-006では全ステータスのIssueを取得する。

**接続先**: `${REDMINE_URL}/issues.json`

**HTTPメソッド**: GET

**リクエストヘッダー:**

| ヘッダー名 | 値 | 必須 | 説明 |
|---|---|---|---|
| `X-Redmine-API-Key` | `${REDMINE_API_KEY}` | ○ | Redmine APIキー（環境変数から取得） |
| `Content-Type` | `application/json` | ○ | コンテンツタイプ |
| `Accept` | `application/json` | ○ | レスポンス形式指定 |

**クエリパラメータ:**

| パラメータ名 | 型 | 必須 | 値 | 説明 |
|---|---|---|---|---|
| `status_id` | string | ○ | `*` | 全ステータスのIssueを取得する。`"*"` を指定することでオープン・クローズ両方のIssueを取得する |
| `limit` | integer | ○ | `100` | 1リクエストで取得する最大件数（Redmine APIの最大値は100） |
| `offset` | integer | ○ | `0`, `100`, `200`, ... | 取得開始位置（ページネーション用） |
| `project_id` | string | × | - | プロジェクトIDでフィルタ（省略時は全プロジェクト） |
| `sort` | string | × | `updated_on:desc` | ソート条件（未指定の場合はRedmine側のデフォルト順） |

**実際のリクエスト例:**

```
GET http://localhost:8080/issues.json?status_id=*&limit=100&offset=0
X-Redmine-API-Key: {REDMINE_API_KEY}
Content-Type: application/json
Accept: application/json
```

**レスポンス形式（成功 200 OK）:**

```json
{
  "issues": [
    {
      "id": 123,
      "project": {
        "id": 1,
        "name": "personal-agent"
      },
      "tracker": {
        "id": 1,
        "name": "Bug"
      },
      "status": {
        "id": 2,
        "name": "In Progress"
      },
      "priority": {
        "id": 3,
        "name": "High"
      },
      "author": {
        "id": 1,
        "name": "管理者"
      },
      "assigned_to": {
        "id": 1,
        "name": "山田 太郎"
      },
      "subject": "API基本設計書の作成",
      "description": "バックエンドAPIの基本設計書を作成する",
      "start_date": "2026-03-01",
      "due_date": "2026-03-06",
      "done_ratio": 30,
      "is_private": false,
      "estimated_hours": null,
      "created_on": "2026-03-01T09:00:00Z",
      "updated_on": "2026-03-03T10:30:00Z",
      "closed_on": null
    },
    {
      "id": 124,
      "project": {
        "id": 1,
        "name": "personal-agent"
      },
      "tracker": {
        "id": 2,
        "name": "Feature"
      },
      "status": {
        "id": 1,
        "name": "New"
      },
      "priority": {
        "id": 2,
        "name": "Normal"
      },
      "author": {
        "id": 1,
        "name": "管理者"
      },
      "assigned_to": null,
      "subject": "データベース設計",
      "description": "",
      "start_date": null,
      "due_date": null,
      "done_ratio": 0,
      "is_private": false,
      "estimated_hours": null,
      "created_on": "2026-03-02T14:00:00Z",
      "updated_on": "2026-03-03T09:00:00Z",
      "closed_on": null
    }
  ],
  "total_count": 15,
  "offset": 0,
  "limit": 100
}
```

**レスポンスフィールド仕様:**

| フィールド | 型 | 説明 | FEAT-006での利用 |
|---|---|---|---|
| `issues` | array | Issueオブジェクトの配列 | 全件処理 |
| `total_count` | integer | フィルタ条件に一致するIssueの総件数 | ページネーション制御に使用 |
| `offset` | integer | 取得開始位置 | ページネーション確認に使用 |
| `limit` | integer | 1ページあたりの件数 | ページネーション確認に使用 |

**Issueオブジェクトのフィールド仕様（FEAT-006で使用するフィールドのみ）:**

| フィールド | 型 | FEAT-006での利用 | TaskSummaryへの変換 |
|---|---|---|---|
| `id` | integer | ○ | `id` そのまま |
| `subject` | string | ○ | `title` にマッピング |
| `status.name` | string | ○ | `status`（コード変換）・`status_label`（日本語変換） |
| `priority.name` | string | ○ | `priority`（コード変換）・`priority_label`（日本語変換） |
| `assigned_to` | object \| null | ○ | `assignee_name`（null許容） |
| `assigned_to.name` | string | ○ | `assignee_name` にマッピング |
| `due_date` | "YYYY-MM-DD" \| null | ○ | `due_date` そのまま・urgency算出に使用 |
| `created_on` | ISO 8601 string | ○ | `created_at` そのまま |
| `updated_on` | ISO 8601 string | ○ | `updated_at` そのまま |
| `project` | object | × | 未使用（フェーズ1では全プロジェクト対象） |
| `tracker` | object | × | 未使用 |
| `description` | string | × | 未使用（ダッシュボードでは非表示） |
| `done_ratio` | integer | × | 未使用 |
| `closed_on` | ISO 8601 \| null | × | 未使用 |

---

## 3. ページネーション処理

### 3.1 ページネーションの必要性

Redmine APIは1リクエストで最大100件のIssueを返す（`limit=100`）。Redmineのチケット総数が100件を超える場合、複数回リクエストして全件取得する必要がある。

### 3.2 ページネーション処理フロー

```mermaid
flowchart TD
    Start([開始]) --> Request1[GET /issues.json?status_id=*&limit=100&offset=0]
    Request1 --> Response1[レスポンス取得]
    Response1 --> Parse1[issues[]をall_issuesに追加]
    Parse1 --> Check{offset + limit >= total_count?}
    Check -->|Yes| End([終了])
    Check -->|No| NextOffset[offset += 100]
    NextOffset --> RequestN[GET /issues.json?status_id=*&limit=100&offset=N]
    RequestN --> ResponseN[レスポンス取得]
    ResponseN --> ParseN[issues[]をall_issuesに追加]
    ParseN --> Check
```

### 3.3 ページネーション実装コード

```python
# app/integration/mcp_client.py の _fetch_all_issues 実装

async def get_issues_all(self) -> List[dict]:
    """
    Redmineから全Issueをページネーションして取得する。
    total_countが100を超える場合は複数回リクエストを行う。

    Returns:
        全Issueのリスト

    Raises:
        RedmineConnectionError: 接続失敗（リトライ後）
        RedmineTimeoutError: タイムアウト
    """
    PAGE_SIZE = 100
    all_issues = []
    offset = 0

    # 初回リクエスト（total_countを取得するため）
    response = await self.get_issues({
        "status_id": "*",
        "limit": PAGE_SIZE,
        "offset": offset,
    })
    issues = response.get("issues", [])
    total_count = response.get("total_count", 0)
    all_issues.extend(issues)
    offset += PAGE_SIZE

    # 2ページ目以降（total_countを超えるまで繰り返し）
    while offset < total_count:
        response = await self.get_issues({
            "status_id": "*",
            "limit": PAGE_SIZE,
            "offset": offset,
        })
        issues = response.get("issues", [])
        all_issues.extend(issues)
        offset += PAGE_SIZE

    return all_issues
```

### 3.4 ページネーション処理の制限

| 項目 | 仕様 |
|---|---|
| 1リクエストの最大件数 | 100件（Redmine APIの最大値） |
| 最大総件数 | 制限なし（全件取得） |
| ページネーション時の総リクエスト数 | `ceil(total_count / 100)` 回 |
| 実用上の想定 | 個人利用のため、ほとんどの場合1リクエスト（100件以内）で完結する |

---

## 4. タイムアウト・リトライ仕様

### 4.1 タイムアウト設定

| 項目 | 値 | 環境変数 |
|---|---|---|
| 接続タイムアウト | 10秒 | `REDMINE_CONNECT_TIMEOUT_SECONDS` |
| 読み取りタイムアウト | 30秒 | `REDMINE_TIMEOUT_SECONDS` |
| 1ページ取得の最大所要時間 | 接続タイムアウト + 読み取りタイムアウト = 40秒 |

### 4.2 リトライ設定

| 項目 | 値 |
|---|---|
| 最大リトライ回数 | 3回（初回を含めず） |
| リトライバックオフ | 指数バックオフ（1秒 → 2秒 → 4秒） |
| リトライ対象エラー | `ConnectError`, `TimeoutException`, `HTTP 5xx` |
| リトライしないエラー | `HTTP 4xx`（クライアントエラー）, `HTTP 401/403`（認証エラー） |

```python
# app/integration/mcp_client.py のリトライ設定（tenacityライブラリ使用）
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

@retry(
    stop=stop_after_attempt(3),          # 最大3回（初回含む）
    wait=wait_exponential(
        multiplier=1, min=1, max=10      # 1秒 → 2秒 → 4秒
    ),
    retry=retry_if_exception_type((
        httpx.ConnectError,
        httpx.TimeoutException,
    )),
    reraise=True,                         # 最終リトライ後も例外を再raise
)
async def get_issues(self, filters: dict) -> dict:
    """Redmine GET /issues.json の呼び出し（リトライ付き）"""
    params = {k: str(v) for k, v in filters.items()}
    response = await self.http_client.get(
        f"{self.base_url}/issues.json",
        params=params,
        headers={"X-Redmine-API-Key": self.api_key},
        timeout=self.timeout,
    )
    response.raise_for_status()
    return response.json()
```

---

## 5. データマッピング仕様

### 5.1 Redmine status.name → TaskSummaryへの変換

Redmineのステータス名（英語）は環境・プロジェクト設定によって異なる可能性があるため、既知のステータス名はマッピングで変換し、未知のステータス名は英語のままとする。

| Redmine `status.name` | `status`（内部コード） | `status_label`（日本語） |
|---|---|---|
| `"New"` | `"new"` | `"新規"` |
| `"In Progress"` | `"in_progress"` | `"進行中"` |
| `"Feedback"` | `"feedback"` | `"フィードバック"` |
| `"Resolved"` | `"resolved"` | `"解決済み"` |
| `"Closed"` | `"closed"` | `"完了"` |
| `"Rejected"` | `"rejected"` | `"却下"` |
| その他（未知） | `"{name.lower().replace(' ', '_')}"` | `"{name}"` |

### 5.2 Redmine priority.name → TaskSummaryへの変換

| Redmine `priority.name` | `priority`（内部コード） | `priority_label`（日本語） |
|---|---|---|
| `"Low"` | `"low"` | `"低"` |
| `"Normal"` | `"normal"` | `"通常"` |
| `"High"` | `"high"` | `"高"` |
| `"Urgent"` | `"urgent"` | `"緊急"` |
| `"Immediate"` | `"immediate"` | `"即時"` |
| その他（未知） | `"{name.lower()}"` | `"{name}"` |

---

## 6. エラーハンドリング

### 6.1 エラー分類と対応

| エラー種別 | 条件 | 対応 |
|---|---|---|
| Redmine接続失敗 | `httpx.ConnectError` | リトライ（最大3回）後、`RedmineConnectionError`を raise |
| タイムアウト | `httpx.TimeoutException` | リトライ（最大3回）後、`RedmineTimeoutError`を raise |
| 認証エラー | HTTP 401 | リトライなし。`RedmineAuthError`を raise |
| リソース不存在 | HTTP 404 | リトライなし。`RedmineNotFoundError`を raise |
| Redmineサーバエラー | HTTP 5xx | リトライ（最大3回）後、`RedmineServerError`を raise |
| Issue JSONの不正フォーマット | キーエラー・型エラー | 該当Issueをスキップし、ログに記録 |

### 6.2 エラークラス定義

```python
# app/integration/exceptions.py

class RedmineError(Exception):
    """Redmine接続エラーの基底クラス"""
    pass

class RedmineConnectionError(RedmineError):
    """Redmineへの接続失敗（3回リトライ後）"""
    pass

class RedmineTimeoutError(RedmineError):
    """Redmineへの接続タイムアウト（3回リトライ後）"""
    pass

class RedmineAuthError(RedmineError):
    """Redmine APIキー認証エラー（HTTP 401）"""
    pass

class RedmineNotFoundError(RedmineError):
    """Redmineリソース不存在エラー（HTTP 404）"""
    pass

class RedmineServerError(RedmineError):
    """RedmineサーバエラーHTTP 5xx（3回リトライ後）"""
    pass
```

### 6.3 エラー発生時のサービス動作

| エラー | TaskDashboardServiceの動作 | フロントエンドへのレスポンス |
|---|---|---|
| `RedmineConnectionError` | エラーをraiseし、ルーターがHTTP503を返す | `503 SERVICE_UNAVAILABLE` |
| `RedmineTimeoutError` | エラーをraiseし、ルーターがHTTP503を返す | `503 SERVICE_UNAVAILABLE` |
| `RedmineAuthError` | エラーログを記録し、`503 SERVICE_UNAVAILABLE`を返す | `503 SERVICE_UNAVAILABLE` |
| Issue JSONの不正フォーマット | 該当Issueをスキップし、他のIssueの処理を継続する | `200 OK`（スキップした件数分少ない）|

---

## 7. テスト・モック方針

### 7.1 単体テストでのモック

FEAT-006の単体テスト（DSD-008_FEAT-006参照）では、`RedmineMCPClient`をモック化してRedmineへの実接続を行わない。

```python
# tests/task/test_task_dashboard_service.py での使用例

@pytest.fixture
def mock_redmine_client_success():
    """正常なIssue一覧を返すRedmineクライアントのモック"""
    client = MagicMock()
    client.get_issues = AsyncMock(return_value={
        "issues": [
            {
                "id": 1,
                "subject": "設計書作成",
                "status": {"id": 2, "name": "In Progress"},
                "priority": {"id": 3, "name": "High"},
                "assigned_to": {"id": 1, "name": "山田 太郎"},
                "due_date": "2026-03-06",
                "created_on": "2026-03-01T09:00:00Z",
                "updated_on": "2026-03-03T10:00:00Z",
            }
        ],
        "total_count": 1,
        "offset": 0,
        "limit": 100,
    })
    return client

@pytest.fixture
def mock_redmine_client_connection_error():
    """接続エラーを raise するRedmineクライアントのモック"""
    client = MagicMock()
    client.get_issues = AsyncMock(side_effect=RedmineConnectionError("接続失敗"))
    return client
```

### 7.2 結合テストでの考慮事項

IT-001_FEAT-006では、実際のRedmineインスタンス（テスト環境）に接続してAPIの動作確認を行う。テスト専用のRedmineプロジェクト・Issue を準備すること。

---

## 8. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-001_FEAT-006 | `RedmineMCPClient.get_issues()`メソッドの実装（ページネーション・リトライ含む） |
| DSD-008_FEAT-006 | `RedmineMCPClient`のモック設定パターン（本文書7.1を参照） |
| IT-001_FEAT-006 | 結合テストでの実Redmine接続確認項目（ページネーション・認証エラー） |
| OPS-001 | Redmineの起動確認手順（docker-compose up でRedmineを起動する運用手順） |
