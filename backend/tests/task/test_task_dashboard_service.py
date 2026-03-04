"""TaskDashboardService の単体テスト（TDD: TC-BE-S001〜TC-BE-S007）。"""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.exceptions import RedmineConnectionError


def make_issue(
    id: int,
    subject: str,
    status_name: str = "In Progress",
    due_date: str | None = None,
) -> dict:
    """テスト用の Redmine Issue 辞書を生成するヘルパー。"""
    return {
        "id": id,
        "subject": subject,
        "status": {"id": 2, "name": status_name},
        "priority": {"id": 2, "name": "Normal"},
        "assigned_to": None,
        "due_date": due_date,
        "created_on": "2026-03-01T09:00:00Z",
        "updated_on": "2026-03-03T09:00:00Z",
    }


@pytest.fixture
def mock_redmine_client() -> MagicMock:
    """RedmineMCPClient のモック。デフォルトで3件の Issue を返す。"""
    client = MagicMock()
    client.get_issues = AsyncMock(return_value={
        "issues": [
            make_issue(1, "通常タスク", due_date="2026-03-20"),       # normal
            make_issue(2, "期限超過タスク", due_date="2026-03-01"),   # overdue
            make_issue(3, "期日迫るタスク", due_date="2026-03-05"),   # high (2日後)
        ],
        "total_count": 3,
        "offset": 0,
        "limit": 100,
    })
    return client


@pytest.fixture
def mock_redmine_client_mixed_status() -> MagicMock:
    """ステータス混在の3件を返すモック。"""
    client = MagicMock()
    client.get_issues = AsyncMock(return_value={
        "issues": [
            {**make_issue(1, "新規タスク"), "status": {"id": 1, "name": "New"}},
            {**make_issue(2, "進行中タスク"), "status": {"id": 2, "name": "In Progress"}},
            {**make_issue(3, "完了タスク"), "status": {"id": 5, "name": "Closed"}},
        ],
        "total_count": 3,
        "offset": 0,
        "limit": 100,
    })
    return client


@pytest.fixture
def task_dashboard_service(mock_redmine_client: MagicMock):
    """TaskDashboardService インスタンス（デフォルトの mock_redmine_client 付き）。"""
    from app.task.service import TaskDashboardService

    return TaskDashboardService(redmine_client=mock_redmine_client)


class TestTaskDashboardService:
    """TaskDashboardService のテストクラス。"""

    # TC-BE-S001: タスク一覧取得（正常系・urgency 優先度順ソート）
    @pytest.mark.asyncio
    async def test_get_tasks_returns_sorted_tasks(
        self,
        task_dashboard_service,
        mock_redmine_client: MagicMock,
    ) -> None:
        # Given: today=2026-03-03 に固定
        with patch("app.task.service.date") as mock_date:
            mock_date.today.return_value = date(2026, 3, 3)

            # When
            results = await task_dashboard_service.get_tasks()

        # Then
        assert len(results) == 3
        assert results[0].urgency == "overdue"   # 期限超過が最初
        assert results[1].urgency == "high"      # 期日迫るが2番目
        assert results[2].urgency == "normal"    # 通常が最後

    # TC-BE-S002: ステータスフィルタリング（正常系）
    @pytest.mark.asyncio
    async def test_get_tasks_with_status_filter(
        self,
        mock_redmine_client_mixed_status: MagicMock,
    ) -> None:
        from app.task.service import TaskDashboardService

        service = TaskDashboardService(redmine_client=mock_redmine_client_mixed_status)

        # When
        results = await service.get_tasks(status_filter="in_progress")

        # Then
        assert len(results) == 1
        assert results[0].status == "in_progress"

    # TC-BE-S003: urgency フィルタリング（正常系）
    @pytest.mark.asyncio
    async def test_get_tasks_with_urgency_filter(
        self,
        task_dashboard_service,
    ) -> None:
        # When: today=2026-03-03 に固定
        with patch("app.task.service.date") as mock_date:
            mock_date.today.return_value = date(2026, 3, 3)
            results = await task_dashboard_service.get_tasks(urgency_filter="overdue")

        # Then
        assert len(results) == 1
        assert results[0].urgency == "overdue"

    # TC-BE-S004: Redmine 接続失敗（異常系）
    @pytest.mark.asyncio
    async def test_get_tasks_redmine_connection_error(
        self,
        task_dashboard_service,
    ) -> None:
        # Given: RedmineMCPClient が RedmineConnectionError を raise する
        task_dashboard_service.redmine_client.get_issues = AsyncMock(
            side_effect=RedmineConnectionError("接続失敗")
        )

        # When / Then
        with pytest.raises(RedmineConnectionError):
            await task_dashboard_service.get_tasks()

    # TC-BE-S005: タスク 0 件（正常系）
    @pytest.mark.asyncio
    async def test_get_tasks_empty_result(
        self,
        task_dashboard_service,
        mock_redmine_client: MagicMock,
    ) -> None:
        # Given: 空のリストを返す
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

    # TC-BE-S006: ページネーション（total_count > 100）
    @pytest.mark.asyncio
    async def test_fetch_all_issues_pagination(
        self,
        task_dashboard_service,
    ) -> None:
        # Given: 150件のケース（1ページ目100件、2ページ目50件）
        first_page_issues = [
            make_issue(i, f"Task {i}")
            for i in range(1, 101)
        ]
        second_page_issues = [
            make_issue(i, f"Task {i}")
            for i in range(101, 151)
        ]

        task_dashboard_service.redmine_client.get_issues = AsyncMock(
            side_effect=[
                {
                    "issues": first_page_issues,
                    "total_count": 150,
                    "offset": 0,
                    "limit": 100,
                },
                {
                    "issues": second_page_issues,
                    "total_count": 150,
                    "offset": 100,
                    "limit": 100,
                },
            ]
        )

        # When
        results = await task_dashboard_service._fetch_all_issues()

        # Then
        assert len(results) == 150
        assert task_dashboard_service.redmine_client.get_issues.call_count == 2

    # TC-BE-S007: ステータスグルーピング（正常系）
    @pytest.mark.asyncio
    async def test_get_tasks_grouped(
        self,
        mock_redmine_client: MagicMock,
    ) -> None:
        from app.task.service import TaskDashboardService

        # Given: new: 2件, in_progress: 3件, closed: 1件
        mock_redmine_client.get_issues = AsyncMock(return_value={
            "issues": [
                {**make_issue(1, "新規1"), "status": {"id": 1, "name": "New"}},
                {**make_issue(2, "新規2"), "status": {"id": 1, "name": "New"}},
                {**make_issue(3, "進行1"), "status": {"id": 2, "name": "In Progress"}},
                {**make_issue(4, "進行2"), "status": {"id": 2, "name": "In Progress"}},
                {**make_issue(5, "進行3"), "status": {"id": 2, "name": "In Progress"}},
                {**make_issue(6, "完了1"), "status": {"id": 5, "name": "Closed"}},
            ],
            "total_count": 6,
            "offset": 0,
            "limit": 100,
        })
        service = TaskDashboardService(redmine_client=mock_redmine_client)

        # When
        result = await service.get_tasks_grouped()

        # Then
        assert len(result["todo"]) == 2        # new: 2件
        assert len(result["in_progress"]) == 3  # in_progress: 3件
        assert len(result["done"]) == 1         # closed: 1件
