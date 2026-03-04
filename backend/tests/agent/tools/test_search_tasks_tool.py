"""search_tasks_tool 関数の単体テスト（FEAT-002）。"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agent.tools.search_tasks_tool import search_tasks_tool, _format_markdown_list


@pytest.fixture
def sample_tasks() -> list[dict]:
    return [
        {
            "id": "123",
            "title": "設計書レビュー",
            "priority": "high",
            "due_date": "2026-03-03",
            "url": "http://localhost:8080/issues/123",
            "status": "新規",
            "description": "...",
            "project_id": 1,
            "project_name": "テスト",
            "created_at": "2026-02-20T09:00:00Z",
            "updated_at": "2026-03-01T14:30:00Z",
        },
        {
            "id": "124",
            "title": "API テスト実施",
            "priority": "normal",
            "due_date": "2026-03-03",
            "url": "http://localhost:8080/issues/124",
            "status": "新規",
            "description": None,
            "project_id": 1,
            "project_name": "テスト",
            "created_at": "2026-02-22T10:00:00Z",
            "updated_at": "2026-03-02T09:00:00Z",
        },
    ]


class TestSearchTasksTool:
    """search_tasks_tool 関数の単体テスト。"""

    @pytest.mark.asyncio
    async def test_search_tasks_tool_with_open_status_returns_markdown_list(
        self, sample_tasks: list[dict]
    ):
        """TC-001: status="open"、due_date あり → Markdown タスク一覧を返す
        Given: status="open", due_date="2026-03-03" を指定
        When:  search_tasks_tool を呼び出す
        Then:  Markdown 形式のタスク一覧文字列が返る
        """
        # Given
        mock_service = MagicMock()
        mock_service.search_tasks = AsyncMock(return_value=sample_tasks)

        with patch(
            "app.agent.tools.search_tasks_tool.TaskSearchService",
            return_value=mock_service,
        ), patch("app.agent.tools.search_tasks_tool.RedmineAdapter"), patch(
            "app.agent.tools.search_tasks_tool.get_settings"
        ):
            # When
            result = await search_tasks_tool.ainvoke(
                {"status": "open", "due_date": "2026-03-03"}
            )

        # Then
        assert isinstance(result, str)
        assert "タスク一覧" in result
        assert "設計書レビュー" in result
        assert "http://localhost:8080/issues/123" in result

    @pytest.mark.asyncio
    async def test_search_tasks_tool_with_no_results_returns_empty_message(self):
        """TC-002: 0 件の場合 → 「該当するタスクはありません」を返す
        Given: 検索結果が 0 件
        When:  search_tasks_tool を呼び出す
        Then:  「該当するタスクはありません」を含む文字列が返る
        """
        # Given
        mock_service = MagicMock()
        mock_service.search_tasks = AsyncMock(return_value=[])

        with patch(
            "app.agent.tools.search_tasks_tool.TaskSearchService",
            return_value=mock_service,
        ), patch("app.agent.tools.search_tasks_tool.RedmineAdapter"), patch(
            "app.agent.tools.search_tasks_tool.get_settings"
        ):
            # When
            result = await search_tasks_tool.ainvoke({"keyword": "存在しないタスク"})

        # Then
        assert "該当するタスクはありません" in result
        assert "存在しないタスク" in result

    @pytest.mark.asyncio
    async def test_search_tasks_tool_when_connection_error_returns_error_message(self):
        """TC-003: Redmine 接続エラー → エラーメッセージ文字列を返す（例外を上げない）
        Given: Redmine が接続不能
        When:  search_tasks_tool を呼び出す
        Then:  エラーメッセージ文字列が返る（例外を上げず LLM に渡す）
        """
        # Given
        from app.domain.exceptions import RedmineConnectionError

        mock_service = MagicMock()
        mock_service.search_tasks = AsyncMock(
            side_effect=RedmineConnectionError("接続タイムアウト")
        )

        with patch(
            "app.agent.tools.search_tasks_tool.TaskSearchService",
            return_value=mock_service,
        ), patch("app.agent.tools.search_tasks_tool.RedmineAdapter"), patch(
            "app.agent.tools.search_tasks_tool.get_settings"
        ):
            # When
            result = await search_tasks_tool.ainvoke({})

        # Then
        assert "失敗" in result
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_search_tasks_tool_clamps_limit_to_100(self):
        """TC-004: limit=200 → min(200, 100) = 100 件で呼び出す
        Given: limit=200 を指定（最大値を超える）
        When:  search_tasks_tool を呼び出す
        Then:  TaskSearchService.search_tasks が limit=100 で呼ばれる
        """
        # Given
        mock_service = MagicMock()
        mock_service.search_tasks = AsyncMock(return_value=[])

        with patch(
            "app.agent.tools.search_tasks_tool.TaskSearchService",
            return_value=mock_service,
        ), patch("app.agent.tools.search_tasks_tool.RedmineAdapter"), patch(
            "app.agent.tools.search_tasks_tool.get_settings"
        ):
            # When
            await search_tasks_tool.ainvoke({"limit": 200})

        # Then
        call_kwargs = mock_service.search_tasks.call_args.kwargs
        assert call_kwargs["limit"] == 100

    @pytest.mark.asyncio
    async def test_search_tasks_tool_with_long_keyword_does_not_raise(self):
        """TC-005: keyword が 30 文字を超える場合でもログエラーは出ない
        Given: 100 文字のキーワードを指定
        When:  search_tasks_tool を呼び出す
        Then:  正常に処理される
        """
        # Given
        mock_service = MagicMock()
        mock_service.search_tasks = AsyncMock(return_value=[])

        with patch(
            "app.agent.tools.search_tasks_tool.TaskSearchService",
            return_value=mock_service,
        ), patch("app.agent.tools.search_tasks_tool.RedmineAdapter"), patch(
            "app.agent.tools.search_tasks_tool.get_settings"
        ):
            # When
            result = await search_tasks_tool.ainvoke({"keyword": "あ" * 100})

        # Then
        assert isinstance(result, str)


class TestFormatMarkdownList:
    """_format_markdown_list 関数の単体テスト。"""

    def test_format_markdown_list_returns_numbered_list(self):
        """TC-006: 3 件のタスク → 番号付き Markdown リストを返す
        Given: 3 件のタスクリスト
        When:  _format_markdown_list を呼び出す
        Then:  「1.」「2.」「3.」で始まる Markdown テキストが返る
        """
        # Given
        tasks = [
            {
                "id": "1",
                "title": "タスクA",
                "priority": "high",
                "due_date": "2026-03-03",
                "url": "http://localhost:8080/issues/1",
                "status": "新規",
            },
            {
                "id": "2",
                "title": "タスクB",
                "priority": "normal",
                "due_date": None,
                "url": "http://localhost:8080/issues/2",
                "status": "新規",
            },
            {
                "id": "3",
                "title": "タスクC",
                "priority": "urgent",
                "due_date": "2026-03-05",
                "url": "http://localhost:8080/issues/3",
                "status": "進行中",
            },
        ]

        # When
        result = _format_markdown_list(tasks)

        # Then
        assert "1. " in result
        assert "2. " in result
        assert "3. " in result
        assert "タスクA" in result
        assert "タスクB" in result
        assert "タスクC" in result

    def test_format_markdown_list_high_priority_shows_bold(self):
        """TC-007: 高優先度タスク → **高** で太字表示される"""
        tasks = [
            {
                "id": "1",
                "title": "緊急タスク",
                "priority": "high",
                "due_date": None,
                "url": "http://localhost:8080/issues/1",
                "status": "新規",
            }
        ]
        result = _format_markdown_list(tasks)
        assert "**高**" in result

    def test_format_markdown_list_due_date_in_header_when_specified(self):
        """TC-008: due_date を指定した場合 → ヘッダーに期限が表示される"""
        tasks = [
            {
                "id": "1",
                "title": "タスクA",
                "priority": "normal",
                "due_date": "2026-03-03",
                "url": "http://localhost:8080/issues/1",
                "status": "新規",
            }
        ]
        result = _format_markdown_list(tasks, due_date="2026-03-03")
        assert "2026-03-03 期限" in result

    def test_format_markdown_list_no_due_date_filter_shows_generic_header(self):
        """TC-009: due_date なし → 汎用ヘッダーが表示される"""
        tasks = [
            {
                "id": "1",
                "title": "タスクA",
                "priority": "normal",
                "due_date": None,
                "url": "http://localhost:8080/issues/1",
                "status": "新規",
            }
        ]
        result = _format_markdown_list(tasks, due_date=None)
        assert "タスク一覧" in result
        assert "期限" not in result
