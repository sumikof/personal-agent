"""タスク検索アプリケーションサービス（FEAT-002）。"""
from __future__ import annotations

import logging

from app.config import get_settings
from app.infra.redmine.redmine_adapter import RedmineAdapter

logger = logging.getLogger(__name__)

MAX_LIMIT = 100

# ステータス文字列 → Redmine status_id パラメータのマッピング
STATUS_MAP: dict[str, str] = {
    "open": "open",
    "closed": "closed",
    "all": "*",
}

# Redmine 優先度 ID → 内部優先度文字列のマッピング
PRIORITY_ID_TO_NAME: dict[int, str] = {
    1: "low",
    2: "normal",
    3: "high",
    4: "urgent",
    5: "immediate",
}


class TaskSearchService:
    """Redmine チケット検索のユースケースを実装するサービスクラス。

    検索パラメータの変換・Redmine API 呼び出し・結果の内部形式への変換を担う。
    """

    def __init__(self, redmine_adapter: RedmineAdapter) -> None:
        self._redmine_adapter = redmine_adapter

    async def search_tasks(
        self,
        status: str | None = "open",
        due_date: str | None = None,
        keyword: str | None = None,
        project_id: int | None = None,
        limit: int = 25,
    ) -> list[dict]:
        """Redmine チケットを検索して内部形式のリストを返す。

        Args:
            status: ステータスフィルタ（"open"/"closed"/"all"）。デフォルト: "open"。
            due_date: 期日フィルタ（YYYY-MM-DD 形式）。
            keyword: タイトル部分一致検索キーワード。
            project_id: Redmine プロジェクト ID フィルタ。
            limit: 取得件数上限（最大 100）。デフォルト: 25。

        Returns:
            タスク情報の辞書リスト。各辞書のキー:
            id, title, status, priority, due_date, url,
            description, project_id, project_name, created_at, updated_at。

        Raises:
            RedmineConnectionError: Redmine への接続に失敗した場合。
            RedmineAuthError: Redmine API キーが無効な場合。
            RedmineAPIError: その他の Redmine API エラーの場合。
        """
        params = self._build_redmine_params(
            status=status,
            due_date=due_date,
            keyword=keyword,
            project_id=project_id,
            limit=limit,
        )

        logger.info(
            "task_search_service_search_started status=%s due_date=%s keyword=%s limit=%d",
            status,
            due_date,
            keyword[:30] if keyword else None,
            params["limit"],
        )

        response = await self._redmine_adapter.list_issues(**params)

        issues = response.get("issues", [])
        result = [self._format_task(issue) for issue in issues]

        logger.info(
            "task_search_service_search_succeeded count=%d total=%d",
            len(result),
            response.get("total_count", 0),
        )

        return result

    def _build_redmine_params(
        self,
        status: str | None,
        due_date: str | None,
        keyword: str | None,
        project_id: int | None,
        limit: int,
    ) -> dict:
        """Redmine API パラメータ辞書を構築する。

        Args:
            status: ステータスフィルタ文字列。
            due_date: 期日フィルタ。
            keyword: タイトル部分一致キーワード。
            project_id: プロジェクト ID フィルタ。
            limit: 取得件数上限。

        Returns:
            RedmineAdapter.list_issues に渡すキーワード引数辞書。
        """
        # status のデフォルト値処理と Redmine パラメータへの変換
        effective_status = status if status is not None else "open"
        status_id = STATUS_MAP.get(effective_status, effective_status)

        # limit のクランプ
        clamped_limit = min(limit, MAX_LIMIT)

        params: dict = {
            "status_id": status_id,
            "limit": clamped_limit,
        }

        if due_date is not None:
            params["due_date"] = due_date
        if keyword is not None:
            params["subject_like"] = keyword
        if project_id is not None:
            params["project_id"] = project_id

        return params

    def _format_task(self, issue: dict) -> dict:
        """Redmine API レスポンスの Issue を内部形式の辞書に変換する。

        Args:
            issue: Redmine API レスポンスの issue オブジェクト。

        Returns:
            内部形式のタスク辞書。
        """
        settings = get_settings()
        issue_id = str(issue["id"])

        priority_id = issue.get("priority", {}).get("id", 2)
        priority_name = PRIORITY_ID_TO_NAME.get(priority_id, "normal")

        return {
            "id": issue_id,
            "title": issue["subject"],
            "status": issue.get("status", {}).get("name", ""),
            "priority": priority_name,
            "due_date": issue.get("due_date"),
            "url": f"{settings.redmine_url}/issues/{issue_id}",
            "description": issue.get("description") or None,
            "project_id": issue.get("project", {}).get("id"),
            "project_name": issue.get("project", {}).get("name", ""),
            "created_at": issue.get("created_on"),
            "updated_at": issue.get("updated_on"),
        }
