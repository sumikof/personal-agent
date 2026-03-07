"""create_task_tool 関数の単体テスト（TDD: TC-001〜TC-004）。"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.agent.tools.create_task_tool import create_task_tool
from app.domain.exceptions import RedmineConnectionError


class TestCreateTaskToolSuccess:
    """TC-001: タスク作成成功（最小限の入力）"""

    @pytest.mark.asyncio
    async def test_create_task_tool_with_title_only_returns_success_message(
        self,
        mock_task_create_service: AsyncMock,
    ) -> None:
        """
        Given: タイトルのみ指定（他はデフォルト値）
        When: create_task_tool を呼び出す
        Then: 成功メッセージ（タスク ID・URL 含む）が返る
        """
        # Given
        mock_task_create_service.create_task.return_value = {
            "id": "124",
            "title": "設計書レビュー",
            "status": "新規",
            "priority": "通常",
            "due_date": None,
            "project_id": 1,
            "url": "http://localhost:8080/issues/124",
            "created_at": "2026-03-03T10:00:00Z",
        }

        # When
        result = await create_task_tool(title="設計書レビュー")

        # Then
        assert "タスクを作成しました" in result
        assert "124" in result
        assert "http://localhost:8080/issues/124" in result

    @pytest.mark.asyncio
    async def test_create_task_tool_with_all_params_returns_success_message(
        self,
        mock_task_create_service: AsyncMock,
    ) -> None:
        """TC-002: タスク作成成功（全パラメータ指定）
        Given: タイトル・説明・優先度・期日・プロジェクト ID をすべて指定
        When: create_task_tool を呼び出す
        Then: 成功メッセージに期日情報が含まれる
        """
        # Given
        mock_task_create_service.create_task.return_value = {
            "id": "125",
            "title": "API 設計レビュー",
            "status": "新規",
            "priority": "高",
            "due_date": "2026-03-31",
            "project_id": 1,
            "url": "http://localhost:8080/issues/125",
            "created_at": "2026-03-03T10:00:00Z",
        }

        # When
        result = await create_task_tool(
            title="API 設計レビュー",
            description="DSD-003 の API 詳細設計書をレビューする",
            priority="high",
            due_date="2026-03-31",
            project_id=1,
        )

        # Then
        assert "タスクを作成しました" in result
        assert "125" in result
        assert "2026-03-31" in result
        assert "高" in result

    @pytest.mark.asyncio
    async def test_create_task_tool_when_redmine_unavailable_returns_error_message(
        self,
        mock_task_create_service: AsyncMock,
    ) -> None:
        """TC-003: Redmine 接続失敗時のエラーメッセージ
        Given: Redmine が接続不可（RedmineConnectionError が発生する）
        When: create_task_tool を呼び出す
        Then: エラーメッセージ文字列が返る（例外は発生しない）
        """
        # Given
        mock_task_create_service.create_task.side_effect = RedmineConnectionError(
            "Redmine への接続に失敗しました"
        )

        # When
        result = await create_task_tool(title="テストタスク")

        # Then
        assert "失敗" in result
        assert "エラー" in result
        # 例外が発生しないことを確認（ツール関数はエラーを文字列で返す）

    @pytest.mark.asyncio
    async def test_create_task_tool_passes_correct_params_to_service(
        self,
        mock_task_create_service: AsyncMock,
    ) -> None:
        """TC-004: TaskCreateService の呼び出しパラメータ検証
        Given: 特定のパラメータで create_task_tool を呼び出す
        When: create_task_tool を呼び出す
        Then: TaskCreateService.create_task が正しいパラメータで呼ばれる
        """
        # Given
        mock_task_create_service.create_task.return_value = {
            "id": "126",
            "title": "テスト",
            "status": "新規",
            "priority": "高",
            "due_date": None,
            "project_id": 2,
            "url": "http://localhost:8080/issues/126",
            "created_at": "2026-03-03T10:00:00Z",
        }

        # When
        await create_task_tool(
            title="テスト",
            priority="high",
            project_id=2,
        )

        # Then: TaskCreateService.create_task が正しいパラメータで呼ばれる
        mock_task_create_service.create_task.assert_called_once_with(
            title="テスト",
            description=None,  # 空文字列は None に変換される
            priority="high",
            due_date=None,  # 空文字列は None に変換される
            project_id=2,
        )
