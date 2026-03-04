"""TaskPriority 値オブジェクト。"""
from __future__ import annotations

from enum import Enum


class TaskPriority(str, Enum):
    """タスクの優先度を表す値オブジェクト。

    Redmine のデフォルト優先度に対応する。
    """

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

    @classmethod
    def from_redmine_id(cls, priority_id: int) -> TaskPriority:
        """Redmine の優先度 ID から TaskPriority を生成する。

        未知の優先度 ID の場合はデフォルトで NORMAL を返す。
        """
        _MAPPING: dict[int, TaskPriority] = {
            1: cls.LOW,
            2: cls.NORMAL,
            3: cls.HIGH,
            4: cls.URGENT,
        }
        return _MAPPING.get(priority_id, cls.NORMAL)

    def to_redmine_id(self) -> int:
        """Redmine の優先度 ID に変換する。"""
        _MAPPING: dict[TaskPriority, int] = {
            TaskPriority.LOW: 1,
            TaskPriority.NORMAL: 2,
            TaskPriority.HIGH: 3,
            TaskPriority.URGENT: 4,
        }
        return _MAPPING[self]

    @classmethod
    def from_string(cls, name: str) -> TaskPriority:
        """優先度名称文字列から TaskPriority を生成する。

        Args:
            name: 優先度名称（"low"/"normal"/"high"/"urgent"）。

        Returns:
            対応する TaskPriority。

        Raises:
            ValueError: 無効な優先度名称の場合。
        """
        try:
            return cls(name.lower())
        except ValueError:
            valid = [p.value for p in cls]
            raise ValueError(
                f"無効な優先度名称: {name!r}。有効な値: {valid}"
            )

    def display_name(self) -> str:
        """日本語表示名を返す。"""
        _DISPLAY: dict[TaskPriority, str] = {
            TaskPriority.LOW: "低",
            TaskPriority.NORMAL: "通常",
            TaskPriority.HIGH: "高",
            TaskPriority.URGENT: "緊急",
        }
        return _DISPLAY[self]
