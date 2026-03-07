# DSD-005_FEAT-004 外部インターフェース詳細設計書（タスク優先度・スケジュール調整）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-005_FEAT-004 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-004 |
| 機能名 | タスク優先度・スケジュール調整 |
| 入力元 | BSD-007, BSD-009, DSD-005_FEAT-003 |
| ステータス | 初版 |

---

## 目次

1. 外部インターフェース概要
2. Redmine REST API仕様（優先度・期日更新）
3. Redmine REST API仕様（Issue一覧取得）
4. Redmine優先度マスタ
5. Redmineデータフォーマット詳細
6. RedmineAdapter 実装仕様（FEAT-004拡張）
7. ACL変換マッピング
8. リトライ・タイムアウト設計
9. エラーハンドリング
10. 後続フェーズへの影響

---

## 1. 外部インターフェース概要

### 1.1 対象外部システム

| 外部システムID | システム名 | 役割 |
|---|---|---|
| EXT-001 | Redmine | タスク（Issue）管理システム。MCPクライアント経由でREST APIを呼び出す |

FEAT-004では FEAT-003 で設計した `GET /issues/{id}.json`・`PUT /issues/{id}.json` に加え、**未完了タスク一覧取得**のための `GET /issues.json` エンドポイントを使用する。

### 1.2 FEAT-004で使用するRedmine APIエンドポイント

| No. | メソッド | エンドポイント | 用途 | MCP ツール名 |
|---|---|---|---|---|
| 1 | GET | `/issues/{id}.json` | Issue存在確認・現在の状態取得（FEAT-003と共用） | `get_issue` |
| 2 | PUT | `/issues/{id}.json` | Issue更新（優先度・期日変更）（FEAT-003拡張） | `update_issue` |
| 3 | GET | `/issues.json` | 未完了Issue一覧取得（FEAT-004新規） | `list_issues` |
| 4 | GET | `/enumerations/priorities.json` | 優先度マスタ取得（初期化時に1回） | N/A（直接呼び出し） |

### 1.3 接続情報

FEAT-003と同一の接続情報を使用する。

| 項目 | 値 |
|---|---|
| ベースURL | `${REDMINE_URL}`（環境変数）例: `http://localhost:8080` |
| プロトコル | HTTP（ローカル環境）/ HTTPS（本番環境） |
| 認証方式 | `X-Redmine-API-Key` ヘッダー（環境変数 `REDMINE_API_KEY`） |
| データ形式 | JSON（`Content-Type: application/json`） |
| 文字コード | UTF-8 |
| 接続タイムアウト | 10秒 |
| 読み取りタイムアウト | 30秒 |

### 1.4 FEAT-003との差分

| 項目 | FEAT-003 | FEAT-004 |
|---|---|---|
| PUT `/issues/{id}.json` | `status_id`・`notes` フィールドを使用 | `priority_id`・`due_date` フィールドを追加使用 |
| GET `/issues.json` | 未使用 | 新規使用（優先タスクレポート用） |
| `list_issues` MCPツール | 未使用 | 新規使用 |

---

## 2. Redmine REST API仕様（優先度・期日更新）

### 2.1 PUT `/issues/{id}.json`（優先度・期日変更）

FEAT-004で追加するフィールドを使用した PUT API の仕様を記述する。FEAT-003の `GET /issues/{id}.json` の仕様はそのまま踏襲する。

**HTTPメソッド**: PUT

**URLパラメータ**:

| パラメータ | 型 | 必須 | 説明 |
|---|---|---|---|
| `id` | integer | 必須 | Redmine Issue ID |

**リクエストヘッダー**:

```http
PUT /issues/123.json HTTP/1.1
Host: localhost:8080
X-Redmine-API-Key: {REDMINE_API_KEY}
Content-Type: application/json
```

**リクエストボディ（優先度変更）**:

```json
{
  "issue": {
    "priority_id": 4
  }
}
```

**リクエストボディ（期日変更）**:

```json
{
  "issue": {
    "due_date": "2026-03-14"
  }
}
```

**リクエストボディ（優先度 + 期日 + コメント 複合変更）**:

```json
{
  "issue": {
    "priority_id": 3,
    "due_date": "2026-03-14",
    "notes": "優先度と期日を見直しました。"
  }
}
```

**FEAT-004で使用するリクエストボディフィールド一覧**:

| フィールド | 型 | 必須 | 説明 | FEAT-004での使用 |
|---|---|---|---|---|
| `priority_id` | integer | 任意 | 優先度ID（1〜5） | 使用（UC-005） |
| `due_date` | string | 任意 | 期日（YYYY-MM-DD形式）。`null` を指定すると期日をクリア | 使用（UC-006） |
| `notes` | string | 任意 | コメント追加（Journalとして記録） | 任意使用 |
| `status_id` | integer | 任意 | ステータスID | 未使用（FEAT-003で使用） |

**FEAT-004での`due_date`の特記事項**:

- `due_date` は `"YYYY-MM-DD"` 形式の文字列として送信する
- 期日クリア（削除）の場合は `null` を送信する: `{"issue": {"due_date": null}}`
- Redmineは `due_date` が `start_date` より前の場合、`422 Unprocessable Entity` を返す場合がある
- 過去の日付（本日より前）の設定はRedmineサーバー側では拒否されない（警告のみ）

**レスポンス（成功）**:

Redmine REST APIのPUT `/issues/{id}.json` は成功時に **HTTP 204 No Content** または **HTTP 200 OK** を返す（Redmineのバージョンにより異なる）。

- **HTTP 204 No Content**: レスポンスボディなし（多くのRedmineバージョンで採用）
- **HTTP 200 OK**: 更新後のIssue情報を返す場合もある

**実装上の注意**: 更新後の状態を取得するため、PUT呼び出し後に `GET /issues/{id}.json` を呼び出して最新状態を取得する。

**エラーレスポンス**:

| HTTPステータス | 発生条件 | 対処 |
|---|---|---|
| 404 Not Found | 指定IDのIssueが存在しない | `TaskNotFoundError` を発生させる |
| 401 Unauthorized | APIキーが無効 | 設定エラーとしてログに記録 |
| 403 Forbidden | 更新権限なし | アクセス拒否エラーとしてユーザーに通知 |
| 422 Unprocessable Entity | バリデーションエラー（期日形式不正・start_date>due_date 等） | エラー内容をユーザーに返す |
| 500 Internal Server Error | Redmineサーバーエラー | リトライ後にエラーをユーザーに通知 |

---

## 3. Redmine REST API仕様（Issue一覧取得）

### 3.1 GET `/issues.json`（未完了Issue一覧取得）

**目的**: 優先タスクレポート（UC-007）のために、未完了タスクの一覧を取得する。ページネーション付きで全件取得する。

**HTTPメソッド**: GET

**クエリパラメータ**:

| パラメータ | 型 | 必須 | 説明 | FEAT-004での使用値 |
|---|---|---|---|---|
| `status_id` | string \| integer | 任意 | フィルタ。`open`=未完了、`closed`=完了、`*`=全件 | `"open"` |
| `limit` | integer | 任意 | 1回のリクエストで返す最大件数（デフォルト25、最大100） | `100` |
| `offset` | integer | 任意 | 取得開始位置（ページネーション用） | `0`, `100`, `200`, ... |
| `sort` | string | 任意 | ソート条件（例: `due_date:asc`） | 未使用（アプリ側でソート） |
| `project_id` | integer \| string | 任意 | プロジェクトIDまたは識別子でフィルタ | 未使用（全プロジェクト対象） |
| `assigned_to_id` | integer | 任意 | 担当者IDでフィルタ（`me`=自分） | 未使用 |

**リクエスト例（未完了タスク全件、ページ1）**:

```http
GET /issues.json?status_id=open&limit=100&offset=0 HTTP/1.1
Host: localhost:8080
X-Redmine-API-Key: {REDMINE_API_KEY}
Content-Type: application/json
```

**リクエスト例（ページ2、offset=100）**:

```http
GET /issues.json?status_id=open&limit=100&offset=100 HTTP/1.1
Host: localhost:8080
X-Redmine-API-Key: {REDMINE_API_KEY}
Content-Type: application/json
```

**レスポンス（成功 200 OK）**:

```json
{
  "issues": [
    {
      "id": 123,
      "project": {
        "id": 1,
        "name": "パーソナルエージェント開発"
      },
      "tracker": {
        "id": 1,
        "name": "機能"
      },
      "status": {
        "id": 2,
        "name": "進行中"
      },
      "priority": {
        "id": 3,
        "name": "高"
      },
      "author": {
        "id": 1,
        "name": "山田 太郎"
      },
      "assigned_to": {
        "id": 1,
        "name": "山田 太郎"
      },
      "subject": "設計書作成",
      "description": "システム設計書を作成する",
      "start_date": "2026-03-01",
      "due_date": "2026-03-10",
      "done_ratio": 60,
      "is_private": false,
      "estimated_hours": null,
      "created_on": "2026-03-01T09:00:00Z",
      "updated_on": "2026-03-03T10:00:00Z",
      "closed_on": null
    },
    {
      "id": 124,
      "project": { "id": 1, "name": "パーソナルエージェント開発" },
      "tracker": { "id": 2, "name": "バグ" },
      "status": { "id": 1, "name": "未着手" },
      "priority": { "id": 4, "name": "緊急" },
      "author": { "id": 1, "name": "山田 太郎" },
      "assigned_to": null,
      "subject": "認証バグ修正",
      "description": "",
      "start_date": null,
      "due_date": null,
      "done_ratio": 0,
      "is_private": false,
      "estimated_hours": null,
      "created_on": "2026-03-02T11:00:00Z",
      "updated_on": "2026-03-02T11:00:00Z",
      "closed_on": null
    }
  ],
  "total_count": 47,
  "offset": 0,
  "limit": 100
}
```

**レスポンスフィールド詳細**:

| フィールド | 型 | 説明 |
|---|---|---|
| `issues` | array | Issueオブジェクトの配列 |
| `total_count` | integer | フィルタ条件に合致する総件数（ページネーションに使用） |
| `offset` | integer | 今回取得した開始オフセット |
| `limit` | integer | 今回の取得件数上限 |

**ページネーション終了条件**:

- `issues` の件数が `limit` より少ない場合、最終ページに到達したと判断する
- または `offset + len(issues) >= total_count` の場合

**エラーレスポンス**:

| HTTPステータス | 発生条件 | 対処 |
|---|---|---|
| 401 Unauthorized | APIキーが無効 | 設定エラーとしてログに記録し、ユーザーに通知 |
| 403 Forbidden | プロジェクトへのアクセス権限なし | アクセス拒否エラーとしてユーザーに通知 |
| 500 Internal Server Error | Redmineサーバーエラー | リトライ後にエラーをユーザーに通知 |

---

## 4. Redmine優先度マスタ

### 4.1 デフォルト優先度一覧

Redmineの標準インストール時のデフォルト優先度。本システムではこのデフォルト設定を前提とする。

| priority_id | 名称（英語） | 名称（日本語） | 説明 | 色（参考） |
|---|---|---|---|---|
| 1 | Low | 低 | 緊急性のない通常より低い優先度 | グレー |
| 2 | Normal | 通常 | デフォルト優先度 | ブルー |
| 3 | High | 高 | 通常より高い優先度 | イエロー |
| 4 | Urgent | 緊急 | 緊急対応が必要 | オレンジ |
| 5 | Immediate | 即座に | 最高優先度。即座の対応が必要 | レッド |

**重要**: 優先度IDは Redmine の管理画面から変更可能。環境によってIDが異なる場合は `GET /enumerations/priorities.json` で確認すること。

### 4.2 優先度マスタ取得API

本番環境や設定変更後に優先度IDを確認するためのAPIを記述する（アプリ起動時・必要時に1回呼び出す）。

**エンドポイント**: GET `/enumerations/priorities.json`

**リクエスト**:

```http
GET /enumerations/priorities.json HTTP/1.1
Host: localhost:8080
X-Redmine-API-Key: {REDMINE_API_KEY}
Content-Type: application/json
```

**レスポンス（成功 200 OK）**:

```json
{
  "issue_priorities": [
    { "id": 1, "name": "低", "is_default": false, "active": true },
    { "id": 2, "name": "通常", "is_default": true, "active": true },
    { "id": 3, "name": "高", "is_default": false, "active": true },
    { "id": 4, "name": "緊急", "is_default": false, "active": true },
    { "id": 5, "name": "即座に", "is_default": false, "active": true }
  ]
}
```

**レスポンスフィールド詳細**:

| フィールド | 型 | 説明 |
|---|---|---|
| `id` | integer | 優先度ID（PUT `/issues/{id}.json` の `priority_id` に使用） |
| `name` | string | 優先度名称（日本語環境では日本語表記） |
| `is_default` | boolean | デフォルト優先度かどうか（Redmineで新規Issue作成時に使用） |
| `active` | boolean | アクティブな優先度かどうか（falseは非表示・使用不可） |

### 4.3 LLMへの優先度IDマッピング指示

LLMがユーザーの発話から `update_task_priority` ツールを呼び出す際の変換ルール（ツール定義の `description` および システムプロンプトに含める）:

```
優先度ID変換ルール:
- 「低い」「低」「低優先」→ priority_id = 1
- 「通常」「普通」「デフォルト」「標準」→ priority_id = 2
- 「高い」「高」「高優先」→ priority_id = 3
- 「緊急」「急いで」「急ぎ」「至急」→ priority_id = 4
- 「即座に」「すぐ」「今すぐ」「最高優先」→ priority_id = 5
```

---

## 5. Redmineデータフォーマット詳細

### 5.1 FEAT-004で重要なフィールドのデータ型

| フィールド名 | Redmine型 | Python型 | 変換規則 |
|---|---|---|---|
| `priority.id` | integer | int | そのまま使用 |
| `priority.name` | string | str | そのまま使用 |
| `due_date` | string (YYYY-MM-DD) \| null | `date \| None` | `date.fromisoformat()` / `None` |
| `start_date` | string (YYYY-MM-DD) \| null | `date \| None` | `date.fromisoformat()` / `None` |
| `total_count` | integer | int | ページネーション管理に使用 |

### 5.2 `due_date` null値の扱い

Redmineの `due_date` フィールドは:

- **存在しない** / **null**: 期日未設定（`None` として扱う）
- **"YYYY-MM-DD"**: 期日が設定されている

```python
# 変換例
raw_due_date = issue_data.get("due_date")  # None または "2026-03-14"
due_date = date.fromisoformat(raw_due_date) if raw_due_date else None
```

### 5.3 `priority` オブジェクトの変換

```python
# Redmineのpriority オブジェクト
priority_data = issue_data.get("priority", {})
priority_id = priority_data.get("id", 2)   # デフォルト: 通常(2)
priority_name = priority_data.get("name", "通常")

# TaskPriority 値オブジェクトへの変換
task_priority = TaskPriority(id=priority_id, name=priority_name)
```

---

## 6. RedmineAdapter 実装仕様（FEAT-004拡張）

### 6.1 クラス概要

FEAT-003で実装した `RedmineAdapter` に、以下のメソッドを追加する。

```
backend/app/infrastructure/redmine/redmine_adapter.py
```

**追加メソッド**:

| メソッド名 | 説明 |
|---|---|
| `update_issue_priority(issue_id, priority_id)` | 優先度を更新する（内部的には `update_issue` を使用） |
| `update_issue_due_date(issue_id, due_date)` | 期日を更新する（内部的には `update_issue` を使用） |
| `list_issues(params)` | 指定条件でIssue一覧を取得する |

### 6.2 `update_issue_priority` 実装仕様

```python
async def update_issue_priority(self, issue_id: int, priority_id: int) -> dict:
    """
    RedmineチケットのPriority（優先度）を更新する。
    更新後に GET /issues/{id}.json で最新状態を取得して返す。

    Args:
        issue_id: Redmine Issue ID
        priority_id: 新しい優先度ID（1〜5）

    Returns:
        更新後のIssue辞書（Redmineレスポンス形式）

    Raises:
        TaskNotFoundError: 指定IDのIssueが存在しない
        RedmineConnectionError: Redmine接続失敗
        RedmineAPIError: Redmine APIエラー（422など）
    """
    payload = {
        "issue": {
            "priority_id": priority_id
        }
    }
    url = f"{self.base_url}/issues/{issue_id}.json"

    async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await self._put_with_retry(client, url, payload)

    # 更新後の状態を取得
    return await self.get_issue(issue_id)
```

### 6.3 `update_issue_due_date` 実装仕様

```python
async def update_issue_due_date(self, issue_id: int, due_date: date) -> dict:
    """
    RedmineチケットのDue Date（期日）を更新する。
    更新後に GET /issues/{id}.json で最新状態を取得して返す。

    Args:
        issue_id: Redmine Issue ID
        due_date: 新しい期日（dateオブジェクト）

    Returns:
        更新後のIssue辞書（Redmineレスポンス形式）

    Raises:
        TaskNotFoundError: 指定IDのIssueが存在しない
        RedmineConnectionError: Redmine接続失敗
        RedmineAPIError: バリデーションエラー（start_date > due_date 等）
    """
    payload = {
        "issue": {
            "due_date": due_date.isoformat()  # "YYYY-MM-DD" 形式
        }
    }
    url = f"{self.base_url}/issues/{issue_id}.json"

    async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await self._put_with_retry(client, url, payload)

    # 更新後の状態を取得
    return await self.get_issue(issue_id)
```

### 6.4 `list_issues` 実装仕様

```python
async def list_issues(self, params: dict) -> dict:
    """
    条件を指定してRedmine Issueの一覧を取得する。

    ページネーションのため、PriorityReportServiceがoffsetを増やしながら
    繰り返し呼び出すことを想定した設計。

    Args:
        params: クエリパラメータ辞書
                例: {"status_id": "open", "limit": 100, "offset": 0}

    Returns:
        Redmineレスポンス辞書
        {"issues": [...], "total_count": N, "offset": N, "limit": N}

    Raises:
        RedmineConnectionError: Redmine接続失敗
        RedmineAPIError: APIエラー（403等）
    """
    url = f"{self.base_url}/issues.json"
    headers = {
        "X-Redmine-API-Key": self.api_key,
        "Content-Type": "application/json",
    }

    for attempt in range(self.max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, params=params)

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                raise RedmineAPIError("Redmine認証エラー: APIキーが無効です", status_code=401)
            elif response.status_code == 403:
                raise RedmineAPIError("Redmineアクセス拒否: プロジェクトへのアクセス権限がありません", status_code=403)
            else:
                raise RedmineAPIError(
                    f"Redmine APIエラー: status={response.status_code}",
                    status_code=response.status_code,
                )

        except httpx.TimeoutException:
            if attempt < self.max_retries:
                wait_secs = 2 ** attempt  # 指数バックオフ: 1s → 2s → 4s
                self.logger.warning(f"Redmine list_issues タイムアウト。{wait_secs}秒後にリトライ ({attempt + 1}/{self.max_retries})")
                await asyncio.sleep(wait_secs)
            else:
                raise RedmineConnectionError("Redmine接続タイムアウト（リトライ上限到達）")

        except httpx.ConnectError as e:
            if attempt < self.max_retries:
                wait_secs = 2 ** attempt
                self.logger.warning(f"Redmine list_issues 接続エラー。{wait_secs}秒後にリトライ ({attempt + 1}/{self.max_retries})")
                await asyncio.sleep(wait_secs)
            else:
                raise RedmineConnectionError(f"Redmine接続エラー: {str(e)}")
```

### 6.5 `_put_with_retry` 共通メソッド仕様

FEAT-003・FEAT-004共通のPUT操作リトライメソッド。FEAT-003で実装済みのものをFEAT-004でも使用する。

```python
async def _put_with_retry(
    self,
    client: httpx.AsyncClient,
    url: str,
    payload: dict,
) -> httpx.Response:
    """
    PUT操作をリトライ付きで実行する共通メソッド。

    Args:
        client: httpxクライアント
        url: リクエストURL
        payload: リクエストボディ（dict）

    Returns:
        httpxレスポンス（204 or 200）

    Raises:
        TaskNotFoundError: 404の場合
        RedmineAPIError: 422など
        RedmineConnectionError: タイムアウト・接続エラー（リトライ上限後）
    """
    headers = {
        "X-Redmine-API-Key": self.api_key,
        "Content-Type": "application/json",
    }

    for attempt in range(self.max_retries + 1):
        try:
            response = await client.put(url, headers=headers, json=payload)

            if response.status_code in (200, 204):
                return response
            elif response.status_code == 404:
                raise TaskNotFoundError(f"Issueが見つかりません: {url}")
            elif response.status_code == 401:
                raise RedmineAPIError("Redmine認証エラー: APIキーが無効です", status_code=401)
            elif response.status_code == 403:
                raise RedmineAPIError("Redmineアクセス拒否: 更新権限がありません", status_code=403)
            elif response.status_code == 422:
                error_body = response.json()
                errors = error_body.get("errors", [])
                raise RedmineAPIError(
                    f"Redmineバリデーションエラー: {', '.join(errors)}",
                    status_code=422,
                )
            else:
                if attempt < self.max_retries:
                    wait_secs = 2 ** attempt
                    await asyncio.sleep(wait_secs)
                    continue
                raise RedmineAPIError(
                    f"Redmine APIエラー: status={response.status_code}",
                    status_code=response.status_code,
                )

        except httpx.TimeoutException:
            if attempt < self.max_retries:
                wait_secs = 2 ** attempt
                self.logger.warning(f"Redmine PUT タイムアウト。{wait_secs}秒後にリトライ ({attempt + 1}/{self.max_retries})")
                await asyncio.sleep(wait_secs)
            else:
                raise RedmineConnectionError("Redmine PUT タイムアウト（リトライ上限到達）")

        except httpx.ConnectError as e:
            if attempt < self.max_retries:
                wait_secs = 2 ** attempt
                await asyncio.sleep(wait_secs)
            else:
                raise RedmineConnectionError(f"Redmine接続エラー: {str(e)}")

    raise RedmineConnectionError("想定外のリトライ終了")
```

### 6.6 RedmineAdapter 全体構成（FEAT-004追加後）

```python
import asyncio
import logging
from datetime import date
from typing import Optional

import httpx

from app.domain.task.exceptions import TaskNotFoundError
from app.infrastructure.redmine.exceptions import RedmineAPIError, RedmineConnectionError


class RedmineAdapter:
    """
    Redmine REST APIとの通信を担当するアダプタ。
    ACL（Anti-Corruption Layer）として、Redmineのデータモデルを
    内部ドメインモデルから分離する。
    """

    def __init__(self, base_url: str, api_key: str, max_retries: int = 2):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.max_retries = max_retries
        self.timeout = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)
        self.logger = logging.getLogger(__name__)

    # ── FEAT-003 ──────────────────────────────────────────────────────
    async def get_issue(self, issue_id: int) -> dict: ...
    async def update_issue_status(self, issue_id: int, status_id: int, notes: Optional[str] = None) -> dict: ...
    async def add_issue_comment(self, issue_id: int, notes: str) -> dict: ...

    # ── FEAT-004 ──────────────────────────────────────────────────────
    async def update_issue_priority(self, issue_id: int, priority_id: int) -> dict: ...
    async def update_issue_due_date(self, issue_id: int, due_date: date) -> dict: ...
    async def list_issues(self, params: dict) -> dict: ...

    # ── 共通内部メソッド ──────────────────────────────────────────────
    async def _put_with_retry(self, client: httpx.AsyncClient, url: str, payload: dict) -> httpx.Response: ...
```

---

## 7. ACL変換マッピング

### 7.1 Redmine Issue → Task エンティティ変換（FEAT-004追加フィールド）

FEAT-003で設計したACL変換に、FEAT-004で追加するフィールドのマッピングを補足する。

| Redmineフィールド | Python型 | 内部ドメインフィールド | 変換ロジック |
|---|---|---|---|
| `issue.priority.id` | int | `Task.priority.id` | `int(priority_data["id"])` |
| `issue.priority.name` | str | `Task.priority.name` | `str(priority_data.get("name", "通常"))` |
| `issue.due_date` | str \| null | `Task.due_date` | `date.fromisoformat(v) if v else None` |
| `issue.start_date` | str \| null | `Task.start_date` | `date.fromisoformat(v) if v else None` |

### 7.2 Task.from_redmine_response（FEAT-004追加フィールド対応）

```python
@classmethod
def from_redmine_response(cls, response: dict) -> "Task":
    """
    Redmine API レスポンス辞書からTaskエンティティを生成する。
    FEAT-003（status, notes）+ FEAT-004（priority, due_date）対応。
    """
    issue = response["issue"]
    priority_data = issue.get("priority", {})
    due_date_str = issue.get("due_date")
    start_date_str = issue.get("start_date")

    return cls(
        redmine_issue_id=issue["id"],
        title=issue["subject"],
        description=issue.get("description", ""),
        status=TaskStatus.from_id(issue["status"]["id"]),
        priority=TaskPriority(
            id=priority_data.get("id", 2),
            name=priority_data.get("name", "通常"),
        ),
        due_date=date.fromisoformat(due_date_str) if due_date_str else None,
        start_date=date.fromisoformat(start_date_str) if start_date_str else None,
        done_ratio=issue.get("done_ratio", 0),
    )
```

### 7.3 PriorityUpdateResult への変換

```python
@dataclass
class PriorityUpdateResult:
    """優先度更新結果をフロントエンドに返すためのDTO。"""
    issue_id: int
    title: str
    old_priority_id: int
    new_priority_id: int
    new_priority_name: str
    updated_at: str  # ISO 8601形式

@dataclass
class DueDateUpdateResult:
    """期日更新結果をフロントエンドに返すためのDTO。"""
    issue_id: int
    title: str
    old_due_date: Optional[str]   # "YYYY-MM-DD" または None
    new_due_date: str              # "YYYY-MM-DD"
    is_past_due: bool              # 過去日付かどうか
    updated_at: str                # ISO 8601形式
```

---

## 8. リトライ・タイムアウト設計

### 8.1 リトライポリシー（FEAT-004共通）

FEAT-003と同一のリトライポリシーを適用する。

| 項目 | 値 | 説明 |
|---|---|---|
| 最大リトライ回数 | 2回（合計3回試行） | `max_retries=2` |
| リトライ待機時間 | 指数バックオフ | 1回目失敗→1秒待機, 2回目失敗→2秒待機, 3回目失敗→例外 |
| リトライ対象 | タイムアウト・接続エラー・500系エラー | クライアントエラー（4xx）はリトライしない |
| 非リトライ対象 | 401, 403, 404, 422 | 認証エラー・バリデーションエラーはリトライ不要 |

**待機時間計算式**:

```
wait_seconds = 2 ^ attempt_index
  attempt 0 (1回目失敗) → wait = 1秒
  attempt 1 (2回目失敗) → wait = 2秒
  attempt 2 (3回目失敗) → 例外送出（4秒は待機しない）
```

### 8.2 list_issues 専用の考慮事項

`list_issues` はページネーション中に失敗した場合、全件取得が中断される。このため:

- タイムアウトはGET操作として読み取りタイムアウト30秒を適用する
- ページネーションの途中でエラーが発生した場合は `RedmineConnectionError` を送出し、部分データを返さない
- 最大取得件数は1000件（offset=900まで）とし、それ以上は打ち切る（レポートの実用性を考慮）

```python
MAX_TOTAL_ISSUES = 1000  # 安全上限

while True:
    if offset >= MAX_TOTAL_ISSUES:
        self.logger.warning(f"未完了タスクが{MAX_TOTAL_ISSUES}件を超えています。最初の{MAX_TOTAL_ISSUES}件のみレポートします。")
        break
    # ... (取得処理)
```

### 8.3 タイムアウト設定

| 操作 | タイムアウト種別 | 値 |
|---|---|---|
| 接続確立 | `connect` | 10秒 |
| レスポンス読み取り（GET） | `read` | 30秒 |
| リクエスト送信（PUT） | `write` | 10秒 |
| コネクションプール取得 | `pool` | 5秒 |

---

## 9. エラーハンドリング

### 9.1 例外クラス階層

FEAT-003で定義した例外クラスをそのまま使用する。

```python
# app/infrastructure/redmine/exceptions.py
class RedmineError(Exception):
    """Redmine操作の基底例外クラス。"""

class RedmineConnectionError(RedmineError):
    """Redmineへの接続失敗（タイムアウト・ネットワークエラー）。"""

class RedmineAPIError(RedmineError):
    """Redmine APIエラー（4xx/5xx レスポンス）。"""
    def __init__(self, message: str, status_code: int = 0):
        super().__init__(message)
        self.status_code = status_code

# app/domain/task/exceptions.py
class TaskError(Exception):
    """タスクドメインの基底例外クラス。"""

class TaskNotFoundError(TaskError):
    """指定IDのタスクが存在しない。"""

class InvalidPriorityError(TaskError):
    """無効な優先度IDが指定された。"""

class InvalidDueDateError(TaskError):
    """無効な期日が指定された（形式エラー等）。"""
```

### 9.2 エラーケース別処理方針

| エラー種別 | 発生条件 | 処理方針 | ユーザーへのメッセージ例 |
|---|---|---|---|
| `TaskNotFoundError` | 指定チケットIDが存在しない | 即座にエラーを返す | 「チケット #999 は見つかりませんでした。IDをご確認ください。」 |
| `InvalidPriorityError` | priority_id が {1,2,3,4,5} 以外 | バリデーション時に即座にエラー | 「優先度IDは1〜5の値を指定してください。」 |
| `InvalidDueDateError` | due_date のフォーマットが不正 | バリデーション時に即座にエラー | 「期日の形式が正しくありません。YYYY-MM-DD形式で指定してください。」 |
| `RedmineAPIError(422)` | Redmineバリデーション失敗（start_date>due_date 等） | Redmineエラーメッセージをユーザーに伝達 | 「期日の設定に問題があります: {Redmineのエラーメッセージ}」 |
| `RedmineAPIError(403)` | 更新権限なし | 権限エラーをユーザーに通知 | 「このチケットを更新する権限がありません。」 |
| `RedmineConnectionError` | Redmineへの接続失敗（リトライ後） | 接続エラーをユーザーに通知 | 「Redmineへの接続に失敗しました。しばらく後にお試しください。」 |

### 9.3 `list_issues` 専用エラー処理

優先タスクレポートでは `list_issues` が失敗すると全体が失敗する。

```python
async def generate_report(self, as_of: Optional[date] = None) -> PriorityReport:
    try:
        tasks = await self._fetch_open_tasks()
    except RedmineConnectionError as e:
        self.logger.error(f"優先タスクレポート生成失敗: Redmine接続エラー: {e}")
        raise  # 上位（TaskScheduleNode）に委譲
    except RedmineAPIError as e:
        self.logger.error(f"優先タスクレポート生成失敗: Redmine APIエラー: {e}")
        raise
```

---

## 10. 後続フェーズへの影響

### 10.1 IMP（実装）フェーズへの影響

| 実装箇所 | 内容 |
|---|---|
| `backend/app/infrastructure/redmine/redmine_adapter.py` | `update_issue_priority()`・`update_issue_due_date()`・`list_issues()` を追加実装する |
| `backend/app/infrastructure/redmine/exceptions.py` | `InvalidPriorityError`・`InvalidDueDateError` を追加定義する |
| `backend/app/domain/task/entities.py` | `Task.from_redmine_response()` にpriority・due_dateフィールドを追加する |
| `backend/app/application/services/task_schedule_service.py` | `update_task_priority()`・`update_task_due_date()` で `RedmineAdapter` を呼び出す |
| `backend/app/application/services/priority_report_service.py` | `_fetch_open_tasks()` で `RedmineAdapter.list_issues()` を呼び出す |

### 10.2 IT（結合テスト）フェーズへの影響

| テスト項目 | 確認ポイント |
|---|---|
| Redmine優先度更新 | PUT `/issues/{id}.json` に `priority_id` を送信し、Redmine側で実際に優先度が変わること |
| Redmine期日更新 | PUT `/issues/{id}.json` に `due_date` を送信し、Redmine側で実際に期日が変わること |
| 未完了Issue一覧取得 | GET `/issues.json?status_id=open` で未完了タスクのみ返ること |
| ページネーション | 100件超の未完了タスクがある場合にoffsetを増やして全件取得できること |
| 優先度マスタ確認 | `GET /enumerations/priorities.json` で priority_id=1〜5 が返ること |

### 10.3 ST（システムテスト）フェーズへの影響

- Redmineが実際に動作する環境での統合テストが必要
- Docker Composeでローカル環境を構築し、Redmine実機との疎通確認を行う

---
