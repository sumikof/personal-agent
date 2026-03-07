"""TaskStatus 値オブジェクト。"""
from __future__ import annotations

from enum import Enum


class TaskStatus(str, Enum):
    """タスクのステータスを表す値オブジェクト。

    Redmine のデフォルトステータスに対応する。
    """

    NEW = "new"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REJECTED = "rejected"

    @classmethod
    def from_redmine_id(cls, status_id: int) -> TaskStatus:
        """Redmine のステータス ID から TaskStatus を生成する。

        未知のステータス ID の場合はデフォルトで NEW を返す。
        """
        _MAPPING: dict[int, TaskStatus] = {
            1: cls.NEW,
            2: cls.IN_PROGRESS,
            3: cls.RESOLVED,
            4: cls.CLOSED,
            5: cls.REJECTED,
        }
        return _MAPPING.get(status_id, cls.NEW)

    def to_redmine_id(self) -> int:
        """Redmine のステータス ID に変換する。"""
        _MAPPING: dict[TaskStatus, int] = {
            TaskStatus.NEW: 1,
            TaskStatus.IN_PROGRESS: 2,
            TaskStatus.RESOLVED: 3,
            TaskStatus.CLOSED: 4,
            TaskStatus.REJECTED: 5,
        }
        return _MAPPING[self]

    def display_name(self) -> str:
        """日本語表示名を返す。"""
        _DISPLAY: dict[TaskStatus, str] = {
            TaskStatus.NEW: "新規",
            TaskStatus.IN_PROGRESS: "進行中",
            TaskStatus.RESOLVED: "解決済み",
            TaskStatus.CLOSED: "完了",
            TaskStatus.REJECTED: "却下",
        }
        return _DISPLAY[self]
