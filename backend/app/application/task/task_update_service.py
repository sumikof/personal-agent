"""タスク更新アプリケーションサービス（FEAT-003）。

DSD-001_FEAT-003 の 8.1 に従い実装する。
UC-003（タスクのステータス更新）と UC-004（タスクへのコメント追加）を提供する。
"""
from __future__ import annotations

import logging

from app.domain.exceptions import (
    InvalidStatusIdError,
    TaskDeleteOperationForbiddenError,
    TaskNotFoundError,
)
from app.domain.task.task_update import TaskUpdate
from app.domain.task.value_objects import TaskStatusVO
from app.infra.redmine.redmine_adapter import RedmineAdapter

logger = logging.getLogger(__name__)


class TaskUpdateService:
    """タスク更新のユースケースを調整するアプリケーションサービス。

    UC-003: タスクのステータスを更新する。
    UC-004: タスクにコメントを追加する。

    依存性注入により RedmineAdapter を受け取ることでテスト可能にする。
    """

    def __init__(self, redmine_adapter: RedmineAdapter) -> None:
        self._redmine_adapter = redmine_adapter

    def _prevent_delete_operation(self, operation: str) -> None:
        """削除操作の試行を検出し、例外を発生させる（多層防御の最終層・BR-02）。

        Args:
            operation: 実行しようとしている操作名。

        Raises:
            TaskDeleteOperationForbiddenError: 削除操作が検出された場合。
        """
        if "delete" in operation.lower() or "destroy" in operation.lower():
            logger.warning("task_delete_operation_blocked operation=%s", operation)
            raise TaskDeleteOperationForbiddenError()

    async def update_task_status(
        self,
        issue_id: int,
        status_id: int,
        notes: str | None = None,
    ) -> TaskUpdate:
        """タスクのステータスを更新する（UC-003）。

        Args:
            issue_id: Redmine の Issue ID。
            status_id: 新しいステータスID（環境変数で設定した有効値のいずれか）。
            notes: ステータス変更時のコメント（任意）。

        Returns:
            更新後の TaskUpdate エンティティ。

        Raises:
            InvalidStatusIdError: status_id が有効範囲外の場合。
            TaskNotFoundError: 指定された issue_id のタスクが存在しない場合。
            RedmineConnectionError: Redmine との接続に失敗した場合。
            TaskDeleteOperationForbiddenError: 削除操作が検出された場合（BR-02）。
        """
        # BR-02: 削除操作の事前チェック（多層防御）
        self._prevent_delete_operation("update_status")

        # ステータスIDの検証
        if not TaskStatusVO.validate_id(status_id):
            logger.warning("invalid_status_id_rejected status_id=%d", status_id)
            raise InvalidStatusIdError(
                status_id=status_id,
                valid_ids=TaskStatusVO.get_valid_ids(),
            )

        # チケット存在確認
        await self._validate_issue_exists(issue_id)

        logger.info(
            "task_update_status_started issue_id=%d status_id=%d",
            issue_id,
            status_id,
        )

        # Redmine API 呼び出し
        payload: dict = {"issue": {"status_id": status_id}}
        if notes:
            payload["issue"]["notes"] = notes

        response = await self._redmine_adapter.update_issue(issue_id, payload)
        result = TaskUpdate.from_redmine_response(response)

        logger.info(
            "task_update_status_succeeded issue_id=%d new_status=%s",
            issue_id,
            result.status.name,
        )

        return result

    async def add_task_comment(self, issue_id: int, notes: str) -> TaskUpdate:
        """タスクにコメントを追加する（UC-004）。

        Args:
            issue_id: Redmine の Issue ID。
            notes: 追加するコメント内容。

        Returns:
            更新後の TaskUpdate エンティティ。

        Raises:
            ValueError: notes が空文字列またはスペースのみの場合。
            TaskNotFoundError: 指定された issue_id のタスクが存在しない場合。
            RedmineConnectionError: Redmine との接続に失敗した場合。
            TaskDeleteOperationForbiddenError: 削除操作が検出された場合（BR-02）。
        """
        # BR-02: 削除操作の事前チェック（多層防御）
        self._prevent_delete_operation("add_comment")

        # コメント内容の検証
        if not notes or not notes.strip():
            raise ValueError("コメント内容は空にできません")

        # チケット存在確認
        await self._validate_issue_exists(issue_id)

        logger.info("task_add_comment_started issue_id=%d", issue_id)

        # Redmine API 呼び出し（notes のみ更新）
        payload = {"issue": {"notes": notes}}
        response = await self._redmine_adapter.update_issue(issue_id, payload)
        result = TaskUpdate.from_redmine_response(response)

        logger.info("task_add_comment_succeeded issue_id=%d", issue_id)

        return result

    async def _validate_issue_exists(self, issue_id: int) -> None:
        """指定された issue_id のタスクが存在するかを確認する。

        Raises:
            TaskNotFoundError: タスクが存在しない場合。
        """
        try:
            await self._redmine_adapter.get_issue(issue_id)
        except TaskNotFoundError:
            raise
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                raise TaskNotFoundError(issue_id)
            raise
