"""TaskStatus 値オブジェクトの単体テスト。"""
from __future__ import annotations

import pytest

from app.domain.task.task_status import TaskStatus


class TestTaskStatusFromRedmineId:
    """from_redmine_id クラスメソッドのテスト。"""

    @pytest.mark.parametrize(
        "status_id, expected",
        [
            (1, TaskStatus.NEW),
            (2, TaskStatus.IN_PROGRESS),
            (3, TaskStatus.RESOLVED),
            (4, TaskStatus.CLOSED),
            (5, TaskStatus.REJECTED),
        ],
    )
    def test_from_redmine_id_known_ids(self, status_id: int, expected: TaskStatus) -> None:
        """既知のステータス ID から正しい TaskStatus を生成する。"""
        assert TaskStatus.from_redmine_id(status_id) == expected

    def test_from_redmine_id_unknown_returns_new(self) -> None:
        """未知のステータス ID の場合は NEW を返す。"""
        assert TaskStatus.from_redmine_id(999) == TaskStatus.NEW


class TestTaskStatusToRedmineId:
    """to_redmine_id メソッドのテスト。"""

    @pytest.mark.parametrize(
        "status, expected_id",
        [
            (TaskStatus.NEW, 1),
            (TaskStatus.IN_PROGRESS, 2),
            (TaskStatus.RESOLVED, 3),
            (TaskStatus.CLOSED, 4),
            (TaskStatus.REJECTED, 5),
        ],
    )
    def test_to_redmine_id(self, status: TaskStatus, expected_id: int) -> None:
        """TaskStatus から正しい Redmine ステータス ID に変換する。"""
        assert status.to_redmine_id() == expected_id


class TestTaskStatusDisplayName:
    """display_name メソッドのテスト。"""

    @pytest.mark.parametrize(
        "status, expected_name",
        [
            (TaskStatus.NEW, "新規"),
            (TaskStatus.IN_PROGRESS, "進行中"),
            (TaskStatus.RESOLVED, "解決済み"),
            (TaskStatus.CLOSED, "完了"),
            (TaskStatus.REJECTED, "却下"),
        ],
    )
    def test_display_name(self, status: TaskStatus, expected_name: str) -> None:
        """日本語表示名を正しく返す。"""
        assert status.display_name() == expected_name
