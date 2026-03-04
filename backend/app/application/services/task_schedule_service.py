"""タスクスケジュールサービス（FEAT-004）。

DSD-001_FEAT-004 のクラス図に従い実装する。
UC-005（優先度変更）・UC-006（期日変更）のユースケースを担う。
"""
from __future__ import annotations

import logging
from datetime import date

from app.domain.exceptions import InvalidPriorityError
from app.domain.task.entities import Task
from app.domain.task.value_objects import TaskPriorityVO

logger = logging.getLogger(__name__)


class TaskScheduleService:
    """タスクの優先度・期日変更を担うアプリケーションサービス（FEAT-004）。

    DSD-001_FEAT-004 セクション 3 のクラス図に従う。

    Args:
        redmine_adapter: Redmine REST API アダプター。
    """

    def __init__(self, redmine_adapter) -> None:
        self._redmine_adapter = redmine_adapter

    async def update_task_priority(self, issue_id: int, priority_id: int) -> Task:
        """タスクの優先度を変更する（UC-005）。

        Args:
            issue_id: 変更対象の Redmine Issue ID。
            priority_id: 新しい優先度 ID（1=低/2=通常/3=高/4=緊急/5=即座に）。

        Returns:
            更新後の Task エンティティ。

        Raises:
            InvalidPriorityError: priority_id が有効範囲外（{1,2,3,4,5} 以外）の場合。
            TaskNotFoundError: 指定した Issue が存在しない場合。
            RedmineConnectionError: Redmine への接続に失敗した場合。
            RedmineAPIError: Redmine API がエラーを返した場合。
        """
        self._validate_priority_id(priority_id)

        logger.info(
            "task_schedule_update_priority issue_id=%d priority_id=%d",
            issue_id,
            priority_id,
        )

        response = await self._redmine_adapter.update_issue_priority(issue_id, priority_id)
        return Task.from_redmine_response(response)

    async def update_task_due_date(self, issue_id: int, due_date: date) -> Task:
        """タスクの期日を変更する（UC-006）。

        Args:
            issue_id: 変更対象の Redmine Issue ID。
            due_date: 新しい期日（date オブジェクト）。

        Returns:
            更新後の Task エンティティ。

        Raises:
            TaskNotFoundError: 指定した Issue が存在しない場合。
            RedmineConnectionError: Redmine への接続に失敗した場合。
            RedmineAPIError: Redmine API がエラーを返した場合。
        """
        logger.info(
            "task_schedule_update_due_date issue_id=%d due_date=%s",
            issue_id,
            due_date.isoformat(),
        )

        response = await self._redmine_adapter.update_issue_due_date(issue_id, due_date)
        return Task.from_redmine_response(response)

    def _validate_priority_id(self, priority_id: int) -> None:
        """優先度 ID が有効範囲内かを検証する。

        Args:
            priority_id: 検証対象の優先度 ID。

        Raises:
            InvalidPriorityError: priority_id が {1,2,3,4,5} 以外の場合。
        """
        if not TaskPriorityVO.validate_id(priority_id):
            raise InvalidPriorityError(priority_id)
