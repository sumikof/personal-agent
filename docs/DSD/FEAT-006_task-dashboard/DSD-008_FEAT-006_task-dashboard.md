# DSD-008_FEAT-006 単体テスト設計書（タスク一覧ダッシュボード）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-008_FEAT-006 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-006 |
| 機能名 | タスク一覧ダッシュボード（task-dashboard） |
| 入力元 | DSD-001_FEAT-006, DSD-002_FEAT-006, DSD-003_FEAT-006 |
| ステータス | 初版 |

---

## 目次

1. テスト設計方針
2. テスト対象コンポーネント
3. モック方針
4. バックエンドテストケース
5. フロントエンドテストケース
6. テスト実行環境
7. カバレッジ目標
8. 後続フェーズへの影響

---

## 1. テスト設計方針

### 1.1 TDD方針

FEAT-005と同様に、本設計書を起点としたTDD（Red → Green → Refactor）サイクルで実装する。

| フェーズ | 説明 |
|---|---|
| Red | 本設計書のテストケースをコードに落とし込む。すべて失敗することを確認する |
| Green | テストが通る最小限の実装を行う |
| Refactor | コードの品質・可読性を改善する |

### 1.2 テストレベル

| テストレベル | 対象 | 本書の対象 |
|---|---|---|
| 単体テスト（UT） | クラス・関数単位のテスト | ○（本書） |
| 結合テスト（IT） | API〜Redmine連携テスト | × （IT-001_FEAT-006） |

### 1.3 テストフレームワーク

FEAT-005のDSD-008と同じフレームワークを使用する。

| 領域 | フレームワーク | 補助ライブラリ |
|---|---|---|
| バックエンド（Python） | pytest + pytest-asyncio | pytest-mock, faker |
| フロントエンド（TypeScript） | Vitest + Testing Library | @testing-library/react, msw |

---

## 2. テスト対象コンポーネント

### 2.1 バックエンドテスト対象

| テスト対象 | クラス/モジュール | テストファイル |
|---|---|---|
| タスクダッシュボードサービス | `TaskDashboardService` | `tests/task/test_task_dashboard_service.py` |
| Redmineアダプター | `RedmineAdapter` | `tests/task/test_redmine_adapter.py` |
| 期日チェックロジック | `TaskUrgency.from_due_date` | `tests/task/test_task_urgency.py` |
| タスクデータ変換 | `RedmineAdapter.to_task_summary` | `tests/task/test_redmine_adapter.py` |
| ステータスグルーピング | `TaskDashboardService.get_tasks_grouped` | `tests/task/test_task_dashboard_service.py` |
| APIルーター | `TaskRouter` | `tests/task/test_task_router.py` |

### 2.2 フロントエンドテスト対象

| テスト対象 | コンポーネント/フック | テストファイル |
|---|---|---|
| タスクカード | `TaskCard` | `src/components/dashboard/__tests__/TaskCard.test.tsx` |
| タスクステータスカラム | `TaskStatusColumn` | `src/components/dashboard/__tests__/TaskStatusColumn.test.tsx` |
| タスクバッジ | `TaskBadge` | `src/components/dashboard/__tests__/TaskBadge.test.tsx` |
| タスクサマリー統計 | `TaskSummaryStats` | `src/components/dashboard/__tests__/TaskSummaryStats.test.tsx` |
| タスク管理フック | `useTasks` | `src/hooks/__tests__/useTasks.test.ts` |

---

## 3. モック方針

### 3.1 バックエンドモック

| モック対象 | モック方法 | 理由 |
|---|---|---|
| `RedmineMCPClient` | `pytest-mock`で`get_issues`をモック | 外部Redmineサーバ依存排除 |
| `date.today()` | `unittest.mock.patch`で固定日付を返す | テスト結果の再現性確保（期日チェックが日付依存） |

**日付のモック方法:**

```python
# tests/task/test_task_urgency.py
from unittest.mock import patch
from datetime import date

def test_urgency_overdue():
    # 今日を2026-03-03に固定
    with patch('app.task.domain.models.date') as mock_date:
        mock_date.today.return_value = date(2026, 3, 3)
        mock_date.fromisoformat = date.fromisoformat

        urgency = TaskUrgency.from_due_date("2026-03-01", date(2026, 3, 3))
        assert urgency == TaskUrgency.OVERDUE
```

より安全な方法として、`TaskUrgency.from_due_date` の引数として `today` を明示的に渡す設計とすることで、モック不要にする（DSD-001で採用済み）。

```python
# today を引数として受け取るため、モック不要
urgency = TaskUrgency.from_due_date("2026-03-01", today=date(2026, 3, 3))
```

### 3.2 フロントエンドモック

| モック対象 | モック方法 | 理由 |
|---|---|---|
| GET /api/v1/tasks | MSW（Mock Service Worker） | バックエンドAPI依存排除 |
| `Date.now()` | `vi.setSystemTime()` | 期日表示のテストを日付固定で実行 |

---

## 4. バックエンドテストケース

### 4.1 TaskUrgency.from_due_dateテスト（期日チェックロジック）

#### TC-BE-U001: 期限超過（異常系・due_date < today）

```
Given: today = 2026-03-03
When: TaskUrgency.from_due_date("2026-03-01", today=date(2026, 3, 3)) を呼び出す
Then: TaskUrgency.OVERDUE が返される（urgency = "overdue"）
```

```python
from datetime import date
import pytest
from app.task.domain.models import TaskUrgency

class TestTaskUrgency:

    def test_overdue(self):
        # Given
        today = date(2026, 3, 3)
        due_date_str = "2026-03-01"  # 2日前

        # When
        result = TaskUrgency.from_due_date(due_date_str, today)

        # Then
        assert result == TaskUrgency.OVERDUE
        assert result.value == "overdue"
```

#### TC-BE-U002: 当日（高緊急度）

```
Given: today = 2026-03-03
When: TaskUrgency.from_due_date("2026-03-03", today=date(2026, 3, 3)) を呼び出す
Then: TaskUrgency.HIGH が返される（当日 = days_diff=0 → high）
```

#### TC-BE-U003: 1日後（高緊急度）

```
Given: today = 2026-03-03
When: TaskUrgency.from_due_date("2026-03-04", today=date(2026, 3, 3)) を呼び出す
Then: TaskUrgency.HIGH が返される（days_diff=1）
```

#### TC-BE-U004: 3日後（高緊急度の境界値）

```
Given: today = 2026-03-03
When: TaskUrgency.from_due_date("2026-03-06", today=date(2026, 3, 3)) を呼び出す
Then: TaskUrgency.HIGH が返される（days_diff=3 ← 高緊急度の上限）
```

```python
def test_high_urgency_boundary_3days(self):
    today = date(2026, 3, 3)
    result = TaskUrgency.from_due_date("2026-03-06", today)
    assert result == TaskUrgency.HIGH  # 3日後は high
```

#### TC-BE-U005: 4日後（中緊急度の境界値）

```
Given: today = 2026-03-03
When: TaskUrgency.from_due_date("2026-03-07", today=date(2026, 3, 3)) を呼び出す
Then: TaskUrgency.MEDIUM が返される（days_diff=4 ← 中緊急度の開始）
```

```python
def test_medium_urgency_boundary_4days(self):
    today = date(2026, 3, 3)
    result = TaskUrgency.from_due_date("2026-03-07", today)
    assert result == TaskUrgency.MEDIUM  # 4日後は medium
```

#### TC-BE-U006: 7日後（中緊急度の上限境界値）

```
Given: today = 2026-03-03
When: TaskUrgency.from_due_date("2026-03-10", today=date(2026, 3, 3)) を呼び出す
Then: TaskUrgency.MEDIUM が返される（days_diff=7 ← 中緊急度の上限）
```

#### TC-BE-U007: 8日後（通常緊急度の境界値）

```
Given: today = 2026-03-03
When: TaskUrgency.from_due_date("2026-03-11", today=date(2026, 3, 3)) を呼び出す
Then: TaskUrgency.NORMAL が返される（days_diff=8 ← 通常の開始）
```

#### TC-BE-U008: 期日なし（通常緊急度）

```
Given: today = 2026-03-03
When: TaskUrgency.from_due_date(None, today=date(2026, 3, 3)) を呼び出す
Then: TaskUrgency.NORMAL が返される
```

```python
def test_no_due_date_returns_normal(self):
    today = date(2026, 3, 3)
    result = TaskUrgency.from_due_date(None, today)
    assert result == TaskUrgency.NORMAL
```

#### TC-BE-U009: 不正な日付フォーマット（異常系）

```
Given: today = 2026-03-03
When: TaskUrgency.from_due_date("2026/03/01", today=date(2026, 3, 3)) を呼び出す
      （ハイフン区切りでなくスラッシュ区切りの場合）
Then: TaskUrgency.NORMAL が返される（例外を raise しない）
```

```python
def test_invalid_date_format_returns_normal(self):
    today = date(2026, 3, 3)
    result = TaskUrgency.from_due_date("2026/03/01", today)  # 不正フォーマット
    assert result == TaskUrgency.NORMAL  # 例外なし・normalを返す
```

### 4.2 RedmineAdapterテスト（タスクデータ変換ロジック）

#### TC-BE-A001: 完全なIssueデータの変換（正常系）

```
Given: 全フィールドが揃ったRedmine Issue JSON
When: RedmineAdapter.to_task_summary(issue, today=date(2026, 3, 3)) を呼び出す
Then:
  - task.id == 123
  - task.title == "API基本設計書の作成"
  - task.status == "in_progress"
  - task.status_label == "進行中"
  - task.priority == "high"
  - task.priority_label == "高"
  - task.assignee_name == "山田 太郎"
  - task.due_date == "2026-03-06"
  - task.urgency == "high"（today=3/3, due_date=3/6 → days_diff=3 → high）
  - task.redmine_url == "http://localhost:8080/issues/123"
```

```python
from datetime import date
from app.task.domain.adapters import RedmineAdapter

class TestRedmineAdapter:

    def setup_method(self):
        self.adapter = RedmineAdapter()
        self.today = date(2026, 3, 3)

    def test_to_task_summary_full_issue(self):
        # Given
        issue = {
            "id": 123,
            "subject": "API基本設計書の作成",
            "status": {"id": 2, "name": "In Progress"},
            "priority": {"id": 3, "name": "High"},
            "assigned_to": {"id": 1, "name": "山田 太郎"},
            "due_date": "2026-03-06",
            "created_on": "2026-03-01T09:00:00Z",
            "updated_on": "2026-03-03T10:00:00Z",
        }

        # When
        result = self.adapter.to_task_summary(issue, self.today)

        # Then
        assert result.id == 123
        assert result.title == "API基本設計書の作成"
        assert result.status == "in_progress"
        assert result.status_label == "進行中"
        assert result.priority == "high"
        assert result.priority_label == "高"
        assert result.assignee_name == "山田 太郎"
        assert result.due_date == "2026-03-06"
        assert result.urgency == "high"
        assert "localhost:8080/issues/123" in result.redmine_url
```

#### TC-BE-A002: 担当者なしのIssue変換（正常系）

```
Given: assigned_to が null の Redmine Issue JSON
When: RedmineAdapter.to_task_summary(issue, today) を呼び出す
Then: task.assignee_name == None
```

```python
def test_to_task_summary_no_assignee(self):
    issue = {
        "id": 124,
        "subject": "担当者なしタスク",
        "status": {"id": 1, "name": "New"},
        "priority": {"id": 2, "name": "Normal"},
        "assigned_to": None,  # 担当者なし
        "due_date": None,
        "created_on": "2026-03-02T14:00:00Z",
        "updated_on": "2026-03-03T09:00:00Z",
    }

    result = self.adapter.to_task_summary(issue, self.today)

    assert result.assignee_name is None
```

#### TC-BE-A003: 期日なしのIssue変換（正常系）

```
Given: due_date が null の Redmine Issue JSON
When: RedmineAdapter.to_task_summary(issue, today) を呼び出す
Then:
  - task.due_date == None
  - task.urgency == "normal"
```

#### TC-BE-A004: 未知のステータス名の変換（正常系）

```
Given: status.name が "Testing"（マッピング外）の Redmine Issue JSON
When: RedmineAdapter.to_task_summary(issue, today) を呼び出す
Then:
  - task.status == "testing"（小文字変換）
  - task.status_label == "Testing"（英語のまま）
```

#### TC-BE-A005: 複数Issue一括変換（正常系）

```
Given: 3件のRedmine Issue JSONリスト
When: RedmineAdapter.to_task_summaries(issues, today) を呼び出す
Then:
  - 3件のTaskSummaryリストが返される
  - 各要素のfieldが正しく変換されている
```

```python
def test_to_task_summaries_multiple(self):
    issues = [
        {
            "id": i,
            "subject": f"タスク{i}",
            "status": {"id": 1, "name": "New"},
            "priority": {"id": 2, "name": "Normal"},
            "assigned_to": None,
            "due_date": None,
            "created_on": "2026-03-01T09:00:00Z",
            "updated_on": "2026-03-01T09:00:00Z",
        }
        for i in range(1, 4)
    ]

    results = self.adapter.to_task_summaries(issues, self.today)

    assert len(results) == 3
    assert results[0].id == 1
    assert results[1].id == 2
    assert results[2].id == 3
```

### 4.3 TaskDashboardServiceテスト

#### TC-BE-S001: タスク一覧取得（正常系・全件）

```
Given:
  - RedmineMCPClientが3件のIssueを返すようにモック済み（total_count=3）
  - today = 2026-03-03
When: TaskDashboardService.get_tasks() を呼び出す
Then:
  - 3件のTaskSummaryリストが返される
  - urgencyの優先度順（overdue → high → medium → normal）にソートされている
```

```python
@pytest.mark.asyncio
async def test_get_tasks_returns_sorted_tasks(
    task_dashboard_service: TaskDashboardService,
    mock_redmine_client: MagicMock,
):
    # Given: 3件のモックデータ（urgency がバラバラ）
    mock_redmine_client.get_issues = AsyncMock(return_value={
        "issues": [
            {
                "id": 1, "subject": "通常タスク",
                "status": {"id": 2, "name": "In Progress"},
                "priority": {"id": 2, "name": "Normal"},
                "assigned_to": None, "due_date": "2026-03-20",  # normal
                "created_on": "2026-03-01T09:00:00Z",
                "updated_on": "2026-03-01T09:00:00Z",
            },
            {
                "id": 2, "subject": "期限超過タスク",
                "status": {"id": 2, "name": "In Progress"},
                "priority": {"id": 3, "name": "High"},
                "assigned_to": None, "due_date": "2026-03-01",  # overdue
                "created_on": "2026-02-01T09:00:00Z",
                "updated_on": "2026-03-03T09:00:00Z",
            },
            {
                "id": 3, "subject": "期日迫るタスク",
                "status": {"id": 2, "name": "In Progress"},
                "priority": {"id": 3, "name": "High"},
                "assigned_to": None, "due_date": "2026-03-05",  # high (2日後)
                "created_on": "2026-03-02T09:00:00Z",
                "updated_on": "2026-03-03T09:00:00Z",
            },
        ],
        "total_count": 3,
        "offset": 0,
        "limit": 100,
    })

    # When
    with patch('app.task.service.date') as mock_date:
        mock_date.today.return_value = date(2026, 3, 3)
        results = await task_dashboard_service.get_tasks()

    # Then
    assert len(results) == 3
    assert results[0].urgency == "overdue"  # 期限超過が最初
    assert results[1].urgency == "high"     # 期日迫るが2番目
    assert results[2].urgency == "normal"   # 通常が最後
```

#### TC-BE-S002: ステータスフィルタリング（正常系）

```
Given:
  - RedmineMCPClientが new/in_progress/closed の3件を返すようにモック
When: TaskDashboardService.get_tasks(status_filter="in_progress") を呼び出す
Then: 1件（in_progressのタスク）のみが返される
```

```python
@pytest.mark.asyncio
async def test_get_tasks_with_status_filter(
    task_dashboard_service: TaskDashboardService,
    mock_redmine_client_mixed_status: MagicMock,
):
    # When
    results = await task_dashboard_service.get_tasks(status_filter="in_progress")

    # Then
    assert len(results) == 1
    assert results[0].status == "in_progress"
```

#### TC-BE-S003: urgencyフィルタリング（正常系）

```
Given:
  - RedmineMCPClientがoverdue/high/normalの3件を返すようにモック
When: TaskDashboardService.get_tasks(urgency_filter="overdue") を呼び出す
Then: 1件（overdueのタスク）のみが返される
```

#### TC-BE-S004: Redmine接続失敗（異常系・3回リトライ後）

```
Given: RedmineMCPClientがRedmineConnectionErrorを raise するようにモック
When: TaskDashboardService.get_tasks() を呼び出す
Then: RedmineConnectionError が raise される
```

```python
@pytest.mark.asyncio
async def test_get_tasks_redmine_connection_error(
    task_dashboard_service: TaskDashboardService,
):
    # Given
    task_dashboard_service.redmine_client.get_issues = AsyncMock(
        side_effect=RedmineConnectionError("接続失敗")
    )

    # When / Then
    with pytest.raises(RedmineConnectionError):
        await task_dashboard_service.get_tasks()
```

#### TC-BE-S005: タスク0件（正常系）

```
Given: RedmineMCPClientが空のissuesリストを返すようにモック（total_count=0）
When: TaskDashboardService.get_tasks() を呼び出す
Then: 空のリスト [] が返される（例外は raise しない）
```

```python
@pytest.mark.asyncio
async def test_get_tasks_empty_result(
    task_dashboard_service: TaskDashboardService,
    mock_redmine_client: MagicMock,
):
    # Given
    mock_redmine_client.get_issues = AsyncMock(return_value={
        "issues": [],
        "total_count": 0,
        "offset": 0,
        "limit": 100,
    })

    # When
    results = await task_dashboard_service.get_tasks()

    # Then
    assert results == []
    assert isinstance(results, list)
```

#### TC-BE-S006: ページネーション（total_count > 100）

```
Given:
  - 1回目のget_issues呼び出し: 100件 + total_count=150
  - 2回目のget_issues呼び出し: 50件 + total_count=150
When: TaskDashboardService._fetch_all_issues() を呼び出す
Then:
  - 合計150件のIssueリストが返される
  - get_issuesが2回呼ばれている
```

```python
@pytest.mark.asyncio
async def test_fetch_all_issues_pagination(
    task_dashboard_service: TaskDashboardService,
):
    # Given: 150件のケース（1ページ目100件、2ページ目50件）
    first_page_issues = [{"id": i, "subject": f"Task {i}"} for i in range(1, 101)]
    second_page_issues = [{"id": i, "subject": f"Task {i}"} for i in range(101, 151)]

    task_dashboard_service.redmine_client.get_issues = AsyncMock(
        side_effect=[
            {"issues": first_page_issues, "total_count": 150, "offset": 0, "limit": 100},
            {"issues": second_page_issues, "total_count": 150, "offset": 100, "limit": 100},
        ]
    )

    # When
    results = await task_dashboard_service._fetch_all_issues()

    # Then
    assert len(results) == 150
    assert task_dashboard_service.redmine_client.get_issues.call_count == 2
```

#### TC-BE-S007: ステータスグルーピング（正常系）

```
Given:
  - new: 2件, in_progress: 3件, closed: 1件, のタスク
When: TaskDashboardService.get_tasks_grouped() を呼び出す
Then:
  - result["todo"] == 2件（newのタスク）
  - result["in_progress"] == 3件（in_progressのタスク）
  - result["done"] == 1件（closedのタスク）
```

---

## 5. フロントエンドテストケース

### 5.1 TaskCardテスト

#### TC-FE-001: タスクカード表示（正常系・期限超過タスク）

```
Given: urgency="overdue"、due_date="2026-03-01" のTask
When: TaskCard をレンダリングする
Then:
  - タスクタイトルが表示されている
  - タイトルが Redmine URL へのリンクになっている（href="http://localhost:8080/issues/123"）
  - リンクが target="_blank" で設定されている
  - 左ボーダーが赤色クラス（border-red-500）で表示されている
  - 緊急度バッジ「期限超過」が表示されている
```

```typescript
import { render, screen } from '@testing-library/react';
import { TaskCard } from '../TaskCard';

const overdueTask: Task = {
  id: 123,
  title: '期限超過タスク',
  status: 'in_progress',
  status_label: '進行中',
  priority: 'high',
  priority_label: '高',
  assignee_name: '山田 太郎',
  due_date: '2026-03-01',
  urgency: 'overdue',
  redmine_url: 'http://localhost:8080/issues/123',
  created_at: '2026-02-01T09:00:00Z',
  updated_at: '2026-03-03T09:00:00Z',
};

test('期限超過タスクが赤ボーダーで表示される', () => {
  // When
  render(<TaskCard task={overdueTask} />);

  // Then
  const title = screen.getByText('#123 期限超過タスク');
  expect(title).toBeInTheDocument();

  const link = screen.getByRole('link');
  expect(link).toHaveAttribute('href', 'http://localhost:8080/issues/123');
  expect(link).toHaveAttribute('target', '_blank');

  const card = link.closest('[class*="border-red-500"]');
  expect(card).toBeInTheDocument();

  expect(screen.getByText('期限超過')).toBeInTheDocument();
});
```

#### TC-FE-002: タスクカード表示（正常系・期日迫るタスク）

```
Given: urgency="high"、due_date="2026-03-05" のTask（今日=3/3）
When: TaskCard をレンダリングする
Then:
  - 左ボーダーが黄橙色クラス（border-amber-400）で表示されている
  - 緊急度バッジ「期日迫る」が表示されている
  - 期日表示が「2日後」になっている（vi.setSystemTime でtoday=3/3に固定）
```

#### TC-FE-003: タスクカード表示（正常系・担当者なし）

```
Given: assignee_name=null のTask
When: TaskCard をレンダリングする
Then:
  - 「担当:」の行が表示されない
```

```typescript
test('担当者なしのタスクは担当者行を表示しない', () => {
  const noAssigneeTask = { ...overdueTask, assignee_name: null };
  render(<TaskCard task={noAssigneeTask} />);
  expect(screen.queryByText(/担当:/)).not.toBeInTheDocument();
});
```

#### TC-FE-004: タスクカード表示（正常系・通常タスク）

```
Given: urgency="normal"、due_date=null のTask
When: TaskCard をレンダリングする
Then:
  - 左ボーダーが通常色（border-gray-200）で表示されている
  - urgencyバッジが表示されない（normalは表示しない）
  - 期日表示がない
```

### 5.2 TaskStatusColumnテスト

#### TC-FE-005: TaskStatusColumnのタスク一覧表示

```
Given: 3件のTaskを持つTaskStatusColumn（title="進行中", tasks=3件）
When: TaskStatusColumn をレンダリングする
Then:
  - 「進行中」というタイトルが表示されている
  - 件数バッジに「3」が表示されている
  - 3件のTaskCardが表示されている
```

```typescript
test('TaskStatusColumnがタスク一覧を正しく表示する', () => {
  const tasks = [
    { ...baseTask, id: 1, title: 'タスク1' },
    { ...baseTask, id: 2, title: 'タスク2' },
    { ...baseTask, id: 3, title: 'タスク3' },
  ];

  render(
    <TaskStatusColumn title="進行中" tasks={tasks} colorScheme="blue" isLoading={false} />
  );

  expect(screen.getByText('進行中')).toBeInTheDocument();
  expect(screen.getByText('3')).toBeInTheDocument();  // 件数バッジ
  tasks.forEach(task => {
    expect(screen.getByText(new RegExp(task.title))).toBeInTheDocument();
  });
});
```

#### TC-FE-006: ローディング状態の表示

```
Given: isLoading=true のTaskStatusColumn
When: TaskStatusColumn をレンダリングする
Then:
  - ローディングスケルトンが表示されている（TaskCardは表示されない）
```

#### TC-FE-007: 空状態の表示

```
Given: tasks=[] のTaskStatusColumn
When: TaskStatusColumn をレンダリングする
Then:
  - 「タスクはありません」メッセージが表示されている
```

### 5.3 TaskSummaryStatsテスト

#### TC-FE-008: タスク統計の正しい集計

```
Given:
  - overdue: 2件
  - high: 3件
  - normal: 5件（うち in_progress: 4件）
  のTask配列
When: TaskSummaryStats をレンダリングする
Then:
  - 「全タスク」に「10」が表示されている
  - 「進行中」に「4」が表示されている
  - 「期日迫る」に「3」が表示されている
  - 「期限超過」に「2」が表示されている
```

```typescript
test('TaskSummaryStatsが正しい件数を表示する', () => {
  const tasks: Task[] = [
    ...Array(2).fill(null).map((_, i) => ({ ...baseTask, id: i + 1, urgency: 'overdue' as const, status: 'new' as const })),
    ...Array(3).fill(null).map((_, i) => ({ ...baseTask, id: i + 3, urgency: 'high' as const, status: 'in_progress' as const })),
    ...Array(4).fill(null).map((_, i) => ({ ...baseTask, id: i + 6, urgency: 'normal' as const, status: 'in_progress' as const })),
    { ...baseTask, id: 10, urgency: 'normal' as const, status: 'new' as const },
  ];

  render(<TaskSummaryStats tasks={tasks} />);

  expect(screen.getByText('10')).toBeInTheDocument();  // 全タスク
  expect(screen.getByText('7')).toBeInTheDocument();   // 進行中（in_progress 7件）
  expect(screen.getByText('3')).toBeInTheDocument();   // 期日迫る
  expect(screen.getByText('2')).toBeInTheDocument();   // 期限超過
});
```

### 5.4 useTasksフックテスト

#### TC-FE-009: タスク一覧の取得（正常系）

```
Given: MSWでGET /api/v1/tasksが3件のタスクを返すように設定
When: useTasks フックを使用するコンポーネントをマウントする
Then:
  - isLoading が true → false に変化する
  - tasks に3件のタスクが設定される
  - error が null である
  - lastUpdated が null でなくなる
```

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useTasks } from '../useTasks';

test('マウント時にタスクを取得する', async () => {
  // Given: MSWがデフォルトで3件のタスクを返す

  // When
  const { result } = renderHook(() => useTasks());

  // isLoading=true の初期状態を確認
  expect(result.current.isLoading).toBe(true);

  // Then
  await waitFor(() => {
    expect(result.current.isLoading).toBe(false);
  });

  expect(result.current.tasks).toHaveLength(3);
  expect(result.current.error).toBeNull();
  expect(result.current.lastUpdated).not.toBeNull();
});
```

#### TC-FE-010: Redmine接続失敗（異常系）

```
Given: MSWでGET /api/v1/tasksが503を返すように設定
When: useTasks フックを使用するコンポーネントをマウントする
Then:
  - error が null でなくなる（Redmine接続失敗メッセージ）
  - isLoading が false になる
  - tasks は空配列またはデフォルト値
```

```typescript
test('503エラー時にerrorが設定される', async () => {
  // Given: 503レスポンスのMSWハンドラ上書き
  server.use(
    http.get('/api/v1/tasks', () => {
      return HttpResponse.json(
        { error: { code: 'SERVICE_UNAVAILABLE', message: '...' } },
        { status: 503 }
      );
    })
  );

  // When
  const { result } = renderHook(() => useTasks());

  // Then
  await waitFor(() => {
    expect(result.current.isLoading).toBe(false);
  });

  expect(result.current.error).not.toBeNull();
  expect(result.current.error).toContain('Redmine');
});
```

#### TC-FE-011: 手動更新（refresh）

```
Given: タスクが取得済みの状態
When: refresh() を呼び出す
Then:
  - isRefreshing が true → false に変化する
  - APIが再度呼ばれる
  - lastUpdated が更新される
```

---

## 6. テスト実行環境

FEAT-005のDSD-008と同じ設定を使用する。

**バックエンドテスト実行コマンド:**
```bash
# FEAT-006のテストのみ実行
pytest tests/task/ -v --cov=app.task --cov-report=term-missing
```

**フロントエンドテスト実行コマンド:**
```bash
# FEAT-006のテストのみ実行
npm run test -- src/components/dashboard src/hooks/__tests__/useTasks.test.ts
```

---

## 7. カバレッジ目標

| 対象 | カバレッジ目標 | 優先対象 |
|---|---|---|
| バックエンド（Python） | 行カバレッジ 85%以上 | TaskUrgency.from_due_date（境界値テスト重点）, RedmineAdapter, TaskDashboardService |
| フロントエンド（TypeScript） | 行カバレッジ 70%以上 | useTasks, TaskCard |

**重点テスト対象**: `TaskUrgency.from_due_date` は境界値テスト（TC-BE-U001〜U009）が特に重要。期日チェックロジックのバグはユーザーへの誤った緊急度表示に直結するため、全境界値ケースをカバーすること。

---

## 8. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-001_FEAT-006 | 本設計書のバックエンドテストケース（TC-BE-U001〜S007）をpytestで実装する |
| IMP-002_FEAT-006 | 本設計書のフロントエンドテストケース（TC-FE-001〜011）をVitestで実装する |
| IMP-005 | TDDサイクルで発見したバグはIMP-005（TDD不具合管理票）に記録する |
| IT-001_FEAT-006 | 単体テストで確認した期日チェック境界値を結合テストでも確認する |
