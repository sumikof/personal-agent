"""TaskCreateService の単体テスト（TDD: TC-005〜TC-011）。"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.application.task.task_create_service import TaskCreateService
from app.domain.exceptions import (
    RedmineConnectionError,
    RedmineNotFoundError,
    TaskValidationError,
)


class TestCreateTaskSuccess:
    """TC-005: タスク作成成功（正常系）"""

    @pytest.mark.asyncio
    async def test_create_task_success(
        self,
        mock_redmine_adapter: AsyncMock,
        task_create_service: TaskCreateService,
    ) -> None:
        """
        Given: 有効なタスク作成パラメータと Redmine アダプターのモック
        When: create_task を呼び出す
        Then: タスクが作成され、正しいデータが返る
        """
        # Given
        title = "設計書レビュー"
        project_id = 1
        mock_redmine_adapter.create_issue.return_value = {
            "issue": {
                "id": 124,
                "subject": title,
                "status": {"id": 1, "name": "新規"},
                "priority": {"id": 2, "name": "通常"},
                "due_date": None,
                "created_on": "2026-03-03T10:00:00Z",
            }
        }

        # When
        result = await task_create_service.create_task(
            title=title,
            project_id=project_id,
        )

        # Then
        assert result["id"] == "124"
        assert result["title"] == title
        assert "url" in result
        assert "124" in result["url"]
        mock_redmine_adapter.create_issue.assert_called_once()


class TestCreateTaskValidation:
    """バリデーションエラーのテスト"""

    @pytest.mark.asyncio
    async def test_create_task_with_empty_title_raises_validation_error(
        self,
        task_create_service: TaskCreateService,
    ) -> None:
        """TC-006: タイトル空文字列でバリデーションエラー
        Given: 空文字列のタイトル
        When: create_task を呼び出す
        Then: TaskValidationError が発生する（field="title"）
        """
        # When / Then
        with pytest.raises(TaskValidationError) as exc_info:
            await task_create_service.create_task(title="")

        assert exc_info.value.field == "title"
        assert "必須" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_create_task_with_title_exceeding_max_length_raises_validation_error(
        self,
        task_create_service: TaskCreateService,
    ) -> None:
        """TC-007: タイトル 201 文字でバリデーションエラー
        Given: 201 文字のタイトル（最大 200 文字を超過）
        When: create_task を呼び出す
        Then: TaskValidationError が発生する
        """
        # Given
        long_title = "あ" * 201  # 201文字（制限超過）

        # When / Then
        with pytest.raises(TaskValidationError) as exc_info:
            await task_create_service.create_task(title=long_title)

        assert exc_info.value.field == "title"
        assert "200文字" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_create_task_with_invalid_priority_raises_validation_error(
        self,
        task_create_service: TaskCreateService,
    ) -> None:
        """TC-008: 不正な優先度でバリデーションエラー
        Given: 有効でない優先度文字列（"critical"）
        When: create_task を呼び出す
        Then: TaskValidationError が発生する（field="priority"）
        """
        # When / Then
        with pytest.raises(TaskValidationError) as exc_info:
            await task_create_service.create_task(
                title="テストタスク",
                priority="critical",  # 無効な優先度
            )

        assert exc_info.value.field == "priority"


class TestCreateTaskErrors:
    """エラー伝播のテスト"""

    @pytest.mark.asyncio
    async def test_create_task_when_redmine_unavailable_raises_connection_error(
        self,
        mock_redmine_adapter: AsyncMock,
        task_create_service: TaskCreateService,
    ) -> None:
        """TC-009: Redmine 接続失敗で RedmineConnectionError が伝播
        Given: Redmine アダプターが RedmineConnectionError を発生させる
        When: create_task を呼び出す
        Then: RedmineConnectionError が呼び出し元に伝播する
        """
        # Given
        mock_redmine_adapter.create_issue.side_effect = RedmineConnectionError()

        # When / Then
        with pytest.raises(RedmineConnectionError):
            await task_create_service.create_task(title="テストタスク")

    @pytest.mark.asyncio
    async def test_create_task_with_nonexistent_project_raises_not_found_error(
        self,
        mock_redmine_adapter: AsyncMock,
        task_create_service: TaskCreateService,
    ) -> None:
        """TC-010: 存在しないプロジェクト ID で RedmineNotFoundError が伝播
        Given: 存在しないプロジェクト ID（9999）を指定
        When: create_task を呼び出す
        Then: RedmineNotFoundError が発生する
        """
        # Given
        mock_redmine_adapter.create_issue.side_effect = RedmineNotFoundError(
            "プロジェクト ID 9999 が見つかりません"
        )

        # When / Then
        with pytest.raises(RedmineNotFoundError):
            await task_create_service.create_task(
                title="テストタスク",
                project_id=9999,
            )


class TestCreateTaskPriorityConversion:
    """TC-011: 優先度名称を ID に正しく変換する"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "priority_name, expected_priority_id",
        [
            ("low", 1),
            ("normal", 2),
            ("high", 3),
            ("urgent", 4),
        ],
    )
    async def test_create_task_converts_priority_name_to_id(
        self,
        priority_name: str,
        expected_priority_id: int,
        mock_redmine_adapter: AsyncMock,
        task_create_service: TaskCreateService,
    ) -> None:
        """
        Given: 優先度名称文字列
        When: create_task を呼び出す
        Then: RedmineAdapter が正しい優先度 ID で呼ばれる
        """
        # Given
        mock_redmine_adapter.create_issue.return_value = {
            "issue": {
                "id": 124,
                "subject": "テスト",
                "status": {"id": 1, "name": "新規"},
                "priority": {"id": expected_priority_id, "name": ""},
                "due_date": None,
                "created_on": "2026-03-03T10:00:00Z",
            }
        }

        # When
        await task_create_service.create_task(
            title="テスト",
            priority=priority_name,
        )

        # Then
        mock_redmine_adapter.create_issue.assert_called_once()
        call_kwargs = mock_redmine_adapter.create_issue.call_args.kwargs
        assert call_kwargs["priority_id"] == expected_priority_id
