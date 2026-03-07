"""FEAT-004: TaskScheduleService の単体テスト（DSD-008 TC-SCH01〜TC-SCH06）。

TDD: テストを先に書いた後、Green フェーズで実装する。
"""
from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.exceptions import InvalidPriorityError, TaskNotFoundError


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------


def _make_issue_response(
    issue_id: int,
    priority_id: int = 2,
    due_date: str | None = None,
    status_id: int = 2,
) -> dict:
    """RedmineAdapter のモック戻り値として使用するIssueレスポンス辞書。"""
    priority_names = {1: "低", 2: "通常", 3: "高", 4: "緊急", 5: "即座に"}
    status_names = {1: "未着手", 2: "進行中", 3: "完了", 5: "却下"}
    return {
        "issue": {
            "id": issue_id,
            "subject": "テストタスク",
            "status": {"id": status_id, "name": status_names.get(status_id, "不明")},
            "priority": {
                "id": priority_id,
                "name": priority_names.get(priority_id, "通常"),
            },
            "due_date": due_date,
            "start_date": None,
            "done_ratio": 0,
            "description": "",
            "updated_on": "2026-03-03T10:00:00Z",
            "created_on": "2026-03-01T09:00:00Z",
        }
    }


@pytest.fixture
def mock_redmine_adapter() -> MagicMock:
    """RedmineAdapter のモックフィクスチャ。"""
    adapter = MagicMock()
    adapter.get_issue = AsyncMock()
    adapter.update_issue_priority = AsyncMock()
    adapter.update_issue_due_date = AsyncMock()
    adapter.list_issues = AsyncMock()
    return adapter


@pytest.fixture
def task_schedule_service(mock_redmine_adapter: MagicMock):
    """TaskScheduleService のフィクスチャ（RedmineAdapterをモック化）。"""
    from app.application.services.task_schedule_service import TaskScheduleService

    return TaskScheduleService(redmine_adapter=mock_redmine_adapter)


# ---------------------------------------------------------------------------
# TC-SCH01: update_task_priority - 優先度変更成功（正常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskPrioritySuccess:
    """TC-SCH01: update_task_priority - 優先度変更成功（正常系）。"""

    @pytest.mark.asyncio
    async def test_update_task_priority_success(
        self, task_schedule_service, mock_redmine_adapter: MagicMock
    ) -> None:
        """存在するIssue ID=123 に対して有効なpriority_id=4（緊急）で優先度変更が成功する。

        Given: 存在するIssue ID=123、有効なpriority_id=4（緊急）
        When: task_schedule_service.update_task_priority(123, 4) を呼び出す
        Then: RedmineAdapter.update_issue_priority が呼び出される
              返却されたTaskオブジェクトの priority.id == 4 である
        """
        # Given
        mock_redmine_adapter.update_issue_priority.return_value = _make_issue_response(
            123, priority_id=4
        )

        # When
        result = await task_schedule_service.update_task_priority(123, 4)

        # Then
        assert result.redmine_issue_id == 123
        assert result.priority.id == 4
        assert result.priority.name == "緊急"
        mock_redmine_adapter.update_issue_priority.assert_called_once_with(123, 4)


# ---------------------------------------------------------------------------
# TC-SCH02: update_task_priority - 無効な優先度ID（異常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskPriorityInvalidId:
    """TC-SCH02: update_task_priority - 無効な優先度ID（異常系）。"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_priority_id", [0, 6, -1, 10, 100])
    async def test_update_task_priority_invalid_id(
        self,
        task_schedule_service,
        mock_redmine_adapter: MagicMock,
        invalid_priority_id: int,
    ) -> None:
        """無効なpriority_id（{1,2,3,4,5}以外）で InvalidPriorityError が発生する。

        Given: 無効なpriority_id（{1,2,3,4,5}以外）
        When: task_schedule_service.update_task_priority(123, invalid_priority_id) を呼び出す
        Then: InvalidPriorityError が発生する
              update_issue_priority は呼び出されない
        """
        with pytest.raises(InvalidPriorityError):
            await task_schedule_service.update_task_priority(123, invalid_priority_id)

        mock_redmine_adapter.update_issue_priority.assert_not_called()


# ---------------------------------------------------------------------------
# TC-SCH03: update_task_priority - チケット不存在（異常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskPriorityNotFound:
    """TC-SCH03: update_task_priority - チケット不存在（異常系）。"""

    @pytest.mark.asyncio
    async def test_update_task_priority_task_not_found(
        self, task_schedule_service, mock_redmine_adapter: MagicMock
    ) -> None:
        """存在しないIssue ID=9999 に対して TaskNotFoundError が発生する。

        Given: 存在しないIssue ID=9999
        When: task_schedule_service.update_task_priority(9999, 3) を呼び出す
        Then: TaskNotFoundError が発生する
        """
        mock_redmine_adapter.update_issue_priority.side_effect = TaskNotFoundError(9999)

        with pytest.raises(TaskNotFoundError) as exc_info:
            await task_schedule_service.update_task_priority(9999, 3)

        assert "9999" in str(exc_info.value)


# ---------------------------------------------------------------------------
# TC-SCH04: update_task_due_date - 期日変更成功（正常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskDueDateSuccess:
    """TC-SCH04: update_task_due_date - 期日変更成功（正常系）。"""

    @pytest.mark.asyncio
    async def test_update_task_due_date_success(
        self, task_schedule_service, mock_redmine_adapter: MagicMock
    ) -> None:
        """存在するIssue ID=123 に対して valid due_date で期日変更が成功する。

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


# ---------------------------------------------------------------------------
# TC-SCH05: update_task_due_date - 過去日付の警告付き成功（正常系・警告あり）
# ---------------------------------------------------------------------------


class TestUpdateTaskDueDatePastDate:
    """TC-SCH05: update_task_due_date - 過去日付の警告付き成功（正常系・警告あり）。"""

    @pytest.mark.asyncio
    async def test_update_task_due_date_past_date_warning(
        self, task_schedule_service, mock_redmine_adapter: MagicMock
    ) -> None:
        """過去日付を設定した場合でも更新は成功する。

        Given: 過去日付 due_date=date(2026, 2, 1)（本日2026-03-03より前）
        When: task_schedule_service.update_task_due_date(123, date(2026, 2, 1)) を呼び出す
        Then: 更新は成功する（Redmineは過去日付を拒否しない）
        """
        past_date = date(2026, 2, 1)
        mock_redmine_adapter.update_issue_due_date.return_value = _make_issue_response(
            123, due_date="2026-02-01"
        )

        result = await task_schedule_service.update_task_due_date(123, past_date)
        assert result.due_date == past_date
        # 更新は成功する（Redmineサーバー側は過去日付を拒否しない）
        mock_redmine_adapter.update_issue_due_date.assert_called_once()


# ---------------------------------------------------------------------------
# TC-SCH06: update_task_due_date - Redmineバリデーションエラー（異常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskDueDateRedmineError:
    """TC-SCH06: update_task_due_date - Redmineバリデーションエラー（異常系）。"""

    @pytest.mark.asyncio
    async def test_update_task_due_date_redmine_validation_error(
        self, task_schedule_service, mock_redmine_adapter: MagicMock
    ) -> None:
        """start_date > due_date となる期日設定で RedmineAPIError が発生する。

        Given: start_date > due_date となる期日の設定（Redmineが422を返すケース）
        When: task_schedule_service.update_task_due_date(123, date(2026, 2, 28)) を呼び出す
        Then: RedmineAPIError が発生する
        """
        from app.domain.exceptions import RedmineAPIError

        mock_redmine_adapter.update_issue_due_date.side_effect = RedmineAPIError(
            "Redmineバリデーションエラー: 開始日より前の期日は設定できません",
            status_code=422,
        )

        with pytest.raises(RedmineAPIError) as exc_info:
            await task_schedule_service.update_task_due_date(123, date(2026, 2, 28))

        assert exc_info.value.status_code == 422
