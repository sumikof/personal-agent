"""タスクダッシュボードサービス（FEAT-006）。"""
from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from app.task.domain.adapters import RedmineAdapter
from app.task.domain.models import TaskSummary

logger = logging.getLogger(__name__)

# 1 ページあたりの最大取得件数（Redmine API の上限）
PAGE_SIZE = 100

# ステータスグループ定義（Kanban ビュー用）
STATUS_GROUPS: dict[str, list[str]] = {
    "todo": ["new"],
    "in_progress": ["in_progress", "feedback"],
    "done": ["resolved", "closed", "rejected"],
}

# urgency のソート順（小さい値が優先）
URGENCY_ORDER: dict[str, int] = {
    "overdue": 0,
    "high": 1,
    "medium": 2,
    "normal": 3,
}


class TaskDashboardService:
    """タスク一覧ダッシュボードのユースケースを実装するサービスクラス。

    Redmine からタスクを取得し、変換・フィルタリング・ソートを担う。
    """

    def __init__(self, redmine_client: object) -> None:
        self.redmine_client = redmine_client
        self.adapter = RedmineAdapter()

    async def get_tasks(
        self,
        status_filter: Optional[str] = None,
        urgency_filter: Optional[str] = None,
    ) -> list[TaskSummary]:
        """Redmine から全タスクを取得し、変換・フィルタリングして返す。

        Args:
            status_filter: ステータスフィルタ（"new", "in_progress", "resolved" 等）。
            urgency_filter: 緊急度フィルタ（"overdue", "high", "medium", "normal"）。

        Returns:
            urgency 優先度順にソートされた TaskSummary のリスト。

        Raises:
            RedmineConnectionError: Redmine への接続が失敗した場合。
        """
        logger.info("TaskDashboardService.get_tasks started")

        # 全件取得（ページネーション対応）
        issues = await self._fetch_all_issues()
        logger.info("Fetched %d issues from Redmine", len(issues))

        # 今日の日付を取得（patch できるよう date.today() を直接参照）
        today = date.today()

        # Redmine Issue → TaskSummary に変換
        tasks = self.adapter.to_task_summaries(issues, today)

        # フィルタリング
        tasks = self._apply_filters(tasks, status_filter, urgency_filter)

        # urgency の優先度順にソート（overdue → high → medium → normal）
        tasks.sort(
            key=lambda t: (
                URGENCY_ORDER.get(t.urgency, 99),
                t.due_date or "9999-12-31",
            )
        )

        logger.info(
            "TaskDashboardService.get_tasks completed: %d tasks returned",
            len(tasks),
        )
        return tasks

    async def _fetch_all_issues(self) -> list[dict]:
        """ページネーションを考慮して Redmine から全件取得する。

        Redmine API の最大取得件数は 100 件/リクエストのため、
        total_count が 100 を超える場合は複数回リクエストする。
        """
        all_issues: list[dict] = []
        offset = 0

        while True:
            response = await self.redmine_client.get_issues({
                "status_id": "*",  # 全ステータス（オープン・クローズ含む）
                "limit": PAGE_SIZE,
                "offset": offset,
            })
            issues: list[dict] = response.get("issues", [])
            all_issues.extend(issues)

            total_count: int = response.get("total_count", 0)
            offset += PAGE_SIZE

            if offset >= total_count:
                break

        return all_issues

    def _apply_filters(
        self,
        tasks: list[TaskSummary],
        status_filter: Optional[str],
        urgency_filter: Optional[str],
    ) -> list[TaskSummary]:
        """ステータスと緊急度でタスクをフィルタリングする。"""
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        if urgency_filter:
            tasks = [t for t in tasks if t.urgency == urgency_filter]
        return tasks

    async def get_tasks_grouped(self) -> dict[str, list[TaskSummary]]:
        """全タスクをステータスグループ別に分類して返す。

        Returns:
            {
                "todo": [...],         # 未着手（new）
                "in_progress": [...],  # 進行中（in_progress, feedback）
                "done": [...]          # 完了（resolved, closed, rejected）
            }
        """
        all_tasks = await self.get_tasks()

        grouped: dict[str, list[TaskSummary]] = {
            "todo": [],
            "in_progress": [],
            "done": [],
        }

        for task in all_tasks:
            placed = False
            for group_name, statuses in STATUS_GROUPS.items():
                if task.status in statuses:
                    grouped[group_name].append(task)
                    placed = True
                    break
            if not placed:
                # 未分類のステータスは todo に入れる
                grouped["todo"].append(task)

        return grouped
