"""FEAT-003: TaskUpdateService の単体テスト（DSD-008 TC-SVC01〜SVC08）。

TDD Green フェーズ: 実装済みの TaskUpdateService に対してテストを実行する。
モック方針: RedmineAdapter を MagicMock/AsyncMock でモック化する。
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.task.task_update_service import TaskUpdateService
from app.domain.exceptions import (
    InvalidStatusIdError,
    TaskDeleteOperationForbiddenError,
    TaskNotFoundError,
)


# ---------------------------------------------------------------------------
# テストデータヘルパー
# ---------------------------------------------------------------------------


def _make_issue_response(
    issue_id: int,
    status_id: int = 1,
    subject: str = "テストタスク",
    priority_id: int = 2,
    assigned_to_name: str = "山田 太郎",
    due_date: str | None = None,
) -> dict:
    """Redmine Issue APIレスポンスのテストデータを生成するヘルパー関数。"""
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


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_redmine_adapter() -> MagicMock:
    """RedmineAdapter のモックオブジェクト。"""
    adapter = MagicMock()
    adapter.get_issue = AsyncMock()
    adapter.update_issue = AsyncMock()
    return adapter


@pytest.fixture
def task_update_service(mock_redmine_adapter: MagicMock) -> TaskUpdateService:
    """TaskUpdateService のフィクスチャ。RedmineAdapter をモック化する。"""
    return TaskUpdateService(redmine_adapter=mock_redmine_adapter)


# ---------------------------------------------------------------------------
# TC-SVC01: update_task_status - ステータス更新成功（正常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskStatusSuccess:
    """TC-SVC01: update_task_status - ステータス更新成功（正常系）。"""

    @pytest.mark.asyncio
    async def test_update_task_status_success(
        self, task_update_service: TaskUpdateService, mock_redmine_adapter: MagicMock
    ) -> None:
        """ステータス更新が成功し、更新後の TaskUpdate オブジェクトが返される。

        Given: 存在するIssue ID=123、有効なstatus_id=3（完了）
        When: task_update_service.update_task_status(123, 3) を呼び出す
        Then: Redmine update_issueが呼び出され、更新後のTaskオブジェクトが返される
              ステータスが TaskStatusVO(id=3, name="完了") であること
        """
        # Given
        mock_redmine_adapter.get_issue.return_value = _make_issue_response(123, status_id=2)
        mock_redmine_adapter.update_issue.return_value = _make_issue_response(123, status_id=3)

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


# ---------------------------------------------------------------------------
# TC-SVC02: update_task_status - notesを同時に追加（正常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskStatusWithNotes:
    """TC-SVC02: update_task_status - notesを同時に追加（正常系）。"""

    @pytest.mark.asyncio
    async def test_update_task_status_with_notes(
        self, task_update_service: TaskUpdateService, mock_redmine_adapter: MagicMock
    ) -> None:
        """status_idとnotesの両方を含むpayloadでupdate_issueが呼び出される。

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


# ---------------------------------------------------------------------------
# TC-SVC03: update_task_status - チケット不存在（異常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskStatusNotFound:
    """TC-SVC03: update_task_status - チケット不存在（異常系）。"""

    @pytest.mark.asyncio
    async def test_update_task_status_task_not_found(
        self, task_update_service: TaskUpdateService, mock_redmine_adapter: MagicMock
    ) -> None:
        """存在しないIssue IDを指定すると TaskNotFoundError が発生する。

        Given: 存在しないIssue ID=9999
        When: task_update_service.update_task_status(9999, 3) を呼び出す
        Then: TaskNotFoundError が発生する
              エラーメッセージにissue_id=9999が含まれる
        """
        # Given
        mock_redmine_adapter.get_issue.side_effect = TaskNotFoundError(9999)

        # When / Then
        with pytest.raises(TaskNotFoundError) as exc_info:
            await task_update_service.update_task_status(9999, 3)

        assert "9999" in str(exc_info.value)
        # update_issueは呼び出されない
        mock_redmine_adapter.update_issue.assert_not_called()


# ---------------------------------------------------------------------------
# TC-SVC04: update_task_status - 無効なステータスID（異常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskStatusInvalidStatusId:
    """TC-SVC04: update_task_status - 無効なステータスID（異常系）。"""

    @pytest.mark.parametrize("invalid_status_id", [0, 4, 6, 10, -1, 100])
    @pytest.mark.asyncio
    async def test_update_task_status_invalid_status_id(
        self,
        task_update_service: TaskUpdateService,
        mock_redmine_adapter: MagicMock,
        invalid_status_id: int,
    ) -> None:
        """無効なstatus_idを指定すると InvalidStatusIdError が発生する。

        Given: 無効なstatus_id（{1,2,3,5}以外）
        When: task_update_service.update_task_status(123, invalid_status_id) を呼び出す
        Then: InvalidStatusIdError が発生する
              get_issueもupdate_issueも呼び出されない
        """
        with pytest.raises(InvalidStatusIdError):
            await task_update_service.update_task_status(123, invalid_status_id)

        # バリデーション失敗のため、Redmine APIは一切呼び出されない
        mock_redmine_adapter.get_issue.assert_not_called()
        mock_redmine_adapter.update_issue.assert_not_called()


# ---------------------------------------------------------------------------
# TC-SVC05: update_task_status - 削除操作試行のブロック（BR-02検証）
# ---------------------------------------------------------------------------


class TestPreventDeleteOperation:
    """TC-SVC05: 削除操作試行のブロック（BR-02検証）。"""

    def test_prevent_delete_operation_blocked(
        self, task_update_service: TaskUpdateService
    ) -> None:
        """削除を示す操作名が渡されると TaskDeleteOperationForbiddenError が発生する。

        Given: 削除を示す操作名が渡される（BR-02のセーフガード確認）
        When: _prevent_delete_operation("delete_issue") を内部で呼び出す
        Then: TaskDeleteOperationForbiddenError が発生する
        """
        with pytest.raises(TaskDeleteOperationForbiddenError):
            task_update_service._prevent_delete_operation("delete_issue")

    def test_prevent_destroy_operation_blocked(
        self, task_update_service: TaskUpdateService
    ) -> None:
        """destroy を含む操作名でも TaskDeleteOperationForbiddenError が発生する。

        Given: "destroy_task" という操作名
        When: _prevent_delete_operation("destroy_task") を内部で呼び出す
        Then: TaskDeleteOperationForbiddenError が発生する
        """
        with pytest.raises(TaskDeleteOperationForbiddenError):
            task_update_service._prevent_delete_operation("destroy_task")

    def test_normal_operation_not_blocked(
        self, task_update_service: TaskUpdateService
    ) -> None:
        """通常の操作名では例外が発生しない。

        Given: 削除を示さない操作名
        When: _prevent_delete_operation("update_status") を呼び出す
        Then: 例外が発生しない
        """
        # 例外が発生しないことを確認（returnで終了）
        task_update_service._prevent_delete_operation("update_status")


# ---------------------------------------------------------------------------
# TC-SVC06: add_task_comment - コメント追加成功（正常系）
# ---------------------------------------------------------------------------


class TestAddTaskCommentSuccess:
    """TC-SVC06: add_task_comment - コメント追加成功（正常系）。"""

    @pytest.mark.asyncio
    async def test_add_task_comment_success(
        self, task_update_service: TaskUpdateService, mock_redmine_adapter: MagicMock
    ) -> None:
        """コメント追加が成功し、notesのみのpayloadでupdate_issueが呼び出される。

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


# ---------------------------------------------------------------------------
# TC-SVC07: add_task_comment - 空のコメント（異常系）
# ---------------------------------------------------------------------------


class TestAddTaskCommentEmptyNotes:
    """TC-SVC07: add_task_comment - 空のコメント（異常系）。"""

    @pytest.mark.parametrize("empty_notes", ["", "  ", "\n", "\t"])
    @pytest.mark.asyncio
    async def test_add_task_comment_empty_notes(
        self,
        task_update_service: TaskUpdateService,
        mock_redmine_adapter: MagicMock,
        empty_notes: str,
    ) -> None:
        """空またはスペースのみのnotesで ValueError が発生する。

        Given: 空またはスペースのみのnotes
        When: task_update_service.add_task_comment(45, empty_notes) を呼び出す
        Then: ValueError が発生する
              Redmine APIは呼び出されない
        """
        with pytest.raises(ValueError, match="コメント内容は空にできません"):
            await task_update_service.add_task_comment(45, empty_notes)

        mock_redmine_adapter.get_issue.assert_not_called()
        mock_redmine_adapter.update_issue.assert_not_called()


# ---------------------------------------------------------------------------
# TC-SVC08: add_task_comment - チケット不存在（異常系）
# ---------------------------------------------------------------------------


class TestAddTaskCommentNotFound:
    """TC-SVC08: add_task_comment - チケット不存在（異常系）。"""

    @pytest.mark.asyncio
    async def test_add_task_comment_task_not_found(
        self, task_update_service: TaskUpdateService, mock_redmine_adapter: MagicMock
    ) -> None:
        """存在しないIssue IDを指定すると TaskNotFoundError が発生する。

        Given: 存在しないIssue ID=9999
        When: task_update_service.add_task_comment(9999, "コメント") を呼び出す
        Then: TaskNotFoundError が発生する
        """
        mock_redmine_adapter.get_issue.side_effect = TaskNotFoundError(9999)

        with pytest.raises(TaskNotFoundError):
            await task_update_service.add_task_comment(9999, "コメント")

        mock_redmine_adapter.update_issue.assert_not_called()
