"""タスク値オブジェクト（FEAT-003/004）。

DSD-001_FEAT-003/004 に従い実装する。
既存の TaskStatus Enum (task_status.py) は FEAT-001/002 互換のため残置し、
本モジュールは FEAT-003/004（タスク更新・優先度・スケジュール調整）専用の値オブジェクトを提供する。

FEAT-004 追加:
  - TaskPriority: TaskPriorityVO の別名（from_id/validate_id メソッドを持つ）
  - DueDate: 期日を表す値オブジェクト（is_past/days_until/is_within_week メソッドを持つ）
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

from app.domain.exceptions import InvalidStatusIdError


@dataclass(frozen=True)
class TaskStatusVO:
    """タスクのステータスを表す値オブジェクト（FEAT-003）。

    Redmine のステータス定義は環境ごとに異なるため、
    ステータスIDは環境変数 REDMINE_STATUS_ID_* で設定可能にする。
    ハードコードは禁止。環境変数が未設定の場合のみデフォルト値を使用する。

    環境変数:
        REDMINE_STATUS_ID_OPEN: 未着手ステータスのID（デフォルト: 1）
        REDMINE_STATUS_ID_IN_PROGRESS: 進行中ステータスのID（デフォルト: 2）
        REDMINE_STATUS_ID_CLOSED: 完了ステータスのID（デフォルト: 3）
        REDMINE_STATUS_ID_REJECTED: 却下ステータスのID（デフォルト: 5）
    """

    id: int
    name: str

    @classmethod
    def _build_status_map(cls) -> dict[int, "TaskStatusVO"]:
        """環境変数からステータスIDマッピングを構築する。

        lru_cache を使用しないのは、テスト時に環境変数を動的に変更できるようにするため。
        """
        open_id = int(os.getenv("REDMINE_STATUS_ID_OPEN", "1"))
        in_progress_id = int(os.getenv("REDMINE_STATUS_ID_IN_PROGRESS", "2"))
        closed_id = int(os.getenv("REDMINE_STATUS_ID_CLOSED", "3"))
        rejected_id = int(os.getenv("REDMINE_STATUS_ID_REJECTED", "5"))
        return {
            open_id: cls(id=open_id, name="未着手"),
            in_progress_id: cls(id=in_progress_id, name="進行中"),
            closed_id: cls(id=closed_id, name="完了"),
            rejected_id: cls(id=rejected_id, name="却下"),
        }

    @classmethod
    def from_id(cls, status_id: int) -> "TaskStatusVO":
        """ステータスIDから TaskStatusVO を生成する。

        Args:
            status_id: Redmine のステータスID。

        Returns:
            対応する TaskStatusVO。

        Raises:
            ValueError: status_id が有効範囲外の場合。
        """
        mapping = cls._build_status_map()
        if status_id not in mapping:
            raise ValueError(
                f"無効なステータスID: {status_id}。有効値: {list(mapping.keys())}"
            )
        return mapping[status_id]

    @classmethod
    def validate_id(cls, status_id: int) -> bool:
        """ステータスIDが有効範囲内かを検証する。

        Args:
            status_id: 検証対象のステータスID。

        Returns:
            有効な場合は True、無効な場合は False。
        """
        return status_id in cls._build_status_map()

    @classmethod
    def get_valid_ids(cls) -> set[int]:
        """有効なステータスID の集合を返す。"""
        return set(cls._build_status_map().keys())


@dataclass(frozen=True)
class TaskPriorityVO:
    """タスクの優先度を表す値オブジェクト（FEAT-003）。

    Redmine のデフォルト優先度 ID (1-5) に対応する。
    """

    id: int
    name: str

    _PRIORITY_MAP: dict[int, "TaskPriorityVO"] = None  # type: ignore[assignment]

    @classmethod
    def _get_priority_map(cls) -> dict[int, "TaskPriorityVO"]:
        return {
            1: cls(id=1, name="低"),
            2: cls(id=2, name="通常"),
            3: cls(id=3, name="高"),
            4: cls(id=4, name="緊急"),
            5: cls(id=5, name="即座に"),
        }

    @classmethod
    def from_id(cls, priority_id: int) -> "TaskPriorityVO":
        """優先度IDから TaskPriorityVO を生成する。

        Args:
            priority_id: Redmine の優先度ID。

        Returns:
            対応する TaskPriorityVO。

        Raises:
            ValueError: priority_id が有効範囲外の場合。エラーメッセージに「無効な優先度ID」を含む。
        """
        mapping = cls._get_priority_map()
        if priority_id not in mapping:
            raise ValueError(f"無効な優先度ID: {priority_id}。有効値: {{1, 2, 3, 4, 5}}")
        return mapping[priority_id]

    @classmethod
    def validate_id(cls, priority_id: int) -> bool:
        """優先度IDが有効範囲内かを検証する。

        Args:
            priority_id: 検証対象の優先度ID。

        Returns:
            有効な場合は True、無効な場合は False。
        """
        return priority_id in cls._get_priority_map()


# FEAT-004: TaskPriority は TaskPriorityVO の別名として公開する
TaskPriority = TaskPriorityVO


@dataclass(frozen=True)
class DueDate:
    """タスクの期日を表す値オブジェクト（FEAT-004）。

    is_past / days_until / is_within_week メソッドにより、
    ドメインロジックで期日判定を行う。
    """

    value: date

    def __post_init__(self) -> None:
        """date 型以外の値が渡された場合に TypeError を発生させる。"""
        if not isinstance(self.value, date):
            raise TypeError(
                f"DueDateはdate型を受け付けます（受け取った型: {type(self.value).__name__}）。"
                "文字列ではなくdateオブジェクトを渡してください。"
            )

    def is_past(self, reference_date: date) -> bool:
        """参照日より前（過去）かどうかを判定する。

        Args:
            reference_date: 判定の基準日。

        Returns:
            参照日より前の場合は True、参照日当日または未来の場合は False。
        """
        return self.value < reference_date

    def days_until(self, reference_date: date) -> int:
        """参照日から期日までの日数を返す。

        Args:
            reference_date: 判定の基準日。

        Returns:
            期日 - 参照日の日数差。負数は超過を表す。
        """
        return (self.value - reference_date).days

    def is_within_week(self, reference_date: date) -> bool:
        """参照日から7日以内（0〜7日）に期日が含まれるかを判定する。

        Args:
            reference_date: 判定の基準日。

        Returns:
            期日が参照日以降かつ7日以内の場合は True、それ以外は False。
        """
        days = self.days_until(reference_date)
        return 0 <= days <= 7
