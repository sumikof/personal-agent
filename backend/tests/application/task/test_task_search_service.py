"""TaskSearchService 単体テスト（FEAT-002 TDD: TC-010〜TC-020）。"""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.task.task_search_service import TaskSearchService, STATUS_MAP
from app.domain.exceptions import RedmineConnectionError


class TestTaskSearchServiceSearchTasks:
    """TaskSearchService.search_tasks の単体テスト。"""

    # ------------------------------------------------------------------ #
    # TC-010: status="open" → list_issues が status_id="open" で呼ばれる   #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_with_open_status_calls_adapter_with_correct_params(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: status="open" で検索
        When:  search_tasks を呼び出す
        Then:  RedmineAdapter.list_issues が status_id="open" で呼ばれ 3 件返る
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = sample_redmine_issues_response

        # When
        result = await task_search_service.search_tasks(status="open")

        # Then
        assert len(result) == 3
        call_kwargs = mock_redmine_adapter.list_issues.call_args.kwargs
        assert call_kwargs["status_id"] == "open"

    # ------------------------------------------------------------------ #
    # TC-011: status="all" → status_id="*" でAdapterが呼ばれる             #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_with_all_status_maps_to_asterisk(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        empty_redmine_response: dict,
    ):
        """
        Given: status="all" で検索
        When:  search_tasks を呼び出す
        Then:  RedmineAdapter.list_issues が status_id="*" で呼ばれる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = empty_redmine_response

        # When
        await task_search_service.search_tasks(status="all")

        # Then
        call_kwargs = mock_redmine_adapter.list_issues.call_args.kwargs
        assert call_kwargs["status_id"] == "*"

    # ------------------------------------------------------------------ #
    # TC-012: status=None → デフォルト status_id="open" で呼ばれる          #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_with_no_status_defaults_to_open(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        empty_redmine_response: dict,
    ):
        """
        Given: status=None（フィルタなし）
        When:  search_tasks を呼び出す
        Then:  RedmineAdapter.list_issues が status_id="open" で呼ばれる（デフォルト）
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = empty_redmine_response

        # When
        await task_search_service.search_tasks(status=None)

        # Then
        call_kwargs = mock_redmine_adapter.list_issues.call_args.kwargs
        assert call_kwargs["status_id"] == "open"

    # ------------------------------------------------------------------ #
    # TC-013: due_date 指定あり → adapter に due_date が渡される             #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_with_due_date_passes_to_adapter(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: due_date="2026-03-03" を指定
        When:  search_tasks を呼び出す
        Then:  RedmineAdapter.list_issues が due_date="2026-03-03" で呼ばれる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = sample_redmine_issues_response

        # When
        await task_search_service.search_tasks(due_date="2026-03-03")

        # Then
        call_kwargs = mock_redmine_adapter.list_issues.call_args.kwargs
        assert call_kwargs["due_date"] == "2026-03-03"

    # ------------------------------------------------------------------ #
    # TC-014: keyword 指定あり → adapter に subject_like が渡される          #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_with_keyword_passes_subject_like_to_adapter(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        empty_redmine_response: dict,
    ):
        """
        Given: keyword="設計書" を指定
        When:  search_tasks を呼び出す
        Then:  RedmineAdapter.list_issues が subject_like="設計書" で呼ばれる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = empty_redmine_response

        # When
        await task_search_service.search_tasks(keyword="設計書")

        # Then
        call_kwargs = mock_redmine_adapter.list_issues.call_args.kwargs
        assert call_kwargs["subject_like"] == "設計書"

    # ------------------------------------------------------------------ #
    # TC-015: Redmine 接続エラー → RedmineConnectionError が伝播する         #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_when_connection_error_propagates_exception(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
    ):
        """
        Given: Redmine への接続に失敗する
        When:  search_tasks を呼び出す
        Then:  RedmineConnectionError が伝播する
        """
        # Given
        mock_redmine_adapter.list_issues.side_effect = RedmineConnectionError(
            "接続タイムアウト"
        )

        # When / Then
        with pytest.raises(RedmineConnectionError):
            await task_search_service.search_tasks(status="open")

    # ------------------------------------------------------------------ #
    # TC-016: 結果を内部形式に変換 → priority.id=3 が "high" に変換される    #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_converts_priority_id_to_name(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: Redmine レスポンスに priority.id=3 のタスクが含まれる
        When:  search_tasks を呼び出す
        Then:  変換後のタスクの priority が "high" になる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = sample_redmine_issues_response

        # When
        result = await task_search_service.search_tasks()

        # Then
        assert result[0]["priority"] == "high"

    # ------------------------------------------------------------------ #
    # TC-017: 結果の URL → "{REDMINE_URL}/issues/{id}" 形式              #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_generates_correct_url(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: Redmine レスポンスに id=123 のタスクが含まれる
        When:  search_tasks を呼び出す
        Then:  変換後のタスクの url が 正しい形式になる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = sample_redmine_issues_response

        # When
        with pytest.MonkeyPatch.context() as mp:
            import app.application.task.task_search_service as svc_module
            mock_settings = MagicMock()
            mock_settings.redmine_url = "http://localhost:8080"
            mp.setattr(svc_module, "get_settings", lambda: mock_settings)
            result = await task_search_service.search_tasks()

        # Then
        assert result[0]["url"] == "http://localhost:8080/issues/123"


class TestBuildRedmineParams:
    """TaskSearchService._build_redmine_params の単体テスト。"""

    # ------------------------------------------------------------------ #
    # TC-018: 全パラメータ指定 → すべてのパラメータが dict に含まれる          #
    # ------------------------------------------------------------------ #
    def test_build_redmine_params_with_all_params(
        self, task_search_service: TaskSearchService
    ):
        """
        Given: status, due_date, keyword, project_id, limit を全指定
        When:  _build_redmine_params を呼び出す
        Then:  すべてのパラメータが dict に含まれる
        """
        # When
        params = task_search_service._build_redmine_params(
            status="closed",
            due_date="2026-03-03",
            keyword="設計書",
            project_id=1,
            limit=50,
        )

        # Then
        assert params["status_id"] == "closed"
        assert params["due_date"] == "2026-03-03"
        assert params["subject_like"] == "設計書"
        assert params["project_id"] == 1
        assert params["limit"] == 50

    # ------------------------------------------------------------------ #
    # TC-019: limit=200 → 100 にクランプされる                               #
    # ------------------------------------------------------------------ #
    def test_build_redmine_params_clamps_limit_to_100(
        self, task_search_service: TaskSearchService
    ):
        """
        Given: limit=200（最大値超え）
        When:  _build_redmine_params を呼び出す
        Then:  params["limit"] が 100 になる
        """
        # When
        params = task_search_service._build_redmine_params(
            status=None, due_date=None, keyword=None, project_id=None, limit=200
        )

        # Then
        assert params["limit"] == 100

    # ------------------------------------------------------------------ #
    # TC-020: status マッピング（open/closed/all）                           #
    # ------------------------------------------------------------------ #
    @pytest.mark.parametrize("status_input,expected_status_id", [
        ("open", "open"),
        ("closed", "closed"),
        ("all", "*"),
    ])
    def test_build_redmine_params_status_mapping(
        self,
        task_search_service: TaskSearchService,
        status_input: str,
        expected_status_id: str,
    ):
        """
        Given: status が "open" / "closed" / "all" のいずれか
        When:  _build_redmine_params を呼び出す
        Then:  status_id が Redmine の正しい値に変換される
        """
        # When
        params = task_search_service._build_redmine_params(
            status=status_input, due_date=None, keyword=None, project_id=None, limit=25
        )

        # Then
        assert params["status_id"] == expected_status_id
