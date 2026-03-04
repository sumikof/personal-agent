"""TaskPriority 値オブジェクトの単体テスト。"""
from __future__ import annotations

import pytest

from app.domain.task.task_priority import TaskPriority


class TestTaskPriorityFromRedmineId:
    """from_redmine_id クラスメソッドのテスト。"""

    @pytest.mark.parametrize(
        "priority_id, expected",
        [
            (1, TaskPriority.LOW),
            (2, TaskPriority.NORMAL),
            (3, TaskPriority.HIGH),
            (4, TaskPriority.URGENT),
        ],
    )
    def test_from_redmine_id_known_ids(self, priority_id: int, expected: TaskPriority) -> None:
        """既知の優先度 ID から正しい TaskPriority を生成する。"""
        assert TaskPriority.from_redmine_id(priority_id) == expected

    def test_from_redmine_id_unknown_returns_normal(self) -> None:
        """未知の優先度 ID の場合は NORMAL を返す。"""
        assert TaskPriority.from_redmine_id(999) == TaskPriority.NORMAL


class TestTaskPriorityToRedmineId:
    """to_redmine_id メソッドのテスト。"""

    @pytest.mark.parametrize(
        "priority, expected_id",
        [
            (TaskPriority.LOW, 1),
            (TaskPriority.NORMAL, 2),
            (TaskPriority.HIGH, 3),
            (TaskPriority.URGENT, 4),
        ],
    )
    def test_to_redmine_id(self, priority: TaskPriority, expected_id: int) -> None:
        """TaskPriority から正しい Redmine 優先度 ID に変換する。"""
        assert priority.to_redmine_id() == expected_id


class TestTaskPriorityFromString:
    """from_string クラスメソッドのテスト。"""

    @pytest.mark.parametrize(
        "name, expected",
        [
            ("low", TaskPriority.LOW),
            ("normal", TaskPriority.NORMAL),
            ("high", TaskPriority.HIGH),
            ("urgent", TaskPriority.URGENT),
        ],
    )
    def test_from_string_valid_names(self, name: str, expected: TaskPriority) -> None:
        """有効な優先度名称から正しい TaskPriority を生成する。"""
        assert TaskPriority.from_string(name) == expected

    def test_from_string_invalid_raises_value_error(self) -> None:
        """無効な優先度名称の場合は ValueError を発生させる。"""
        with pytest.raises(ValueError):
            TaskPriority.from_string("critical")
