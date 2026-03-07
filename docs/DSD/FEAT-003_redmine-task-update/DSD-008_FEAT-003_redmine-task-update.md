# DSD-008_FEAT-003 単体テスト設計書（Redmineタスク更新・進捗報告）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-008_FEAT-003 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-003 |
| 機能名 | Redmineタスク更新・進捗報告 |
| 入力元 | DSD-001_FEAT-003, DSD-003_FEAT-003, DSD-005_FEAT-003 |
| ステータス | 初版 |

---

## 目次

1. テスト設計方針（TDD）
2. テスト対象コンポーネント
3. モック方針
4. バックエンド単体テスト設計
5. フロントエンド単体テスト設計
6. テストデータ定義
7. カバレッジ目標
8. 後続フェーズへの影響

---

## 1. テスト設計方針（TDD）

### 1.1 TDDサイクル

本設計書はTDD（テスト駆動開発）の「Red → Green → Refactor」サイクルの起点となる。

1. **Red フェーズ**: 本設計書のテストケースに基づきテストコードを先に実装し、失敗させる
2. **Green フェーズ**: テストが通過するように実装コードを最小限で実装する
3. **Refactor フェーズ**: テストを維持しながらコードの品質を向上させる

### 1.2 テストフレームワーク

| 領域 | フレームワーク | 補助ライブラリ |
|---|---|---|
| バックエンド（Python） | pytest + pytest-asyncio | httpx (テスト用)・respx（httpxモック）・pytest-mock |
| フロントエンド（TypeScript） | Vitest + React Testing Library | MSW（Mock Service Worker）・@testing-library/user-event |

### 1.3 テスト範囲

FEAT-003の単体テスト対象:
1. `TaskUpdateService.update_task_status`（UC-003: ステータス更新）
2. `TaskUpdateService.add_task_comment`（UC-004: コメント追加）
3. `RedmineAdapter.update_issue`（Redmine API呼び出し）
4. `RedmineAdapter.get_issue`（Issue存在確認）
5. `TaskStatus.from_id` / `TaskStatus.validate_id`（値オブジェクト）
6. `useChat` カスタムフック（フロントエンドSSE処理）
7. `TaskUpdateConfirmation` コンポーネント

---

## 2. テスト対象コンポーネント

| コンポーネント | ファイルパス | テスト種別 | 優先度 |
|---|---|---|---|
| TaskUpdateService | `backend/app/application/services/task_update_service.py` | 単体テスト | 最高 |
| RedmineAdapter | `backend/app/infrastructure/redmine/redmine_adapter.py` | 単体テスト（モック使用） | 最高 |
| TaskStatus | `backend/app/domain/task/value_objects.py` | 単体テスト | 高 |
| TaskPriority | `backend/app/domain/task/value_objects.py` | 単体テスト | 高 |
| Task.from_redmine_response | `backend/app/domain/task/entities.py` | 単体テスト | 高 |
| UpdateTaskRequest（バリデーション） | `backend/app/presentation/schemas/task_update.py` | 単体テスト | 高 |
| useChat（SSE処理） | `frontend/hooks/useChat.ts` | 単体テスト | 高 |
| TaskUpdateConfirmation | `frontend/components/chat/TaskUpdateConfirmation.tsx` | レンダリングテスト | 中 |
| ToolCallBadge | `frontend/components/chat/ToolCallBadge.tsx` | レンダリングテスト | 中 |

---

## 3. モック方針

### 3.1 バックエンドのモック

| モック対象 | モック方法 | 理由 |
|---|---|---|
| `httpx.AsyncClient`（Redmine HTTP呼び出し） | `respx` または `unittest.mock.AsyncMock` | Redmineサーバーなしでテスト可能にする |
| `RedmineAdapter` | `pytest-mock` の `MagicMock` | `TaskUpdateService` の単体テストでAdapterを差し替える |

```python
# RedmineAdapterのモック例
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_redmine_adapter():
    adapter = MagicMock()
    adapter.get_issue = AsyncMock()
    adapter.update_issue = AsyncMock()
    return adapter

@pytest.fixture
def task_update_service(mock_redmine_adapter):
    from app.application.services.task_update_service import TaskUpdateService
    return TaskUpdateService(redmine_adapter=mock_redmine_adapter)
```

### 3.2 フロントエンドのモック

| モック対象 | モック方法 | 理由 |
|---|---|---|
| `fetch`（バックエンドAPI呼び出し） | MSW（Mock Service Worker）またはVitest `vi.fn()` | バックエンドなしでフロントエンドをテスト |
| SSEレスポンス | ReadableStream のモック | SSEストリーム処理のテスト |

---

## 4. バックエンド単体テスト設計

### 4.1 TaskStatus 値オブジェクトのテスト

**テストファイル**: `backend/tests/domain/test_task_value_objects.py`

#### TC-S01: TaskStatus.from_id - 有効なステータスID（正常系）

```python
# Given-When-Then

@pytest.mark.parametrize("status_id, expected_name", [
    (1, "未着手"),
    (2, "進行中"),
    (3, "完了"),
    (5, "却下"),
])
def test_task_status_from_id_valid(status_id, expected_name):
    """
    Given: 有効なステータスID（1, 2, 3, 5のいずれか）
    When: TaskStatus.from_id(status_id) を呼び出す
    Then: 正しい名称のTaskStatusオブジェクトが返される
    """
    # When
    status = TaskStatus.from_id(status_id)
    # Then
    assert status.id == status_id
    assert status.name == expected_name
```

#### TC-S02: TaskStatus.from_id - 無効なステータスID（異常系）

```python
@pytest.mark.parametrize("invalid_id", [0, 4, 6, 100, -1])
def test_task_status_from_id_invalid(invalid_id):
    """
    Given: 無効なステータスID（{1,2,3,5}以外）
    When: TaskStatus.from_id(invalid_id) を呼び出す
    Then: ValueError が発生する
    """
    with pytest.raises(ValueError, match="無効なステータスID"):
        TaskStatus.from_id(invalid_id)
```

#### TC-S03: TaskStatus.validate_id - 検証

```python
@pytest.mark.parametrize("status_id, expected", [
    (1, True), (2, True), (3, True), (5, True),
    (0, False), (4, False), (6, False), (10, False),
])
def test_task_status_validate_id(status_id, expected):
    """
    Given: ステータスID
    When: TaskStatus.validate_id(status_id) を呼び出す
    Then: 有効なIDはTrue、無効なIDはFalseが返される
    """
    assert TaskStatus.validate_id(status_id) == expected
```

---

### 4.2 Task.from_redmine_response のテスト

**テストファイル**: `backend/tests/domain/test_task_entities.py`

#### TC-E01: 正常なRedmineレスポンスからTaskを生成（正常系）

```python
def test_task_from_redmine_response_full():
    """
    Given: 全フィールドが揃ったRedmine Issueレスポンス
    When: Task.from_redmine_response(data) を呼び出す
    Then: 正しい属性を持つTaskオブジェクトが生成される
    """
    # Given
    redmine_response = {
        "issue": {
            "id": 123,
            "subject": "設計書作成",
            "status": {"id": 2, "name": "進行中"},
            "priority": {"id": 2, "name": "通常"},
            "assigned_to": {"id": 1, "name": "山田 太郎"},
            "due_date": "2026-03-31",
            "updated_on": "2026-03-03T10:00:00Z",
        }
    }
    # When
    task = Task.from_redmine_response(redmine_response)
    # Then
    assert task.redmine_issue_id == 123
    assert task.title == "設計書作成"
    assert task.status.id == 2
    assert task.status.name == "進行中"
    assert task.assignee == "山田 太郎"
    assert str(task.due_date) == "2026-03-31"
```

#### TC-E02: オプションフィールドがnullのRedmineレスポンスからTaskを生成（正常系）

```python
def test_task_from_redmine_response_nullable_fields():
    """
    Given: assigned_to・due_dateがnullのRedmine Issueレスポンス
    When: Task.from_redmine_response(data) を呼び出す
    Then: assigneeはNone、due_dateはNoneのTaskオブジェクトが生成される
    """
    redmine_response = {
        "issue": {
            "id": 456,
            "subject": "タスクタイトル",
            "status": {"id": 1, "name": "未着手"},
            "priority": {"id": 2, "name": "通常"},
            "due_date": None,
            "updated_on": "2026-03-03T10:00:00Z",
        }
    }
    task = Task.from_redmine_response(redmine_response)
    assert task.assignee is None
    assert task.due_date is None
```

---

### 4.3 TaskUpdateService のテスト

**テストファイル**: `backend/tests/application/services/test_task_update_service.py`

#### TC-SVC01: update_task_status - ステータス更新成功（正常系）

```python
@pytest.mark.asyncio
async def test_update_task_status_success(task_update_service, mock_redmine_adapter):
    """
    Given: 存在するIssue ID=123、有効なstatus_id=3（完了）
    When: task_update_service.update_task_status(123, 3) を呼び出す
    Then: Redmine update_issueが呼び出され、更新後のTaskオブジェクトが返される
          ステータスが TaskStatus(id=3, name="完了") であること
    """
    # Given
    mock_redmine_adapter.get_issue.return_value = {
        "issue": {
            "id": 123, "subject": "設計書作成",
            "status": {"id": 2, "name": "進行中"},
            "priority": {"id": 2, "name": "通常"},
            "due_date": None, "updated_on": "2026-03-03T10:00:00Z",
        }
    }
    mock_redmine_adapter.update_issue.return_value = {
        "issue": {
            "id": 123, "subject": "設計書作成",
            "status": {"id": 3, "name": "完了"},
            "priority": {"id": 2, "name": "通常"},
            "due_date": None, "updated_on": "2026-03-03T15:00:00Z",
        }
    }

    # When
    result = await task_update_service.update_task_status(123, 3)

    # Then
    assert result.redmine_issue_id == 123
    assert result.status.id == 3
    assert result.status.name == "完了"
    # Redmine update_issueが正しいpayloadで呼び出されたことを確認
    mock_redmine_adapter.update_issue.assert_called_once_with(
        123, {"issue": {"status_id": 3}}
    )
```

#### TC-SVC02: update_task_status - notesを同時に追加（正常系）

```python
@pytest.mark.asyncio
async def test_update_task_status_with_notes(task_update_service, mock_redmine_adapter):
    """
    Given: 存在するIssue ID=123、status_id=3、notes="設計レビュー完了"
    When: task_update_service.update_task_status(123, 3, notes="設計レビュー完了") を呼び出す
    Then: payloadにstatus_idとnotesの両方が含まれてupdate_issueが呼び出される
    """
    # Given
    mock_redmine_adapter.get_issue.return_value = _make_issue_response(123, status_id=2)
    mock_redmine_adapter.update_issue.return_value = _make_issue_response(123, status_id=3)

    # When
    result = await task_update_service.update_task_status(123, 3, notes="設計レビュー完了")

    # Then
    assert result.status.id == 3
    mock_redmine_adapter.update_issue.assert_called_once_with(
        123, {"issue": {"status_id": 3, "notes": "設計レビュー完了"}}
    )
```

#### TC-SVC03: update_task_status - チケット不存在（異常系）

```python
@pytest.mark.asyncio
async def test_update_task_status_task_not_found(task_update_service, mock_redmine_adapter):
    """
    Given: 存在しないIssue ID=9999
    When: task_update_service.update_task_status(9999, 3) を呼び出す
    Then: TaskNotFoundError が発生する
          エラーメッセージにissue_id=9999が含まれる
    """
    # Given
    from app.domain.exceptions import TaskNotFoundError
    mock_redmine_adapter.get_issue.side_effect = TaskNotFoundError(9999)

    # When / Then
    with pytest.raises(TaskNotFoundError) as exc_info:
        await task_update_service.update_task_status(9999, 3)

    assert "9999" in str(exc_info.value)
    # update_issueは呼び出されない
    mock_redmine_adapter.update_issue.assert_not_called()
```

#### TC-SVC04: update_task_status - 無効なステータスID（異常系）

```python
@pytest.mark.parametrize("invalid_status_id", [0, 4, 6, 10, -1, 100])
@pytest.mark.asyncio
async def test_update_task_status_invalid_status_id(
    task_update_service, mock_redmine_adapter, invalid_status_id
):
    """
    Given: 無効なstatus_id（{1,2,3,5}以外）
    When: task_update_service.update_task_status(123, invalid_status_id) を呼び出す
    Then: InvalidStatusIdError が発生する
          get_issueもupdate_issueも呼び出されない
    """
    from app.domain.exceptions import InvalidStatusIdError

    with pytest.raises(InvalidStatusIdError):
        await task_update_service.update_task_status(123, invalid_status_id)

    # バリデーション失敗のため、Redmine APIは一切呼び出されない
    mock_redmine_adapter.get_issue.assert_not_called()
    mock_redmine_adapter.update_issue.assert_not_called()
```

#### TC-SVC05: update_task_status - 削除操作試行のブロック（BR-02検証）

```python
@pytest.mark.asyncio
async def test_update_task_status_delete_operation_blocked(task_update_service):
    """
    Given: 削除を示す操作名が渡される（BR-02のセーフガード確認）
    When: _prevent_delete_operation("delete_issue") を内部で呼び出す
    Then: TaskDeleteOperationForbiddenError が発生する
    Note: エージェントのツール定義にdelete_issueは存在しないため通常は発生しない。
          多層防御の最終確認テスト。
    """
    from app.domain.exceptions import TaskDeleteOperationForbiddenError

    with pytest.raises(TaskDeleteOperationForbiddenError):
        task_update_service._prevent_delete_operation("delete_issue")
```

#### TC-SVC06: add_task_comment - コメント追加成功（正常系）

```python
@pytest.mark.asyncio
async def test_add_task_comment_success(task_update_service, mock_redmine_adapter):
    """
    Given: 存在するIssue ID=45、notes="設計レビュー完了"
    When: task_update_service.add_task_comment(45, "設計レビュー完了") を呼び出す
    Then: payloadにnotesのみが含まれてupdate_issueが呼び出される
          ステータスは変更されない
    """
    # Given
    original_status_id = 2  # 進行中
    mock_redmine_adapter.get_issue.return_value = _make_issue_response(45, status_id=original_status_id)
    mock_redmine_adapter.update_issue.return_value = _make_issue_response(45, status_id=original_status_id)

    # When
    result = await task_update_service.add_task_comment(45, "設計レビュー完了")

    # Then
    # ステータスは変更されていない
    assert result.status.id == original_status_id
    # notesのみのpayloadでupdate_issueが呼び出される
    mock_redmine_adapter.update_issue.assert_called_once_with(
        45, {"issue": {"notes": "設計レビュー完了"}}
    )
```

#### TC-SVC07: add_task_comment - 空のコメント（異常系）

```python
@pytest.mark.parametrize("empty_notes", ["", "  ", "\n", "\t"])
@pytest.mark.asyncio
async def test_add_task_comment_empty_notes(
    task_update_service, mock_redmine_adapter, empty_notes
):
    """
    Given: 空またはスペースのみのnotes
    When: task_update_service.add_task_comment(45, empty_notes) を呼び出す
    Then: ValueError が発生する
          Redmine APIは呼び出されない
    """
    with pytest.raises(ValueError, match="コメント内容は空にできません"):
        await task_update_service.add_task_comment(45, empty_notes)

    mock_redmine_adapter.get_issue.assert_not_called()
    mock_redmine_adapter.update_issue.assert_not_called()
```

#### TC-SVC08: add_task_comment - チケット不存在（異常系）

```python
@pytest.mark.asyncio
async def test_add_task_comment_task_not_found(task_update_service, mock_redmine_adapter):
    """
    Given: 存在しないIssue ID=9999
    When: task_update_service.add_task_comment(9999, "コメント") を呼び出す
    Then: TaskNotFoundError が発生する
    """
    from app.domain.exceptions import TaskNotFoundError
    mock_redmine_adapter.get_issue.side_effect = TaskNotFoundError(9999)

    with pytest.raises(TaskNotFoundError):
        await task_update_service.add_task_comment(9999, "コメント")

    mock_redmine_adapter.update_issue.assert_not_called()
```

---

### 4.4 RedmineAdapter のテスト

**テストファイル**: `backend/tests/infrastructure/redmine/test_redmine_adapter.py`

モック手法: `respx`（httpxのモックライブラリ）を使用してHTTPリクエストをインターセプトする。

```python
import respx
import httpx
import pytest

REDMINE_BASE_URL = "http://localhost:8080"
REDMINE_API_KEY = "test-api-key"

@pytest.fixture
def adapter():
    from app.infrastructure.redmine.redmine_adapter import RedmineAdapter
    return RedmineAdapter(
        base_url=REDMINE_BASE_URL,
        api_key=REDMINE_API_KEY,
    )
```

#### TC-ADPT01: update_issue - ステータス更新成功（正常系）

```python
@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_update_issue_success(adapter):
    """
    Given: Redmine PUT /issues/123.json が204を返し、
           続くGET /issues/123.json が更新済みIssueを返す
    When: adapter.update_issue(123, {"issue": {"status_id": 3}}) を呼び出す
    Then: 更新後のIssueデータが返される（status.id=3）
          PUTリクエストのボディに正しいpayloadが含まれる
    """
    # Redmine PUT レスポンスのモック（204 No Content）
    respx.put(f"{REDMINE_BASE_URL}/issues/123.json").mock(
        return_value=httpx.Response(204)
    )
    # Redmine GET レスポンスのモック（更新後の状態）
    respx.get(f"{REDMINE_BASE_URL}/issues/123.json").mock(
        return_value=httpx.Response(200, json={
            "issue": {
                "id": 123, "subject": "設計書作成",
                "status": {"id": 3, "name": "完了"},
                "priority": {"id": 2, "name": "通常"},
                "due_date": None, "updated_on": "2026-03-03T15:00:00Z",
            }
        })
    )

    # When
    result = await adapter.update_issue(123, {"issue": {"status_id": 3}})

    # Then
    assert result["issue"]["status"]["id"] == 3
    assert result["issue"]["status"]["name"] == "完了"
```

#### TC-ADPT02: update_issue - チケット不存在（異常系）

```python
@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_update_issue_not_found(adapter):
    """
    Given: Redmine PUT /issues/9999.json が404を返す
    When: adapter.update_issue(9999, {...}) を呼び出す
    Then: TaskNotFoundError が発生する
    """
    from app.domain.exceptions import TaskNotFoundError
    respx.put(f"{REDMINE_BASE_URL}/issues/9999.json").mock(
        return_value=httpx.Response(404)
    )

    with pytest.raises(TaskNotFoundError) as exc_info:
        await adapter.update_issue(9999, {"issue": {"status_id": 3}})

    assert "9999" in str(exc_info.value)
```

#### TC-ADPT03: update_issue - Redmineサーバーエラーのリトライ（異常系）

```python
@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_update_issue_server_error_with_retry(adapter):
    """
    Given: Redmine PUT /issues/123.json が3回連続で500を返す
    When: adapter.update_issue(123, {...}) を呼び出す
    Then: リトライが3回行われた後に RedmineConnectionError が発生する
    """
    from app.domain.exceptions import RedmineConnectionError

    respx.put(f"{REDMINE_BASE_URL}/issues/123.json").mock(
        return_value=httpx.Response(500)
    )

    with pytest.raises(RedmineConnectionError):
        await adapter.update_issue(123, {"issue": {"status_id": 3}})
```

#### TC-ADPT04: update_issue - Redmineバリデーションエラー（異常系）

```python
@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_update_issue_validation_error(adapter):
    """
    Given: Redmine PUT /issues/123.json が422とエラーメッセージを返す
    When: adapter.update_issue(123, {...}) を呼び出す
    Then: ValueError が発生し、Redmineのエラーメッセージが含まれる
    """
    respx.put(f"{REDMINE_BASE_URL}/issues/123.json").mock(
        return_value=httpx.Response(422, json={
            "errors": ["ステータスを変更するためのトランジションが存在しません"]
        })
    )

    with pytest.raises(ValueError, match="ステータスを変更するためのトランジション"):
        await adapter.update_issue(123, {"issue": {"status_id": 3}})
```

#### TC-ADPT05: get_issue - Issue取得成功（正常系）

```python
@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_get_issue_success(adapter):
    """
    Given: Redmine GET /issues/123.json が200とIssueデータを返す
    When: adapter.get_issue(123) を呼び出す
    Then: Issueデータが返される
    """
    respx.get(f"{REDMINE_BASE_URL}/issues/123.json").mock(
        return_value=httpx.Response(200, json={
            "issue": {
                "id": 123, "subject": "設計書作成",
                "status": {"id": 2, "name": "進行中"},
                "priority": {"id": 2, "name": "通常"},
                "due_date": None, "updated_on": "2026-03-03T10:00:00Z",
            }
        })
    )

    result = await adapter.get_issue(123)
    assert result["issue"]["id"] == 123
    assert result["issue"]["subject"] == "設計書作成"
```

#### TC-ADPT06: 接続タイムアウトのリトライ（異常系）

```python
@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_connection_timeout_retry(adapter):
    """
    Given: HTTPリクエストがTimeoutExceptionを発生させる（3回連続）
    When: adapter.get_issue(123) を呼び出す
    Then: リトライが3回行われた後に RedmineConnectionError が発生する
    """
    from app.domain.exceptions import RedmineConnectionError

    respx.get(f"{REDMINE_BASE_URL}/issues/123.json").mock(
        side_effect=httpx.TimeoutException("接続タイムアウト")
    )

    with pytest.raises(RedmineConnectionError, match="タイムアウト"):
        await adapter.get_issue(123)
```

---

### 4.5 APIバリデーションのテスト

**テストファイル**: `backend/tests/presentation/test_task_update_validation.py`

#### TC-VAL01: UpdateTaskRequest - status_id有効値（正常系）

```python
@pytest.mark.parametrize("status_id", [1, 2, 3, 5])
def test_update_task_request_valid_status_id(status_id):
    """
    Given: 有効なstatus_id（1, 2, 3, 5のいずれか）
    When: UpdateTaskRequest(status_id=status_id) を作成する
    Then: バリデーションエラーなしでオブジェクトが生成される
    """
    from app.presentation.schemas.task_update import UpdateTaskRequest
    req = UpdateTaskRequest(status_id=status_id)
    assert req.status_id == status_id
```

#### TC-VAL02: UpdateTaskRequest - status_id無効値（異常系）

```python
@pytest.mark.parametrize("invalid_id", [0, 4, 6, 10, -1])
def test_update_task_request_invalid_status_id(invalid_id):
    """
    Given: 無効なstatus_id（{1,2,3,5}以外）
    When: UpdateTaskRequest(status_id=invalid_id) を作成する
    Then: ValidationError が発生する
    """
    from pydantic import ValidationError
    from app.presentation.schemas.task_update import UpdateTaskRequest

    with pytest.raises(ValidationError):
        UpdateTaskRequest(status_id=invalid_id)
```

#### TC-VAL03: UpdateTaskRequest - notesが空文字（異常系）

```python
@pytest.mark.parametrize("blank_notes", ["", "  ", "\n"])
def test_update_task_request_blank_notes(blank_notes):
    """
    Given: 空文字またはスペースのみのnotes
    When: UpdateTaskRequest(notes=blank_notes) を作成する
    Then: ValidationError が発生する
    """
    from pydantic import ValidationError
    from app.presentation.schemas.task_update import UpdateTaskRequest

    with pytest.raises(ValidationError):
        UpdateTaskRequest(notes=blank_notes)
```

#### TC-VAL04: UpdateTaskRequest - 全フィールドがNone（異常系）

```python
def test_update_task_request_no_fields():
    """
    Given: 更新フィールドが1つもない（全てNone）
    When: UpdateTaskRequest() を作成する
    Then: ValidationError が発生する
    """
    from pydantic import ValidationError
    from app.presentation.schemas.task_update import UpdateTaskRequest

    with pytest.raises(ValidationError):
        UpdateTaskRequest()
```

---

## 5. フロントエンド単体テスト設計

### 5.1 TaskUpdateConfirmation コンポーネントのテスト

**テストファイル**: `frontend/components/chat/__tests__/TaskUpdateConfirmation.test.tsx`

#### TC-FE01: ステータス更新結果の表示（正常系）

```typescript
import { render, screen } from "@testing-library/react";
import { TaskUpdateConfirmation } from "../TaskUpdateConfirmation";

describe("TaskUpdateConfirmation", () => {
  test("ステータス更新完了結果が正しく表示される", () => {
    /**
     * Given: type="status_update", issueId=123, newStatus="完了" の結果オブジェクト
     * When: TaskUpdateConfirmation コンポーネントをレンダリングする
     * Then: 「ステータス更新完了」テキストと issue ID、新しいステータスが表示される
     */
    // Given
    const result = {
      type: "status_update" as const,
      issueId: 123,
      issueTitle: "設計書作成",
      newStatus: "完了",
      redmineUrl: "http://localhost:8080/issues/123",
    };

    // When
    render(<TaskUpdateConfirmation result={result} />);

    // Then
    expect(screen.getByText("ステータス更新完了")).toBeInTheDocument();
    expect(screen.getByText(/#123 設計書作成/)).toBeInTheDocument();
    expect(screen.getByText(/完了/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Redmineで確認/ })).toHaveAttribute(
      "href",
      "http://localhost:8080/issues/123"
    );
  });

  test("コメント追加完了結果が正しく表示される", () => {
    /**
     * Given: type="comment_added" の結果オブジェクト
     * When: TaskUpdateConfirmation コンポーネントをレンダリングする
     * Then: 「コメント追加完了」テキストが表示される
     */
    const result = {
      type: "comment_added" as const,
      issueId: 45,
      issueTitle: "コードレビュー",
    };

    render(<TaskUpdateConfirmation result={result} />);

    expect(screen.getByText("コメント追加完了")).toBeInTheDocument();
    expect(screen.getByText(/#45 コードレビュー/)).toBeInTheDocument();
  });
});
```

### 5.2 ToolCallBadge コンポーネントのテスト

**テストファイル**: `frontend/components/chat/__tests__/ToolCallBadge.test.tsx`

#### TC-FE02: ツール呼び出しバッジの表示（正常系）

```typescript
describe("ToolCallBadge", () => {
  test("update_task_status ツールのバッジが正しく表示される", () => {
    /**
     * Given: name="update_task_status", status="completed" のToolCallオブジェクト
     * When: ToolCallBadge コンポーネントをレンダリングする
     * Then: 「ステータス更新」ラベルが表示される
     */
    const toolCall = {
      id: "toolu_01",
      name: "update_task_status",
      input: { issue_id: 123, status_id: 3 },
      status: "completed" as const,
    };

    render(<ToolCallBadge toolCall={toolCall} />);

    expect(screen.getByText("ステータス更新")).toBeInTheDocument();
    // 実行中のインジケータは表示されない
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
  });

  test("実行中のツール呼び出しバッジにパルスインジケータが表示される", () => {
    /**
     * Given: status="running" のToolCallオブジェクト
     * When: ToolCallBadge コンポーネントをレンダリングする
     * Then: パルスアニメーションのインジケータが表示される
     */
    const toolCall = {
      id: "toolu_02",
      name: "add_task_comment",
      input: { issue_id: 45, notes: "コメント" },
      status: "running" as const,
    };

    render(<ToolCallBadge toolCall={toolCall} />);

    expect(screen.getByText("コメント追加")).toBeInTheDocument();
    // animate-pulseクラスを持つ要素が存在する
    const indicator = document.querySelector(".animate-pulse");
    expect(indicator).toBeInTheDocument();
  });
});
```

---

## 6. テストデータ定義

### 6.1 共通テストフィクスチャ（Python）

```python
# backend/tests/conftest.py

def _make_issue_response(
    issue_id: int,
    status_id: int = 1,
    subject: str = "テストタスク",
    priority_id: int = 2,
    assigned_to_name: str = "山田 太郎",
    due_date: str | None = None,
) -> dict:
    """
    Redmine Issue APIレスポンスのテストデータを生成するヘルパー関数。
    """
    STATUS_NAMES = {1: "未着手", 2: "進行中", 3: "完了", 5: "却下"}
    PRIORITY_NAMES = {1: "低", 2: "通常", 3: "高", 4: "緊急", 5: "即座に"}

    return {
        "issue": {
            "id": issue_id,
            "subject": subject,
            "status": {"id": status_id, "name": STATUS_NAMES.get(status_id, "不明")},
            "priority": {"id": priority_id, "name": PRIORITY_NAMES.get(priority_id, "通常")},
            "assigned_to": {"id": 1, "name": assigned_to_name},
            "due_date": due_date,
            "updated_on": "2026-03-03T10:00:00Z",
        }
    }
```

### 6.2 テスト用Redmineレスポンス一覧

| データID | issue_id | status_id | subject | 用途 |
|---|---|---|---|---|
| TD-001 | 123 | 2（進行中） | 「設計書作成」 | 正常系更新テスト |
| TD-002 | 45 | 1（未着手） | 「コードレビュー」 | コメント追加テスト |
| TD-003 | 9999 | N/A | N/A | 存在しないIssueテスト（404） |
| TD-004 | 1 | 1（未着手） | 「新規タスク」 | 最小限のIssueデータ（null許容テスト） |

---

## 7. カバレッジ目標

### 7.1 バックエンドカバレッジ目標

| モジュール | 目標カバレッジ | 重点対象 |
|---|---|---|
| `TaskUpdateService` | 95%以上 | 正常系・異常系の全分岐 |
| `RedmineAdapter` | 90%以上 | リトライロジック・エラー種別 |
| `TaskStatus`（値オブジェクト） | 100% | 全ステータスIDのfrom_id・validate_id |
| `TaskPriority`（値オブジェクト） | 100% | 全優先度IDのfrom_id |
| `Task.from_redmine_response` | 95%以上 | null許容フィールドのテスト |
| `UpdateTaskRequest`（バリデーション） | 95%以上 | 全バリデーションルール |

### 7.2 フロントエンドカバレッジ目標

| コンポーネント/フック | 目標カバレッジ | 重点対象 |
|---|---|---|
| `TaskUpdateConfirmation` | 90%以上 | status_update/comment_added の両ケース |
| `ToolCallBadge` | 90%以上 | running/completed/failed の各状態 |
| `useChat`（SSEイベント処理） | 85%以上 | content_delta/tool_call/tool_result/error |

---

## 8. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-001_FEAT-003 | 本テスト設計を起点にTDDを実施する。各TCのテストコードをRed状態で実装し、Greenになるよう実装コードを作成する |
| IMP-002_FEAT-003 | フロントエンドTDD実施: TC-FE01〜TC-FE02のテストコードを先に実装する |
| IMP-005 | TDD実施中に発見したバグをTDD不具合管理票に記録する |
| IT-001_FEAT-003 | 結合テストでは本書の単体テストを発展させてRedmineスタブサーバーとの統合確認を行う |
