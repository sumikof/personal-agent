"""Redmine タスク作成ツール関数。"""
from __future__ import annotations

import logging

from app.application.task.task_create_service import TaskCreateService
from app.config import get_settings
from app.infra.redmine.redmine_adapter import RedmineAdapter

logger = logging.getLogger(__name__)


async def create_task_tool(
    title: str,
    description: str = "",
    priority: str = "normal",
    due_date: str = "",
    project_id: int = 1,
) -> str:
    """Redmine に新しいタスク（チケット）を作成する。

    Args:
        title: タスクのタイトル（必須・最大200文字）。
        description: タスクの詳細説明（任意）。
        priority: 優先度（"low", "normal", "high", "urgent"）。デフォルトは "normal"。
        due_date: 期日（YYYY-MM-DD 形式、任意）。
        project_id: Redmine プロジェクト ID（デフォルト: 1）。

    Returns:
        タスク作成結果のメッセージ文字列。作成成功時はチケット URL を含む。
        エラー時はエラーメッセージ文字列を返す（例外は発生しない）。

    Examples:
        >>> result = await create_task_tool(
        ...     title="設計書レビュー",
        ...     description="DSD-001 の詳細設計書をレビューする",
        ...     priority="high",
        ...     due_date="2026-03-31",
        ... )
        >>> print(result)
        タスクを作成しました。
        - ID: 124
        - タイトル: 設計書レビュー
        - 優先度: 高
        - 期日: 2026-03-31
        - URL: http://localhost:8080/issues/124
    """
    logger.info(
        "create_task_tool_called title=%s priority=%s project_id=%d has_due_date=%s",
        title[:50],
        priority,
        project_id,
        bool(due_date),
    )

    settings = get_settings()
    adapter = RedmineAdapter(
        base_url=settings.redmine_url,
        api_key=settings.redmine_api_key,
    )
    service = TaskCreateService(redmine_adapter=adapter)

    try:
        result = await service.create_task(
            title=title,
            description=description or None,
            priority=priority,
            due_date=due_date or None,
            project_id=project_id,
        )

        logger.info(
            "create_task_tool_succeeded task_id=%s title=%s",
            result["id"],
            title[:50],
        )

        priority_display = {
            "low": "低",
            "normal": "通常",
            "high": "高",
            "urgent": "緊急",
        }.get(priority, priority)

        lines = [
            "タスクを作成しました。",
            f"- ID: {result['id']}",
            f"- タイトル: {result['title']}",
            f"- 優先度: {priority_display}",
        ]
        if result.get("due_date"):
            lines.append(f"- 期日: {result['due_date']}")
        lines.append(f"- URL: {result['url']}")

        return "\n".join(lines)

    except Exception as e:
        logger.error(
            "create_task_tool_failed error=%s title=%s",
            str(e),
            title[:50],
        )
        return f"タスクの作成に失敗しました。エラー: {str(e)}"
