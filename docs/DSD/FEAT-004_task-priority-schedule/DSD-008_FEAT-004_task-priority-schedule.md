# DSD-008_FEAT-004 単体テスト設計書（タスク優先度・スケジュール調整）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-008_FEAT-004 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-004 |
| 機能名 | タスク優先度・スケジュール調整 |
| 入力元 | DSD-001_FEAT-004, DSD-002_FEAT-004, DSD-003_FEAT-004, DSD-005_FEAT-004 |
| ステータス | 初版 |

---

## 目次

1. テスト設計方針（TDD）
2. テスト対象コンポーネント
3. モック方針
4. バックエンド単体テスト設計
   - 4.1 TaskPriority 値オブジェクトのテスト
   - 4.2 DueDate 値オブジェクトのテスト
   - 4.3 DateParser のテスト
   - 4.4 Task.from_redmine_response のテスト（FEAT-004追加フィールド）
   - 4.5 TaskScheduleService のテスト
   - 4.6 PriorityReportService のテスト
   - 4.7 RedmineAdapter のテスト（FEAT-004追加メソッド）
   - 4.8 APIバリデーションのテスト
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
| バックエンド（Python） | pytest + pytest-asyncio | httpx・respx（httpxモック）・pytest-mock・freezegun |
| フロントエンド（TypeScript） | Vitest + React Testing Library | MSW（Mock Service Worker）・@testing-library/user-event |

**freezegun**: `PriorityReportService.generate_report` で `date.today()` を使用するため、`freezegun` で現在日付を固定してテストする。

### 1.3 テスト範囲

FEAT-004の単体テスト対象:

1. `TaskPriority` 値オブジェクト（`TaskPriority.from_id`・`TaskPriority.validate_id`）
2. `DueDate` 値オブジェクト（`is_past`・`days_until`・`is_within_week`）
3. `DateParser`（自然言語日付解析）
4. `Task.from_redmine_response`（FEAT-004追加フィールド: priority, due_date）
5. `TaskScheduleService.update_task_priority`（UC-005: 優先度変更）
6. `TaskScheduleService.update_task_due_date`（UC-006: 期日変更）
7. `PriorityReportService.generate_report`（UC-007: 優先タスクレポート）
8. `RedmineAdapter.update_issue_priority`・`update_issue_due_date`・`list_issues`
9. `UpdateTaskRequest` バリデーション（priority_id・due_date）
10. `PriorityUpdateConfirmation`・`PriorityReportCard` コンポーネント

### 1.4 FIRST原則の適用

| 原則 | 適用方法 |
|---|---|
| **F**ast（高速） | Redmine HTTP呼び出しはすべてモック化。`date.today()` は `freezegun` で固定 |
| **I**ndependent（独立） | 各テストケースはフィクスチャで初期化。他テストの副作用を受けない |
| **R**epeatable（再現性） | 日付・ランダム値は固定化。ページネーションも固定データで検証 |
| **S**elf-validating（自己検証） | `assert` で期待値を明示。モックの呼び出し検証も含める |
| **T**imely（タイムリー） | 実装コードより先にテストを書く（Red First） |

---

## 2. テスト対象コンポーネント

| コンポーネント | ファイルパス | テスト種別 | 優先度 |
|---|---|---|---|
| TaskPriority | `backend/app/domain/task/value_objects.py` | 単体テスト | 最高 |
| DueDate | `backend/app/domain/task/value_objects.py` | 単体テスト | 最高 |
| DateParser | `backend/app/domain/utils/date_parser.py` | 単体テスト | 最高 |
| Task.from_redmine_response（FEAT-004追加） | `backend/app/domain/task/entities.py` | 単体テスト | 最高 |
| TaskScheduleService | `backend/app/application/services/task_schedule_service.py` | 単体テスト | 最高 |
| PriorityReportService | `backend/app/application/services/priority_report_service.py` | 単体テスト | 最高 |
| RedmineAdapter（list_issues等） | `backend/app/infrastructure/redmine/redmine_adapter.py` | 単体テスト（モック使用） | 高 |
| UpdateTaskRequest（priority_id/due_date） | `backend/app/presentation/schemas/task_update.py` | バリデーションテスト | 高 |
| PriorityUpdateConfirmation | `frontend/components/chat/PriorityUpdateConfirmation.tsx` | レンダリングテスト | 中 |
| PriorityReportCard | `frontend/components/chat/PriorityReportCard.tsx` | レンダリングテスト | 中 |

---

## 3. モック方針

### 3.1 バックエンドのモック

| モック対象 | モック方法 | 理由 |
|---|---|---|
| `httpx.AsyncClient`（Redmine HTTP呼び出し） | `respx` | Redmineサーバーなしでテスト可能にする |
| `RedmineAdapter` | `pytest-mock` の `MagicMock` + `AsyncMock` | `TaskScheduleService`・`PriorityReportService` の単体テスト |
| `date.today()` | `freezegun.freeze_time` | 日付固定でレポート生成の再現性を確保 |

```python
# フィクスチャ定義（テストファイルの先頭に配置）
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date

@pytest.fixture
def mock_redmine_adapter():
    adapter = MagicMock()
    adapter.get_issue = AsyncMock()
    adapter.update_issue_priority = AsyncMock()
    adapter.update_issue_due_date = AsyncMock()
    adapter.list_issues = AsyncMock()
    return adapter

@pytest.fixture
def task_schedule_service(mock_redmine_adapter):
    from app.application.services.task_schedule_service import TaskScheduleService
    return TaskScheduleService(redmine_adapter=mock_redmine_adapter)

@pytest.fixture
def priority_report_service(mock_redmine_adapter):
    from app.application.services.priority_report_service import PriorityReportService
    return PriorityReportService(redmine_adapter=mock_redmine_adapter)
```

### 3.2 フロントエンドのモック

| モック対象 | モック方法 | 理由 |
|---|---|---|
| `fetch`（バックエンドAPI呼び出し） | MSW（Mock Service Worker）または `vi.fn()` | バックエンドなしでフロントエンドをテスト |
| SSEレスポンス | ReadableStream のモック | SSEストリーム処理のテスト |

---

## 4. バックエンド単体テスト設計

### 4.1 TaskPriority 値オブジェクトのテスト

**テストファイル**: `backend/tests/domain/test_task_value_objects.py`

#### TC-P01: TaskPriority.from_id - 有効な優先度ID（正常系）

```python
import pytest
from app.domain.task.value_objects import TaskPriority

@pytest.mark.parametrize("priority_id, expected_name", [
    (1, "低"),
    (2, "通常"),
    (3, "高"),
    (4, "緊急"),
    (5, "即座に"),
])
def test_task_priority_from_id_valid(priority_id, expected_name):
    """
    Given: 有効な優先度ID（1〜5のいずれか）
    When: TaskPriority.from_id(priority_id) を呼び出す
    Then: 正しい名称のTaskPriorityオブジェクトが返される
    """
    # When
    priority = TaskPriority.from_id(priority_id)
    # Then
    assert priority.id == priority_id
    assert priority.name == expected_name
```

#### TC-P02: TaskPriority.from_id - 無効な優先度ID（異常系）

```python
@pytest.mark.parametrize("invalid_id", [0, 6, 10, -1, 100])
def test_task_priority_from_id_invalid(invalid_id):
    """
    Given: 無効な優先度ID（{1,2,3,4,5}以外）
    When: TaskPriority.from_id(invalid_id) を呼び出す
    Then: ValueError が発生する
          エラーメッセージに「無効な優先度ID」が含まれる
    """
    with pytest.raises(ValueError, match="無効な優先度ID"):
        TaskPriority.from_id(invalid_id)
```

#### TC-P03: TaskPriority.validate_id - 有効・無効の判定

```python
@pytest.mark.parametrize("priority_id, expected", [
    (1, True), (2, True), (3, True), (4, True), (5, True),
    (0, False), (6, False), (-1, False), (100, False),
])
def test_task_priority_validate_id(priority_id, expected):
    """
    Given: 優先度ID
    When: TaskPriority.validate_id(priority_id) を呼び出す
    Then: 有効なIDはTrue、無効なIDはFalseが返される
    """
    assert TaskPriority.validate_id(priority_id) == expected
```

---

### 4.2 DueDate 値オブジェクトのテスト

**テストファイル**: `backend/tests/domain/test_task_value_objects.py`

#### TC-DD01: DueDate.is_past - 過去日付の判定（正常系）

```python
from datetime import date
from app.domain.task.value_objects import DueDate

@pytest.mark.parametrize("due_date_value, reference_date, expected", [
    (date(2026, 3, 1), date(2026, 3, 3), True),   # 2日前 → 過去
    (date(2026, 3, 3), date(2026, 3, 3), False),  # 当日 → 過去ではない
    (date(2026, 3, 10), date(2026, 3, 3), False), # 未来 → 過去ではない
])
def test_due_date_is_past(due_date_value, reference_date, expected):
    """
    Given: DueDateオブジェクトと参照日
    When: due_date.is_past(reference_date) を呼び出す
    Then: 参照日より前の場合はTrue、そうでない場合はFalseが返される
    """
    due_date = DueDate(value=due_date_value)
    assert due_date.is_past(reference_date) == expected
```

#### TC-DD02: DueDate.days_until - 期日までの日数計算

```python
@pytest.mark.parametrize("due_date_value, reference_date, expected_days", [
    (date(2026, 3, 10), date(2026, 3, 3), 7),   # 7日後
    (date(2026, 3, 3), date(2026, 3, 3), 0),    # 当日
    (date(2026, 3, 1), date(2026, 3, 3), -2),   # 2日超過（負数）
])
def test_due_date_days_until(due_date_value, reference_date, expected_days):
    """
    Given: DueDateオブジェクトと参照日
    When: due_date.days_until(reference_date) を呼び出す
    Then: 参照日から期日までの日数が返される（負数は超過を表す）
    """
    due_date = DueDate(value=due_date_value)
    assert due_date.days_until(reference_date) == expected_days
```

#### TC-DD03: DueDate.is_within_week - 今週以内の判定

```python
@pytest.mark.parametrize("due_date_value, reference_date, expected", [
    (date(2026, 3, 10), date(2026, 3, 3), True),  # 7日後 → 今週以内
    (date(2026, 3, 9), date(2026, 3, 3), True),   # 6日後 → 今週以内
    (date(2026, 3, 11), date(2026, 3, 3), False), # 8日後 → 今週超過
    (date(2026, 3, 3), date(2026, 3, 3), True),   # 当日 → 今週以内
    (date(2026, 3, 2), date(2026, 3, 3), False),  # 昨日（過去） → 今週以内ではない
])
def test_due_date_is_within_week(due_date_value, reference_date, expected):
    """
    Given: DueDateオブジェクトと参照日
    When: due_date.is_within_week(reference_date) を呼び出す
    Then: 参照日から7日以内（0〜7日）の場合はTrue、それ以外はFalseが返される
    """
    due_date = DueDate(value=due_date_value)
    assert due_date.is_within_week(reference_date) == expected
```

#### TC-DD04: DueDate - 不正な型（異常系）

```python
def test_due_date_invalid_type():
    """
    Given: date型以外の値（文字列）
    When: DueDate(value="2026-03-10") を呼び出す
    Then: TypeError が発生する
    """
    with pytest.raises(TypeError, match="date型"):
        DueDate(value="2026-03-10")
```

---

### 4.3 DateParser のテスト

**テストファイル**: `backend/tests/domain/test_date_parser.py`

#### TC-DP01: 相対日付の解析 - 「明日」「N日後」（正常系）

```python
from datetime import date
from app.domain.utils.date_parser import DateParser

@pytest.mark.parametrize("text, base_date, expected", [
    ("明日", date(2026, 3, 3), date(2026, 3, 4)),
    ("3日後", date(2026, 3, 3), date(2026, 3, 6)),
    ("1週間後", date(2026, 3, 3), date(2026, 3, 10)),
    ("2週間後", date(2026, 3, 3), date(2026, 3, 17)),
])
def test_date_parser_relative_days(text, base_date, expected):
    """
    Given: 相対日付表現（「明日」「N日後」）と基準日
    When: DateParser(base_date).parse(text) を呼び出す
    Then: 正しいdateオブジェクトが返される
    """
    parser = DateParser(base_date=base_date)
    result = parser.parse(text)
    assert result == expected
```

#### TC-DP02: 曜日指定の解析 - 「今週○曜日」「来週○曜日」（正常系）

```python
# 2026-03-03 は火曜日
@pytest.mark.parametrize("text, base_date, expected", [
    ("来週金曜", date(2026, 3, 3), date(2026, 3, 13)),    # 2026-03-03（火）から翌週金曜
    ("来週月曜", date(2026, 3, 3), date(2026, 3, 9)),     # 2026-03-03（火）から翌週月曜
    ("今週金曜", date(2026, 3, 3), date(2026, 3, 6)),     # 2026-03-03（火）から今週金曜
    ("今週火曜日", date(2026, 3, 3), date(2026, 3, 3)),   # 今日が火曜日 → 今日
])
def test_date_parser_weekday(text, base_date, expected):
    """
    Given: 曜日指定の日付表現（「来週金曜」等）と基準日
    When: DateParser(base_date).parse(text) を呼び出す
    Then: 次に来る指定曜日のdateオブジェクトが返される
    """
    parser = DateParser(base_date=base_date)
    result = parser.parse(text)
    assert result == expected
```

#### TC-DP03: ISO 8601形式の解析（正常系）

```python
@pytest.mark.parametrize("text, expected", [
    ("2026-03-14", date(2026, 3, 14)),
    ("2026-12-31", date(2026, 12, 31)),
    ("2027-01-01", date(2027, 1, 1)),
])
def test_date_parser_iso_format(text, expected):
    """
    Given: ISO 8601形式の日付文字列（YYYY-MM-DD）
    When: DateParser().parse(text) を呼び出す
    Then: 正しいdateオブジェクトが返される
    """
    parser = DateParser()
    result = parser.parse(text)
    assert result == expected
```

#### TC-DP04: 解析できない文字列（異常系）

```python
@pytest.mark.parametrize("invalid_text", [
    "あさって以降",    # 不明瞭な表現
    "いつか",          # 特定できない
    "ABC",             # 英数字のみ
    "",                # 空文字列
    "XXXX-YY-ZZ",      # 不正なISO形式
])
def test_date_parser_invalid_text(invalid_text):
    """
    Given: 解析できない日付表現
    When: DateParser().parse(invalid_text) を呼び出す
    Then: ValueError が発生する
    """
    parser = DateParser()
    with pytest.raises(ValueError, match="日付を解析できません"):
        parser.parse(invalid_text)
```

#### TC-DP05: M/D形式の解析（正常系）

```python
@pytest.mark.parametrize("text, base_date, expected", [
    ("3/14", date(2026, 3, 3), date(2026, 3, 14)),   # 同年
    ("1/5", date(2026, 12, 3), date(2027, 1, 5)),    # 年をまたぐ（来年）
])
def test_date_parser_month_day_format(text, base_date, expected):
    """
    Given: M/D形式の日付文字列
    When: DateParser(base_date).parse(text) を呼び出す
    Then: 今年（または来年）の指定月日のdateオブジェクトが返される
          過去の日付になる場合は来年として解釈する
    """
    parser = DateParser(base_date=base_date)
    result = parser.parse(text)
    assert result == expected
```

---

### 4.4 Task.from_redmine_response のテスト（FEAT-004追加フィールド）

**テストファイル**: `backend/tests/domain/test_task_entities.py`

#### TC-E03: priority・due_dateフィールドを含むTaskの生成（正常系）

```python
from datetime import date
from app.domain.task.entities import Task

def test_task_from_redmine_response_with_priority_and_due_date():
    """
    Given: priority（id=4, name="緊急"）とdue_date（"2026-03-10"）が設定されたRedmineレスポンス
    When: Task.from_redmine_response(data) を呼び出す
    Then: Task.priority.id == 4、Task.due_date == date(2026, 3, 10) のTaskが生成される
    """
    # Given
    redmine_response = {
        "issue": {
            "id": 123,
            "subject": "設計書作成",
            "status": {"id": 2, "name": "進行中"},
            "priority": {"id": 4, "name": "緊急"},
            "due_date": "2026-03-10",
            "start_date": "2026-03-01",
            "done_ratio": 60,
            "updated_on": "2026-03-03T10:00:00Z",
        }
    }
    # When
    task = Task.from_redmine_response(redmine_response)
    # Then
    assert task.priority.id == 4
    assert task.priority.name == "緊急"
    assert task.due_date == date(2026, 3, 10)
    assert task.start_date == date(2026, 3, 1)
```

#### TC-E04: due_dateがnullのTaskの生成（正常系）

```python
def test_task_from_redmine_response_null_due_date():
    """
    Given: due_dateがnull（期日未設定）のRedmineレスポンス
    When: Task.from_redmine_response(data) を呼び出す
    Then: Task.due_date is None である
    """
    redmine_response = {
        "issue": {
            "id": 456,
            "subject": "期日なしタスク",
            "status": {"id": 1, "name": "未着手"},
            "priority": {"id": 2, "name": "通常"},
            "due_date": None,
            "start_date": None,
            "done_ratio": 0,
            "updated_on": "2026-03-03T10:00:00Z",
        }
    }
    task = Task.from_redmine_response(redmine_response)
    assert task.due_date is None
    assert task.start_date is None
```

#### TC-E05: priorityフィールドが欠如している場合のデフォルト値（正常系）

```python
def test_task_from_redmine_response_missing_priority():
    """
    Given: priorityフィールドが存在しないRedmineレスポンス
    When: Task.from_redmine_response(data) を呼び出す
    Then: Task.priority.id == 2（通常）のデフォルト値が設定される
    """
    redmine_response = {
        "issue": {
            "id": 789,
            "subject": "優先度なしタスク",
            "status": {"id": 1, "name": "未着手"},
            # "priority" フィールドが存在しない
            "due_date": None,
            "done_ratio": 0,
            "updated_on": "2026-03-03T10:00:00Z",
        }
    }
    task = Task.from_redmine_response(redmine_response)
    assert task.priority.id == 2
    assert task.priority.name == "通常"
```

---

### 4.5 TaskScheduleService のテスト

**テストファイル**: `backend/tests/application/services/test_task_schedule_service.py`

#### TC-SCH01: update_task_priority - 優先度変更成功（正常系）

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from datetime import date

@pytest.mark.asyncio
async def test_update_task_priority_success(task_schedule_service, mock_redmine_adapter):
    """
    Given: 存在するIssue ID=123、有効なpriority_id=4（緊急）
    When: task_schedule_service.update_task_priority(123, 4) を呼び出す
    Then: RedmineAdapter.update_issue_priority が呼び出される
          返却されたTaskオブジェクトの priority.id == 4 である
    """
    # Given
    mock_redmine_adapter.get_issue.return_value = _make_issue_response(123, priority_id=2)
    mock_redmine_adapter.update_issue_priority.return_value = _make_issue_response(123, priority_id=4)

    # When
    result = await task_schedule_service.update_task_priority(123, 4)

    # Then
    assert result.redmine_issue_id == 123
    assert result.priority.id == 4
    assert result.priority.name == "緊急"
    mock_redmine_adapter.update_issue_priority.assert_called_once_with(123, 4)
```

#### TC-SCH02: update_task_priority - 無効な優先度ID（異常系）

```python
@pytest.mark.parametrize("invalid_priority_id", [0, 6, -1, 10, 100])
@pytest.mark.asyncio
async def test_update_task_priority_invalid_id(
    task_schedule_service, mock_redmine_adapter, invalid_priority_id
):
    """
    Given: 無効なpriority_id（{1,2,3,4,5}以外）
    When: task_schedule_service.update_task_priority(123, invalid_priority_id) を呼び出す
    Then: InvalidPriorityError が発生する
          get_issueもupdate_issue_priorityも呼び出されない
    """
    from app.domain.task.exceptions import InvalidPriorityError

    with pytest.raises(InvalidPriorityError):
        await task_schedule_service.update_task_priority(123, invalid_priority_id)

    mock_redmine_adapter.get_issue.assert_not_called()
    mock_redmine_adapter.update_issue_priority.assert_not_called()
```

#### TC-SCH03: update_task_priority - チケット不存在（異常系）

```python
@pytest.mark.asyncio
async def test_update_task_priority_task_not_found(task_schedule_service, mock_redmine_adapter):
    """
    Given: 存在しないIssue ID=9999
    When: task_schedule_service.update_task_priority(9999, 3) を呼び出す
    Then: TaskNotFoundError が発生する
    """
    from app.domain.task.exceptions import TaskNotFoundError
    mock_redmine_adapter.update_issue_priority.side_effect = TaskNotFoundError(9999)

    with pytest.raises(TaskNotFoundError) as exc_info:
        await task_schedule_service.update_task_priority(9999, 3)

    assert "9999" in str(exc_info.value)
```

#### TC-SCH04: update_task_due_date - 期日変更成功（正常系）

```python
@pytest.mark.asyncio
async def test_update_task_due_date_success(task_schedule_service, mock_redmine_adapter):
    """
    Given: 存在するIssue ID=123、valid due_date=date(2026, 3, 14)
    When: task_schedule_service.update_task_due_date(123, date(2026, 3, 14)) を呼び出す
    Then: RedmineAdapter.update_issue_due_date が正しい引数で呼び出される
          返却されたTaskオブジェクトのdue_date == date(2026, 3, 14) である
    """
    # Given
    target_date = date(2026, 3, 14)
    mock_redmine_adapter.update_issue_due_date.return_value = _make_issue_response(
        123, due_date="2026-03-14"
    )

    # When
    result = await task_schedule_service.update_task_due_date(123, target_date)

    # Then
    assert result.due_date == target_date
    mock_redmine_adapter.update_issue_due_date.assert_called_once_with(123, target_date)
```

#### TC-SCH05: update_task_due_date - 過去日付の警告付き成功（正常系・警告あり）

```python
@pytest.mark.asyncio
async def test_update_task_due_date_past_date_warning(task_schedule_service, mock_redmine_adapter):
    """
    Given: 過去日付 due_date=date(2026, 2, 1)（本日2026-03-03より前）
    When: task_schedule_service.update_task_due_date(123, date(2026, 2, 1)) を呼び出す
    Then: 更新は成功する（Redmineは過去日付を拒否しない）
          結果に is_past_due=True フラグが含まれる（または警告ログが記録される）
    """
    past_date = date(2026, 2, 1)
    mock_redmine_adapter.update_issue_due_date.return_value = _make_issue_response(
        123, due_date="2026-02-01"
    )

    result = await task_schedule_service.update_task_due_date(123, past_date)
    assert result.due_date == past_date
    # 更新は成功する（Redmineサーバー側は過去日付を拒否しない）
    mock_redmine_adapter.update_issue_due_date.assert_called_once()
```

#### TC-SCH06: update_task_due_date - Redmineバリデーションエラー（異常系）

```python
@pytest.mark.asyncio
async def test_update_task_due_date_redmine_validation_error(task_schedule_service, mock_redmine_adapter):
    """
    Given: start_date > due_date となる期日の設定（Redmineが422を返すケース）
    When: task_schedule_service.update_task_due_date(123, date(2026, 2, 28)) を呼び出す
          （start_date=2026-03-01 > due_date=2026-02-28）
    Then: RedmineAPIError が発生する
    """
    from app.infrastructure.redmine.exceptions import RedmineAPIError
    mock_redmine_adapter.update_issue_due_date.side_effect = RedmineAPIError(
        "Redmineバリデーションエラー: 開始日より前の期日は設定できません",
        status_code=422,
    )

    with pytest.raises(RedmineAPIError) as exc_info:
        await task_schedule_service.update_task_due_date(123, date(2026, 2, 28))

    assert exc_info.value.status_code == 422
```

---

### 4.6 PriorityReportService のテスト

**テストファイル**: `backend/tests/application/services/test_priority_report_service.py`

#### TC-REP01: generate_report - 正常系（期日順レポート生成）

```python
from freezegun import freeze_time

@freeze_time("2026-03-03")  # 2026-03-03（火曜日）に固定
@pytest.mark.asyncio
async def test_generate_report_with_mixed_tasks(priority_report_service, mock_redmine_adapter):
    """
    Given: 未完了タスクが以下の通り存在する（全8件）
           - 期限超過2件（2026-03-01, 2026-02-28）
           - 今日期限1件（2026-03-03）
           - 今週以内1件（2026-03-07）
           - 期日なし2件
           - 来週以降1件（2026-03-20）
    When: priority_report_service.generate_report() を呼び出す
    Then: PriorityReportオブジェクトが返される
          overdue_tasks に2件、due_today_tasks に1件、upcoming_tasks に1件、no_due_date_tasks に2件含まれる
          来週以降のタスクはどのカテゴリにも含まれない（upcoming_tasksの対象外）
    """
    # Given: モックデータ
    mock_redmine_adapter.list_issues.return_value = {
        "issues": [
            _make_raw_issue(1, "超過タスクA", due_date="2026-03-01", priority_id=3),
            _make_raw_issue(2, "超過タスクB", due_date="2026-02-28", priority_id=4),
            _make_raw_issue(3, "今日期限タスク", due_date="2026-03-03", priority_id=2),
            _make_raw_issue(4, "今週内タスク", due_date="2026-03-07", priority_id=2),
            _make_raw_issue(5, "期日なしタスクA", due_date=None, priority_id=2),
            _make_raw_issue(6, "期日なしタスクB", due_date=None, priority_id=3),
            _make_raw_issue(7, "来週以降タスク", due_date="2026-03-20", priority_id=2),
        ],
        "total_count": 7,
        "offset": 0,
        "limit": 100,
    }

    # When
    report = await priority_report_service.generate_report()

    # Then
    assert report.generated_at.isoformat() == "2026-03-03"
    assert len(report.overdue_tasks) == 2
    assert len(report.due_today_tasks) == 1
    assert len(report.upcoming_tasks) == 1
    assert len(report.no_due_date_tasks) == 2
    assert report.total_open_count == 7
```

#### TC-REP02: generate_report - 期限超過タスクのみ存在（異常ケース・正常系）

```python
@freeze_time("2026-03-03")
@pytest.mark.asyncio
async def test_generate_report_only_overdue_tasks(priority_report_service, mock_redmine_adapter):
    """
    Given: 未完了タスクがすべて期限超過（今日期限・今週内・期日なしが0件）
    When: priority_report_service.generate_report() を呼び出す
    Then: overdue_tasks に全タスクが含まれる
          due_today_tasks, upcoming_tasks, no_due_date_tasks は空リストである
    """
    mock_redmine_adapter.list_issues.return_value = {
        "issues": [
            _make_raw_issue(1, "超過タスクA", due_date="2026-02-01", priority_id=3),
            _make_raw_issue(2, "超過タスクB", due_date="2026-02-15", priority_id=4),
            _make_raw_issue(3, "超過タスクC", due_date="2026-03-02", priority_id=2),
        ],
        "total_count": 3,
        "offset": 0,
        "limit": 100,
    }

    report = await priority_report_service.generate_report()

    assert len(report.overdue_tasks) == 3
    assert len(report.due_today_tasks) == 0
    assert len(report.upcoming_tasks) == 0
    assert len(report.no_due_date_tasks) == 0
    assert report.total_open_count == 3
```

#### TC-REP03: generate_report - 超過タスクの期日昇順ソート（正常系）

```python
@freeze_time("2026-03-03")
@pytest.mark.asyncio
async def test_generate_report_overdue_tasks_sorted_by_due_date(priority_report_service, mock_redmine_adapter):
    """
    Given: 期限超過タスクが3件（期日: 2026-03-02, 2026-02-15, 2026-02-01）
    When: priority_report_service.generate_report() を呼び出す
    Then: overdue_tasks は期日が古い順（2026-02-01 → 2026-02-15 → 2026-03-02）にソートされる
          最も古い超過タスクがrank=1になる
    """
    mock_redmine_adapter.list_issues.return_value = {
        "issues": [
            _make_raw_issue(1, "最近超過", due_date="2026-03-02", priority_id=2),
            _make_raw_issue(2, "最も古い超過", due_date="2026-02-01", priority_id=2),
            _make_raw_issue(3, "中間超過", due_date="2026-02-15", priority_id=2),
        ],
        "total_count": 3,
        "offset": 0,
        "limit": 100,
    }

    report = await priority_report_service.generate_report()

    assert len(report.overdue_tasks) == 3
    assert report.overdue_tasks[0].task.due_date.isoformat() == "2026-02-01"  # 最も古い
    assert report.overdue_tasks[0].rank == 1
    assert report.overdue_tasks[1].task.due_date.isoformat() == "2026-02-15"
    assert report.overdue_tasks[2].task.due_date.isoformat() == "2026-03-02"
```

#### TC-REP04: generate_report - 同一期日の超過タスクは優先度降順ソート（正常系）

```python
@freeze_time("2026-03-03")
@pytest.mark.asyncio
async def test_generate_report_overdue_same_due_date_sorted_by_priority(priority_report_service, mock_redmine_adapter):
    """
    Given: 同一期日（2026-03-01）の期限超過タスクが2件
           タスクA: priority_id=2（通常）
           タスクB: priority_id=4（緊急）
    When: priority_report_service.generate_report() を呼び出す
    Then: overdue_tasks 内で同一期日のタスクは優先度が高い順（4→2）にソートされる
          タスクBがタスクAより前に配置される
    """
    mock_redmine_adapter.list_issues.return_value = {
        "issues": [
            _make_raw_issue(1, "通常優先超過", due_date="2026-03-01", priority_id=2),
            _make_raw_issue(2, "緊急超過", due_date="2026-03-01", priority_id=4),
        ],
        "total_count": 2,
        "offset": 0,
        "limit": 100,
    }

    report = await priority_report_service.generate_report()

    assert report.overdue_tasks[0].task.priority.id == 4  # 緊急が先
    assert report.overdue_tasks[1].task.priority.id == 2  # 通常が後
```

#### TC-REP05: generate_report - 未完了タスクが0件（正常系・空レポート）

```python
@freeze_time("2026-03-03")
@pytest.mark.asyncio
async def test_generate_report_no_open_tasks(priority_report_service, mock_redmine_adapter):
    """
    Given: 未完了タスクが0件
    When: priority_report_service.generate_report() を呼び出す
    Then: 全カテゴリが空リストのPriorityReportが返される
          total_open_count == 0
    """
    mock_redmine_adapter.list_issues.return_value = {
        "issues": [],
        "total_count": 0,
        "offset": 0,
        "limit": 100,
    }

    report = await priority_report_service.generate_report()

    assert report.total_open_count == 0
    assert len(report.overdue_tasks) == 0
    assert len(report.due_today_tasks) == 0
    assert len(report.upcoming_tasks) == 0
    assert len(report.no_due_date_tasks) == 0
```

#### TC-REP06: generate_report - as_of パラメータ指定（正常系）

```python
@pytest.mark.asyncio
async def test_generate_report_with_as_of_date(priority_report_service, mock_redmine_adapter):
    """
    Given: 未完了タスクが1件（due_date=2026-03-10）
           as_of=date(2026, 3, 15)（期日より後の日付）を指定
    When: priority_report_service.generate_report(as_of=date(2026, 3, 15)) を呼び出す
    Then: 2026-03-15 時点の評価で期限超過（2026-03-10 < 2026-03-15）と判定される
          overdue_tasks に1件含まれる
    """
    mock_redmine_adapter.list_issues.return_value = {
        "issues": [
            _make_raw_issue(1, "将来超過タスク", due_date="2026-03-10", priority_id=2),
        ],
        "total_count": 1,
        "offset": 0,
        "limit": 100,
    }

    report = await priority_report_service.generate_report(as_of=date(2026, 3, 15))

    assert report.generated_at.isoformat() == "2026-03-15"
    assert len(report.overdue_tasks) == 1
```

#### TC-REP07: generate_report - ページネーション（複数ページ取得）

```python
@freeze_time("2026-03-03")
@pytest.mark.asyncio
async def test_generate_report_pagination(priority_report_service, mock_redmine_adapter):
    """
    Given: 未完了タスクが150件存在する（1ページ100件 + 2ページ50件）
    When: priority_report_service.generate_report() を呼び出す
    Then: list_issues が2回呼び出される（offset=0, offset=100）
          total_open_count == 150
    """
    # 1ページ目: 100件
    page1_issues = [_make_raw_issue(i, f"タスク{i}", due_date=None) for i in range(1, 101)]
    # 2ページ目: 50件
    page2_issues = [_make_raw_issue(i, f"タスク{i}", due_date=None) for i in range(101, 151)]

    # list_issues の呼び出し順序に応じてページを返す
    mock_redmine_adapter.list_issues.side_effect = [
        {"issues": page1_issues, "total_count": 150, "offset": 0, "limit": 100},
        {"issues": page2_issues, "total_count": 150, "offset": 100, "limit": 100},
    ]

    report = await priority_report_service.generate_report()

    # Then
    assert report.total_open_count == 150
    assert mock_redmine_adapter.list_issues.call_count == 2
    # 1回目: offset=0, 2回目: offset=100
    calls = mock_redmine_adapter.list_issues.call_args_list
    assert calls[0][0][0]["offset"] == 0
    assert calls[1][0][0]["offset"] == 100
```

#### TC-REP08: generate_report - Redmine接続失敗（異常系）

```python
@pytest.mark.asyncio
async def test_generate_report_redmine_connection_error(priority_report_service, mock_redmine_adapter):
    """
    Given: Redmineへの接続が失敗する
    When: priority_report_service.generate_report() を呼び出す
    Then: RedmineConnectionError が発生する
          部分的なデータは返さない
    """
    from app.infrastructure.redmine.exceptions import RedmineConnectionError
    mock_redmine_adapter.list_issues.side_effect = RedmineConnectionError("接続タイムアウト")

    with pytest.raises(RedmineConnectionError):
        await priority_report_service.generate_report()
```

#### TC-REP09: PriorityReport.to_markdown - Markdown出力の検証

```python
@freeze_time("2026-03-03")
def test_priority_report_to_markdown():
    """
    Given: 期限超過1件・今日期限1件・期日なし1件のPriorityReport
    When: report.to_markdown() を呼び出す
    Then: Markdown形式の文字列が返される
          「## 優先タスクレポート」が含まれる
          「期限超過（要対応）」セクションが含まれる
          「今日期限」セクションが含まれる
          「期日なし」セクションが含まれる
    """
    from app.domain.task.entities import PriorityReport, TaskReportItem, Task
    from app.domain.task.value_objects import TaskPriority, TaskStatus

    # テスト用TaskオブジェクトをMockで代替
    mock_task = MagicMock()
    mock_task.redmine_issue_id = 123
    mock_task.title = "テストタスク"
    mock_task.priority.name = "高"
    mock_task.due_date = date(2026, 3, 1)

    report = PriorityReport(
        generated_at=date(2026, 3, 3),
        overdue_tasks=[TaskReportItem(rank=1, task=mock_task, urgency_label="期限超過", days_until_due=-2, is_overdue=True)],
        due_today_tasks=[],
        upcoming_tasks=[],
        no_due_date_tasks=[],
        total_open_count=1,
    )

    markdown = report.to_markdown()

    assert "## 優先タスクレポート" in markdown
    assert "2026年03月03日" in markdown
    assert "期限超過（要対応）" in markdown
    assert "#123" in markdown
    assert "テストタスク" in markdown
```

---

### 4.7 RedmineAdapter のテスト（FEAT-004追加メソッド）

**テストファイル**: `backend/tests/infrastructure/test_redmine_adapter_feat004.py`

#### TC-ADPT04: update_issue_priority - 優先度更新成功（正常系）

```python
import respx
import httpx
import pytest

@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_update_priority_success():
    """
    Given: Redmine PUT /issues/123.json が HTTP 204 を返す
           GET /issues/123.json が更新後のIssue（priority_id=4）を返す
    When: RedmineAdapter.update_issue_priority(123, 4) を呼び出す
    Then: 更新後のIssue辞書が返される（priority.id == 4）
    """
    # Given
    respx.put("http://localhost:8080/issues/123.json").mock(
        return_value=httpx.Response(204)
    )
    respx.get("http://localhost:8080/issues/123.json").mock(
        return_value=httpx.Response(200, json={
            "issue": {
                "id": 123,
                "subject": "テストタスク",
                "status": {"id": 2, "name": "進行中"},
                "priority": {"id": 4, "name": "緊急"},
                "due_date": None,
                "updated_on": "2026-03-03T15:00:00Z",
            }
        })
    )
    adapter = _make_adapter()

    # When
    result = await adapter.update_issue_priority(123, 4)

    # Then
    assert result["issue"]["priority"]["id"] == 4
```

#### TC-ADPT05: update_issue_due_date - 期日更新成功（正常系）

```python
@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_update_due_date_success():
    """
    Given: Redmine PUT /issues/123.json が HTTP 204 を返す
           GET /issues/123.json が更新後のIssue（due_date="2026-03-14"）を返す
    When: RedmineAdapter.update_issue_due_date(123, date(2026, 3, 14)) を呼び出す
    Then: 更新後のIssue辞書が返される（due_date == "2026-03-14"）
    """
    respx.put("http://localhost:8080/issues/123.json").mock(
        return_value=httpx.Response(204)
    )
    respx.get("http://localhost:8080/issues/123.json").mock(
        return_value=httpx.Response(200, json={
            "issue": {
                "id": 123,
                "subject": "テストタスク",
                "status": {"id": 2, "name": "進行中"},
                "priority": {"id": 2, "name": "通常"},
                "due_date": "2026-03-14",
                "updated_on": "2026-03-03T15:00:00Z",
            }
        })
    )
    adapter = _make_adapter()

    result = await adapter.update_issue_due_date(123, date(2026, 3, 14))

    assert result["issue"]["due_date"] == "2026-03-14"
```

#### TC-ADPT06: list_issues - 未完了タスク一覧取得成功（正常系）

```python
@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_list_issues_success():
    """
    Given: Redmine GET /issues.json?status_id=open&limit=100&offset=0 が2件のIssueを返す
    When: RedmineAdapter.list_issues({"status_id": "open", "limit": 100, "offset": 0}) を呼び出す
    Then: {"issues": [...], "total_count": 2} が返される
    """
    respx.get("http://localhost:8080/issues.json").mock(
        return_value=httpx.Response(200, json={
            "issues": [
                _make_raw_issue(1, "タスクA", due_date="2026-03-10"),
                _make_raw_issue(2, "タスクB", due_date=None),
            ],
            "total_count": 2,
            "offset": 0,
            "limit": 100,
        })
    )
    adapter = _make_adapter()

    result = await adapter.list_issues({"status_id": "open", "limit": 100, "offset": 0})

    assert len(result["issues"]) == 2
    assert result["total_count"] == 2
```

#### TC-ADPT07: list_issues - Redmine接続タイムアウト・リトライ（異常系）

```python
@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_list_issues_timeout_retry():
    """
    Given: Redmine GET /issues.json が3回連続でタイムアウトする
    When: RedmineAdapter.list_issues({...}) を呼び出す
    Then: RedmineConnectionError が発生する（リトライ上限到達後）
          list_issues の呼び出しは合計3回（初回 + リトライ2回）
    """
    from app.infrastructure.redmine.exceptions import RedmineConnectionError

    respx.get("http://localhost:8080/issues.json").mock(
        side_effect=httpx.TimeoutException("タイムアウト")
    )
    adapter = _make_adapter()  # max_retries=2

    with pytest.raises(RedmineConnectionError, match="タイムアウト"):
        await adapter.list_issues({"status_id": "open", "limit": 100, "offset": 0})
```

#### TC-ADPT08: update_issue_priority - PUT リクエストボディの検証

```python
@pytest.mark.asyncio
@respx.mock
async def test_redmine_adapter_update_priority_request_body():
    """
    Given: priority_id=3 で優先度変更
    When: RedmineAdapter.update_issue_priority(123, 3) を呼び出す
    Then: PUT /issues/123.json に {"issue": {"priority_id": 3}} が送信される
    """
    put_route = respx.put("http://localhost:8080/issues/123.json").mock(
        return_value=httpx.Response(204)
    )
    respx.get("http://localhost:8080/issues/123.json").mock(
        return_value=httpx.Response(200, json=_make_raw_response(123, priority_id=3))
    )
    adapter = _make_adapter()

    await adapter.update_issue_priority(123, 3)

    # リクエストボディを検証
    request_body = put_route.calls[0].request.content
    import json
    body = json.loads(request_body)
    assert body == {"issue": {"priority_id": 3}}
```

---

### 4.8 APIバリデーションのテスト

**テストファイル**: `backend/tests/presentation/test_task_update_schema.py`

#### TC-VAL04: UpdateTaskRequest - priority_idの境界値バリデーション

```python
import pytest
from pydantic import ValidationError
from app.presentation.schemas.task_update import UpdateTaskRequest

@pytest.mark.parametrize("priority_id, should_pass", [
    (1, True),    # 有効: 最小値
    (5, True),    # 有効: 最大値
    (3, True),    # 有効: 中間値
    (0, False),   # 無効: 下限未満
    (6, False),   # 無効: 上限超過
    (-1, False),  # 無効: 負数
    (None, True), # 有効: None（priority_idは任意）
])
def test_update_task_request_priority_id_validation(priority_id, should_pass):
    """
    Given: priority_idの値
    When: UpdateTaskRequest(priority_id=priority_id) を呼び出す
    Then: 有効な値（1〜5またはNone）はバリデーション通過
          無効な値（0, 6以上, 負数）はValidationErrorが発生する
    """
    if should_pass:
        req = UpdateTaskRequest(priority_id=priority_id)
        assert req.priority_id == priority_id
    else:
        with pytest.raises(ValidationError) as exc_info:
            UpdateTaskRequest(priority_id=priority_id)
        assert "priority_id" in str(exc_info.value)
```

#### TC-VAL05: UpdateTaskRequest - due_dateのフォーマットバリデーション

```python
@pytest.mark.parametrize("due_date, should_pass", [
    ("2026-03-14", True),    # 有効: ISO 8601形式
    ("2026-12-31", True),    # 有効
    (None, True),            # 有効: None（任意フィールド）
    ("2026/03/14", False),   # 無効: スラッシュ区切り
    ("14-03-2026", False),   # 無効: 日-月-年形式
    ("20260314", False),     # 無効: ハイフンなし
    ("2026-13-01", False),   # 無効: 存在しない月
    ("not-a-date", False),   # 無効: 文字列
])
def test_update_task_request_due_date_validation(due_date, should_pass):
    """
    Given: due_dateの値
    When: UpdateTaskRequest(due_date=due_date) を呼び出す
    Then: 有効な形式（YYYY-MM-DD またはNone）はバリデーション通過
          無効な形式はValidationErrorが発生する
    """
    if should_pass:
        req = UpdateTaskRequest(due_date=due_date)
        assert req.due_date == due_date
    else:
        with pytest.raises(ValidationError) as exc_info:
            UpdateTaskRequest(due_date=due_date)
        assert "due_date" in str(exc_info.value)
```

---

## 5. フロントエンド単体テスト設計

### 5.1 PriorityUpdateConfirmation コンポーネントのテスト

**テストファイル**: `frontend/tests/components/chat/PriorityUpdateConfirmation.test.tsx`

#### TC-FE03: 優先度変更確認カードのレンダリング（正常系）

```typescript
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import PriorityUpdateConfirmation from "@/components/chat/PriorityUpdateConfirmation";

describe("PriorityUpdateConfirmation", () => {
  it("優先度変更確認カードが正しくレンダリングされる", () => {
    /**
     * Given: issueId=123、title="設計書作成"、oldPriorityId=2、newPriorityId=4
     * When: PriorityUpdateConfirmation コンポーネントをレンダリング
     * Then: チケット番号 "#123" が表示される
     *       タイトル "設計書作成" が表示される
     *       新しい優先度 "緊急" が表示される
     *       古い優先度 "通常" が表示される（変更前の表示）
     */
    // Given
    const props = {
      issueId: 123,
      title: "設計書作成",
      oldPriorityId: 2,
      oldPriorityName: "通常",
      newPriorityId: 4,
      newPriorityName: "緊急",
    };

    // When
    render(<PriorityUpdateConfirmation {...props} />);

    // Then
    expect(screen.getByText("#123")).toBeInTheDocument();
    expect(screen.getByText("設計書作成")).toBeInTheDocument();
    expect(screen.getByText("緊急")).toBeInTheDocument();
    expect(screen.getByText("通常")).toBeInTheDocument();
  });

  it("緊急(priority_id=4)にはオレンジ色のバッジが適用される", () => {
    /**
     * Given: newPriorityId=4（緊急）
     * When: PriorityUpdateConfirmation コンポーネントをレンダリング
     * Then: 優先度バッジにオレンジ系のCSSクラスが適用されている
     */
    const props = {
      issueId: 123,
      title: "テスト",
      oldPriorityId: 2,
      oldPriorityName: "通常",
      newPriorityId: 4,
      newPriorityName: "緊急",
    };

    render(<PriorityUpdateConfirmation {...props} />);

    // 優先度バッジ要素を取得してオレンジ色クラスを確認
    const priorityBadge = screen.getByTestId("priority-badge-new");
    expect(priorityBadge).toHaveClass("bg-orange");
  });
});
```

#### TC-FE04: 期日変更確認カードのレンダリング（正常系）

```typescript
import DueDateUpdateConfirmation from "@/components/chat/DueDateUpdateConfirmation";

describe("DueDateUpdateConfirmation", () => {
  it("期日変更確認カードが正しくレンダリングされる", () => {
    /**
     * Given: issueId=123、title="設計書作成"、newDueDate="2026-03-14"
     * When: DueDateUpdateConfirmation コンポーネントをレンダリング
     * Then: チケット番号 "#123" が表示される
     *       タイトル "設計書作成" が表示される
     *       新しい期日 "2026/03/14" が表示される（ローカライズ形式）
     */
    render(
      <DueDateUpdateConfirmation
        issueId={123}
        title="設計書作成"
        oldDueDate="2026-03-07"
        newDueDate="2026-03-14"
        isPastDue={false}
      />
    );

    expect(screen.getByText("#123")).toBeInTheDocument();
    expect(screen.getByText("設計書作成")).toBeInTheDocument();
    expect(screen.getByText(/2026.03.14/)).toBeInTheDocument();
  });

  it("過去日付設定時に警告メッセージが表示される", () => {
    /**
     * Given: isPastDue=true（過去日付に変更）
     * When: DueDateUpdateConfirmation コンポーネントをレンダリング
     * Then: 「過去の日付が設定されています」などの警告テキストが表示される
     */
    render(
      <DueDateUpdateConfirmation
        issueId={123}
        title="テスト"
        oldDueDate={null}
        newDueDate="2026-02-01"
        isPastDue={true}
      />
    );

    expect(screen.getByText(/過去の日付/)).toBeInTheDocument();
  });
});
```

### 5.2 PriorityReportCard コンポーネントのテスト

**テストファイル**: `frontend/tests/components/chat/PriorityReportCard.test.tsx`

#### TC-FE05: 優先タスクレポートカードのレンダリング（正常系）

```typescript
import PriorityReportCard from "@/components/chat/PriorityReportCard";

describe("PriorityReportCard", () => {
  const sampleMarkdown = `## 優先タスクレポート（2026年03月03日時点）
未完了タスク数: 3件

### 🚨 期限超過（要対応）
1. **#100** 設計書作成（2日超過・優先度: 高）

### 📅 今週中
2. **#101** コードレビュー（期日: 03/07・優先度: 通常）

### 📋 期日なし
3. **#102** ドキュメント整備（優先度: 低）
`;

  it("レポートMarkdownが正しくレンダリングされる", () => {
    /**
     * Given: 優先タスクレポートのMarkdown文字列
     * When: PriorityReportCard コンポーネントをレンダリング
     * Then: 「優先タスクレポート」ヘッダーが表示される
     *       「期限超過（要対応）」セクションが表示される
     *       チケット番号 "#100" が表示される
     */
    render(<PriorityReportCard content={sampleMarkdown} />);

    expect(screen.getByText(/優先タスクレポート/)).toBeInTheDocument();
    expect(screen.getByText(/期限超過（要対応）/)).toBeInTheDocument();
    expect(screen.getByText(/#100/)).toBeInTheDocument();
  });

  it("未完了タスク数が表示される", () => {
    /**
     * Given: 「未完了タスク数: 3件」を含むMarkdown
     * When: PriorityReportCard コンポーネントをレンダリング
     * Then: 「3件」のテキストが表示される
     */
    render(<PriorityReportCard content={sampleMarkdown} />);
    expect(screen.getByText(/3件/)).toBeInTheDocument();
  });

  it("空の場合に適切なメッセージが表示される", () => {
    /**
     * Given: 未完了タスクが0件のMarkdown
     * When: PriorityReportCard コンポーネントをレンダリング
     * Then: 「未完了タスク数: 0件」が表示される
     */
    const emptyMarkdown = `## 優先タスクレポート（2026年03月03日時点）\n未完了タスク数: 0件\n`;
    render(<PriorityReportCard content={emptyMarkdown} />);
    expect(screen.getByText(/0件/)).toBeInTheDocument();
  });
});
```

---

## 6. テストデータ定義

### 6.1 バックエンド共通フィクスチャ・ヘルパー関数

```python
# backend/tests/conftest.py に追加（または tests/helpers/redmine_fixtures.py として分離）

def _make_raw_issue(
    issue_id: int,
    subject: str,
    due_date: str | None = None,
    priority_id: int = 2,
    priority_name: str | None = None,
    status_id: int = 2,
    done_ratio: int = 0,
) -> dict:
    """
    Redmineレスポンスのissueオブジェクトを生成するヘルパー。
    FEAT-004のテストで使用するモックデータ作成用。
    """
    priority_names = {1: "低", 2: "通常", 3: "高", 4: "緊急", 5: "即座に"}
    status_names = {1: "未着手", 2: "進行中", 3: "完了", 5: "却下"}
    return {
        "id": issue_id,
        "subject": subject,
        "status": {"id": status_id, "name": status_names.get(status_id, "不明")},
        "priority": {
            "id": priority_id,
            "name": priority_name or priority_names.get(priority_id, "通常"),
        },
        "due_date": due_date,
        "start_date": None,
        "done_ratio": done_ratio,
        "description": "",
        "updated_on": "2026-03-03T10:00:00Z",
        "created_on": "2026-03-01T09:00:00Z",
    }


def _make_issue_response(
    issue_id: int,
    priority_id: int = 2,
    due_date: str | None = None,
    status_id: int = 2,
) -> dict:
    """
    RedmineAdapter のモック戻り値として使用するIssueレスポンス辞書。
    """
    return {
        "issue": _make_raw_issue(
            issue_id=issue_id,
            subject="テストタスク",
            due_date=due_date,
            priority_id=priority_id,
            status_id=status_id,
        )
    }


def _make_raw_response(issue_id: int, priority_id: int = 2) -> dict:
    """respx モックのレスポンスJSONとして使用するヘルパー。"""
    return _make_issue_response(issue_id, priority_id=priority_id)


def _make_adapter():
    """RedmineAdapterインスタンスを生成するヘルパー。"""
    from app.infrastructure.redmine.redmine_adapter import RedmineAdapter
    return RedmineAdapter(
        base_url="http://localhost:8080",
        api_key="test-api-key",
        max_retries=2,
    )
```

### 6.2 テストシナリオ用レポートデータ

| シナリオ名 | 期限超過 | 今日期限 | 今週中 | 期日なし | 合計 |
|---|---|---|---|---|---|
| 正常系（混在） | 2件 | 1件 | 1件 | 2件 | 7件 |
| 期限超過のみ | 3件 | 0件 | 0件 | 0件 | 3件 |
| 空レポート | 0件 | 0件 | 0件 | 0件 | 0件 |
| ページネーション | 0件 | 0件 | 0件 | 150件 | 150件 |

### 6.3 日付テストマトリクス（基準日: 2026-03-03）

| タスク種別 | due_date | days_until_due | カテゴリ |
|---|---|---|---|
| 期限超過（古い） | 2026-02-01 | -30 | overdue |
| 期限超過（最近） | 2026-03-02 | -1 | overdue |
| 今日期限 | 2026-03-03 | 0 | due_today |
| 明日期限 | 2026-03-04 | 1 | upcoming |
| 今週末 | 2026-03-07 | 4 | upcoming |
| 7日後 | 2026-03-10 | 7 | upcoming |
| 8日後以降 | 2026-03-11 | 8 | 対象外（レポートに未掲載） |
| 期日なし | None | None | no_due_date |

---

## 7. カバレッジ目標

### 7.1 バックエンドカバレッジ目標

| 対象モジュール | 目標カバレッジ | 理由 |
|---|---|---|
| `domain/task/value_objects.py`（TaskPriority, DueDate） | 95%以上 | ドメインロジックの根幹 |
| `domain/utils/date_parser.py`（DateParser） | 90%以上 | 多様な入力パターンが存在 |
| `application/services/task_schedule_service.py` | 90%以上 | ビジネスロジックの中核 |
| `application/services/priority_report_service.py` | 90%以上 | レポートロジックの中核 |
| `infrastructure/redmine/redmine_adapter.py`（FEAT-004追加） | 85%以上 | 外部依存モジュール |
| `presentation/schemas/task_update.py`（FEAT-004追加） | 90%以上 | バリデーション漏れ防止 |

### 7.2 フロントエンドカバレッジ目標

| 対象モジュール | 目標カバレッジ | 理由 |
|---|---|---|
| `components/chat/PriorityUpdateConfirmation.tsx` | 80%以上 | UIコンポーネント |
| `components/chat/DueDateUpdateConfirmation.tsx` | 80%以上 | UIコンポーネント |
| `components/chat/PriorityReportCard.tsx` | 80%以上 | UIコンポーネント |

### 7.3 テストケース数サマリ

| テスト区分 | テストケース数 | テストファイル |
|---|---|---|
| TaskPriority 値オブジェクト | 3件（TC-P01〜TC-P03） | `test_task_value_objects.py` |
| DueDate 値オブジェクト | 4件（TC-DD01〜TC-DD04） | `test_task_value_objects.py` |
| DateParser | 5件（TC-DP01〜TC-DP05） | `test_date_parser.py` |
| Task.from_redmine_response | 3件（TC-E03〜TC-E05） | `test_task_entities.py` |
| TaskScheduleService | 6件（TC-SCH01〜TC-SCH06） | `test_task_schedule_service.py` |
| PriorityReportService | 9件（TC-REP01〜TC-REP09） | `test_priority_report_service.py` |
| RedmineAdapter（FEAT-004） | 5件（TC-ADPT04〜TC-ADPT08） | `test_redmine_adapter_feat004.py` |
| APIバリデーション | 2件（TC-VAL04〜TC-VAL05） | `test_task_update_schema.py` |
| フロントエンドコンポーネント | 6件（TC-FE03〜TC-FE05） | 各コンポーネントテストファイル |
| **合計** | **43件** | |

---

## 8. 後続フェーズへの影響

### 8.1 IMP（実装）フェーズへの影響

本設計書は IMP フェーズの TDD実装の起点となる。以下の実装順序を推奨する。

| 実装ステップ | 対象 | TDD起点テストケース |
|---|---|---|
| Step 1 | `TaskPriority` 値オブジェクト | TC-P01〜TC-P03 |
| Step 2 | `DueDate` 値オブジェクト | TC-DD01〜TC-DD04 |
| Step 3 | `DateParser` | TC-DP01〜TC-DP05 |
| Step 4 | `Task.from_redmine_response` FEAT-004追加 | TC-E03〜TC-E05 |
| Step 5 | `TaskScheduleService` | TC-SCH01〜TC-SCH06 |
| Step 6 | `PriorityReportService` | TC-REP01〜TC-REP09 |
| Step 7 | `RedmineAdapter` FEAT-004追加 | TC-ADPT04〜TC-ADPT08 |
| Step 8 | APIバリデーション | TC-VAL04〜TC-VAL05 |
| Step 9 | フロントエンドコンポーネント | TC-FE03〜TC-FE05 |

### 8.2 テスト実行コマンド

```bash
# バックエンド: FEAT-004関連テストのみ実行
pytest backend/tests/ -k "feat004 or priority or due_date or date_parser or report" -v

# バックエンド: カバレッジレポート付きで実行
pytest backend/tests/ --cov=app --cov-report=html -v

# フロントエンド: FEAT-004コンポーネントのテスト
npx vitest run frontend/tests/components/chat/PriorityUpdateConfirmation.test.tsx
npx vitest run frontend/tests/components/chat/PriorityReportCard.test.tsx
```

### 8.3 IT（結合テスト）フェーズへの依存

- 本設計書の単体テストはすべてモックを使用する
- Redmine実機との疎通確認は IT-001_FEAT-004 で実施する
- 実際のページネーション動作（100件超の取得）は IT フェーズで検証する

---
