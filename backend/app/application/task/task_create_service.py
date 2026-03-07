"""タスク作成アプリケーションサービス。"""
from __future__ import annotations

import logging

from app.config import get_settings
from app.domain.exceptions import TaskValidationError
from app.infra.redmine.redmine_adapter import RedmineAdapter

logger = logging.getLogger(__name__)

PRIORITY_NAME_TO_ID: dict[str, int] = {
    "low": 1,
    "normal": 2,
    "high": 3,
    "urgent": 4,
}


class TaskCreateService:
    """タスク作成のユースケースを実装するサービスクラス。

    ビジネスロジックの検証と Redmine への登録を担う。
    """

    def __init__(self, redmine_adapter: RedmineAdapter) -> None:
        self._redmine_adapter = redmine_adapter

    async def create_task(
        self,
        title: str,
        description: str | None = None,
        priority: str = "normal",
        due_date: str | None = None,
        project_id: int = 1,
    ) -> dict:
        """タスクを作成して Redmine に登録する。

        Args:
            title: タスクタイトル（必須・最大200文字）。
            description: タスクの詳細説明（任意）。
            priority: 優先度（"low"/"normal"/"high"/"urgent"）。
            due_date: 期日（YYYY-MM-DD 形式）。
            project_id: Redmine プロジェクト ID。

        Returns:
            作成されたタスクの情報辞書。キー: id, title, status, priority,
            due_date, project_id, url, created_at。

        Raises:
            TaskValidationError: 入力値が不正な場合。
            RedmineConnectionError: Redmine への接続に失敗した場合。
            RedmineAPIError: Redmine API がエラーを返した場合。
        """
        # バリデーション
        self._validate_input(title=title, priority=priority, project_id=project_id)

        # 優先度 ID 変換
        priority_id = PRIORITY_NAME_TO_ID.get(priority, 2)

        logger.info(
            "task_create_service_create_started title=%s project_id=%d priority_id=%d",
            title[:50],
            project_id,
            priority_id,
        )

        # Redmine への登録
        response = await self._redmine_adapter.create_issue(
            subject=title,
            project_id=project_id,
            description=description,
            priority_id=priority_id,
            due_date=due_date,
        )

        # 結果の変換
        result = self._build_task_response(response, project_id=project_id)

        logger.info("task_create_service_create_succeeded task_id=%s", result["id"])

        return result

    def _validate_input(
        self,
        title: str,
        priority: str,
        project_id: int,
    ) -> None:
        """入力値のバリデーションを実施する。

        Raises:
            TaskValidationError: バリデーション違反がある場合。
        """
        if not title or not title.strip():
            raise TaskValidationError(
                "タスクタイトルは必須です",
                field="title",
            )
        if len(title) > 200:
            raise TaskValidationError(
                f"タスクタイトルは200文字以内で入力してください（現在: {len(title)} 文字）",
                field="title",
            )
        if priority not in PRIORITY_NAME_TO_ID:
            raise TaskValidationError(
                f"優先度の値が不正です: {priority}。low/normal/high/urgent のいずれかを指定してください",
                field="priority",
            )
        if project_id < 1:
            raise TaskValidationError(
                f"プロジェクト ID は 1 以上の整数を指定してください: {project_id}",
                field="project_id",
            )

    def _build_task_response(self, redmine_response: dict, project_id: int) -> dict:
        """Redmine API レスポンスをアプリケーション内部の辞書形式に変換する。"""
        issue = redmine_response.get("issue", redmine_response)
        issue_id = str(issue["id"])
        settings = get_settings()

        return {
            "id": issue_id,
            "title": issue["subject"],
            "status": issue.get("status", {}).get("name", "新規"),
            "priority": issue.get("priority", {}).get("name", "通常"),
            "due_date": issue.get("due_date"),
            "project_id": project_id,
            "url": f"{settings.redmine_url}/issues/{issue_id}",
            "created_at": issue.get("created_on"),
        }
