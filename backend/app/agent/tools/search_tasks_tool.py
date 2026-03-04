"""タスク検索ツール関数（FEAT-002）。"""
from __future__ import annotations

import logging

from langchain_core.tools import tool

from app.application.task.task_search_service import TaskSearchService
from app.config import get_settings
from app.infra.redmine.redmine_adapter import RedmineAdapter

logger = logging.getLogger(__name__)


@tool
async def search_tasks_tool(
    status: str = "",
    due_date: str = "",
    keyword: str = "",
    project_id: int = 0,
    limit: int = 25,
) -> str:
    """Redmine からタスク（チケット）一覧を検索して返す。

    Args:
        status: 検索するタスクのステータス。
            - "open": 未完了（新規・進行中）のタスク
            - "closed": 完了したタスク
            - "all": すべてのタスク
            - 空文字: フィルタなし（デフォルト: "open"）
        due_date: 期日でフィルタ（YYYY-MM-DD 形式）。
            指定した日付が期日のタスクを取得する。
            空文字の場合はフィルタなし。
        keyword: タイトルでの検索キーワード（部分一致）。
            空文字の場合はフィルタなし。
        project_id: Redmine プロジェクト ID でフィルタ。
            0 または未指定の場合はフィルタなし（全プロジェクト）。
        limit: 取得件数の上限（デフォルト: 25, 最大: 100）。

    Returns:
        Markdown 形式のタスク一覧文字列。
        タスクが見つからない場合は「該当するタスクはありません」を返す。
    """
    logger.info(
        "search_tasks_tool_called status=%s due_date=%s keyword=%s project_id=%d limit=%d",
        status,
        due_date,
        keyword[:30] if keyword else None,
        project_id,
        limit,
    )

    settings = get_settings()
    adapter = RedmineAdapter(
        base_url=settings.redmine_url,
        api_key=settings.redmine_api_key,
    )
    service = TaskSearchService(redmine_adapter=adapter)

    try:
        tasks = await service.search_tasks(
            status=status or None,
            due_date=due_date or None,
            keyword=keyword or None,
            project_id=project_id if project_id > 0 else None,
            limit=min(limit, 100),
        )

        logger.info("search_tasks_tool_succeeded result_count=%d", len(tasks))

        if not tasks:
            conditions = []
            if status:
                conditions.append(f"ステータス='{status}'")
            if due_date:
                conditions.append(f"期日='{due_date}'")
            if keyword:
                conditions.append(f"キーワード='{keyword}'")
            condition_str = (
                f"（検索条件: {', '.join(conditions)}）" if conditions else ""
            )
            return f"該当するタスクはありません{condition_str}"

        return _format_markdown_list(tasks, due_date=due_date or None)

    except Exception as e:
        logger.error("search_tasks_tool_failed error=%s", str(e))
        return f"タスクの検索に失敗しました。エラー: {str(e)}"


def _format_markdown_list(tasks: list[dict], due_date: str | None = None) -> str:
    """タスク一覧を Markdown 形式にフォーマットする。"""
    count = len(tasks)
    title_suffix = f"（{due_date} 期限）" if due_date else ""
    header = f"## タスク一覧{title_suffix}（{count}件）\n\n"

    priority_display = {
        "low": "低",
        "normal": "通常",
        "high": "**高**",
        "urgent": "**🔴 緊急**",
        "immediate": "**🆘 即座に**",
    }

    lines = [header]
    for i, task in enumerate(tasks, start=1):
        priority_label = priority_display.get(task.get("priority", "normal"), "通常")
        due = task.get("due_date")
        due_str = f" - 期日: {due}" if due else ""
        url = task.get("url", "#")
        title = task.get("title", "（タイトルなし）")
        status = task.get("status", "")

        line = f"{i}. [{title}]({url}) - {priority_label}{due_str}"
        if status and status not in ("新規", "open"):
            line += f" [{status}]"
        lines.append(line)

    return "\n".join(lines)
