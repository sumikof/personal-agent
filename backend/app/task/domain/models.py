"""タスクダッシュボード ドメインモデル（FEAT-006 専用 DTO）。

FEAT-006（タスク一覧ダッシュボード）で使用する読み取り専用 DTO。
FEAT-001〜005 で使用する Task エンティティ（app/domain/task/task.py）とは別物。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Optional


class TaskUrgency(str, Enum):
    """タスクの緊急度値オブジェクト。

    due_date と今日の日付から算出する。
    """

    OVERDUE = "overdue"  # 期限超過
    HIGH = "high"        # 期日迫る（0〜3日）
    MEDIUM = "medium"    # 今週中（4〜7日）
    NORMAL = "normal"    # 通常（8日以上、または期日なし）

    @classmethod
    def from_due_date(cls, due_date_str: Optional[str], today: date) -> "TaskUrgency":
        """due_date と today から緊急度を判定する。

        Args:
            due_date_str: 期日文字列（"YYYY-MM-DD" 形式）または None。
            today: 今日の日付（テスト時に任意の日付を渡せるよう引数で受け取る）。

        Returns:
            TaskUrgency
        """
        if due_date_str is None:
            return cls.NORMAL

        try:
            due_date = date.fromisoformat(due_date_str)
        except ValueError:
            return cls.NORMAL

        days_diff = (due_date - today).days

        if days_diff < 0:
            return cls.OVERDUE       # 期限超過
        elif days_diff <= 3:
            return cls.HIGH          # 期日迫る（0〜3日）
        elif days_diff <= 7:
            return cls.MEDIUM        # 今週中（4〜7日）
        else:
            return cls.NORMAL        # 通常（8日以上）


@dataclass(frozen=True)
class TaskSummary:
    """タスクダッシュボード表示用 DTO（読み取り専用）。

    Redmine の Issue データをダッシュボード表示に最適化した軽量モデル。
    urgency・status_label・redmine_url などダッシュボード専用フィールドを持つ。
    """

    id: int
    title: str
    status: str
    status_label: str
    priority: str
    priority_label: str
    assignee_name: Optional[str]
    due_date: Optional[str]
    urgency: str
    redmine_url: str
    created_at: str
    updated_at: str

    def is_overdue(self) -> bool:
        """期限超過かどうかを返す。"""
        return self.urgency == TaskUrgency.OVERDUE.value

    def days_until_due(self) -> Optional[int]:
        """今日から期日までの日数を返す（期日なしの場合は None）。"""
        if self.due_date is None:
            return None
        try:
            due = date.fromisoformat(self.due_date)
            return (due - date.today()).days
        except ValueError:
            return None
