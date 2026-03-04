"""RedmineAdapter.list_issues 単体テスト（FEAT-002 TDD: TC-021〜TC-028）。"""
from __future__ import annotations

import pytest
import httpx
from pytest_httpx import HTTPXMock

from app.infra.redmine.redmine_adapter import RedmineAdapter
from app.domain.exceptions import (
    RedmineConnectionError,
    RedmineAuthError,
    RedmineNotFoundError,
    RedmineAPIError,
)

REDMINE_URL = "http://localhost:8080"
API_KEY = "test_api_key"
ISSUES_URL = f"{REDMINE_URL}/issues.json"


@pytest.fixture
def redmine_adapter() -> RedmineAdapter:
    return RedmineAdapter(base_url=REDMINE_URL, api_key=API_KEY)


class TestRedmineAdapterListIssues:
    """RedmineAdapter.list_issues の単体テスト（pytest-httpx を使用）。"""

    # ------------------------------------------------------------------ #
    # TC-021: 正常系 → 200 OK でチケット一覧が返る                           #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_returns_issues_on_success(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: Redmine が 200 OK と issues 配列を返す
        When:  list_issues を呼び出す
        Then:  issues 配列と total_count が返る
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=ISSUES_URL,
            match_params={"status_id": "open", "limit": "25", "offset": "0"},
            json=sample_redmine_issues_response,
            status_code=200,
        )

        # When
        result = await redmine_adapter.list_issues(status_id="open", limit=25)

        # Then
        assert len(result["issues"]) == 3
        assert result["total_count"] == 3

    # ------------------------------------------------------------------ #
    # TC-022: due_date パラメータ → URL に含まれる                           #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_sends_due_date_in_query(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: due_date="2026-03-03" を指定
        When:  list_issues を呼び出す
        Then:  HTTP リクエストのクエリパラメータに due_date=2026-03-03 が含まれる
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=ISSUES_URL,
            match_params={"status_id": "open", "limit": "25", "offset": "0", "due_date": "2026-03-03"},
            json=sample_redmine_issues_response,
            status_code=200,
        )

        # When
        await redmine_adapter.list_issues(due_date="2026-03-03")

        # Then
        request = httpx_mock.get_requests()[0]
        assert "due_date=2026-03-03" in str(request.url)

    # ------------------------------------------------------------------ #
    # TC-023: subject_like パラメータ → URL に subject=keyword が含まれる    #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_maps_subject_like_to_subject_param(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
        empty_redmine_response: dict,
    ):
        """
        Given: subject_like="設計書" を指定
        When:  list_issues を呼び出す
        Then:  HTTP リクエストのクエリパラメータに subject=設計書（URLエンコード済み）が含まれる
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=ISSUES_URL,
            match_params={"status_id": "open", "limit": "25", "offset": "0", "subject": "設計書"},
            json=empty_redmine_response,
            status_code=200,
        )

        # When
        await redmine_adapter.list_issues(subject_like="設計書")

        # Then
        request = httpx_mock.get_requests()[0]
        assert "subject=" in str(request.url)

    # ------------------------------------------------------------------ #
    # TC-024: 401 Unauthorized → RedmineAuthError を上げる（リトライなし）   #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_raises_auth_error_on_401(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
    ):
        """
        Given: Redmine が 401 Unauthorized を返す
        When:  list_issues を呼び出す
        Then:  RedmineAuthError が発生する（リトライなし）
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=ISSUES_URL,
            match_params={"status_id": "open", "limit": "25", "offset": "0"},
            status_code=401,
        )

        # When / Then
        with pytest.raises(RedmineAuthError):
            await redmine_adapter.list_issues()

    # ------------------------------------------------------------------ #
    # TC-025: 404 Not Found → RedmineNotFoundError を上げる                 #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_raises_not_found_error_on_404(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
    ):
        """
        Given: Redmine が 404 Not Found を返す（存在しない project_id）
        When:  list_issues を呼び出す
        Then:  RedmineNotFoundError が発生する
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=ISSUES_URL,
            match_params={"status_id": "open", "limit": "25", "offset": "0", "project_id": "9999"},
            status_code=404,
        )

        # When / Then
        with pytest.raises(RedmineNotFoundError):
            await redmine_adapter.list_issues(project_id=9999)

    # ------------------------------------------------------------------ #
    # TC-026: ConnectError × 3 回 → RedmineConnectionError（3リトライ後）   #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_raises_connection_error_after_3_retries(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
    ):
        """
        Given: Redmine が ConnectError を 3 回連続で発生させる
        When:  list_issues を呼び出す
        Then:  RedmineConnectionError が発生する（3 回リトライ後）
        """
        # Given: 3 回のリクエストすべてで ConnectError
        httpx_mock.add_exception(httpx.ConnectError("接続失敗"), is_reusable=True)

        # When / Then
        with pytest.raises(RedmineConnectionError):
            await redmine_adapter.list_issues()

    # ------------------------------------------------------------------ #
    # TC-027: API キーが X-Redmine-API-Key ヘッダに含まれる                   #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_sends_api_key_in_header(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
        empty_redmine_response: dict,
    ):
        """
        Given: API キーを設定した RedmineAdapter
        When:  list_issues を呼び出す
        Then:  HTTP リクエストヘッダに X-Redmine-API-Key が含まれる
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=ISSUES_URL,
            match_params={"status_id": "open", "limit": "25", "offset": "0"},
            json=empty_redmine_response,
            status_code=200,
        )

        # When
        await redmine_adapter.list_issues()

        # Then
        request = httpx_mock.get_requests()[0]
        assert request.headers["X-Redmine-API-Key"] == API_KEY

    # ------------------------------------------------------------------ #
    # TC-028: 5xx エラー 3 回 → RedmineConnectionError（3リトライ後）         #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_retries_on_500_error(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
    ):
        """
        Given: Redmine が 500 Internal Server Error を 3 回連続で返す
        When:  list_issues を呼び出す
        Then:  RedmineConnectionError が発生する（3 回リトライ後）
        """
        # Given: 3回のリトライに対応するため3回分追加
        for _ in range(3):
            httpx_mock.add_response(
                url=ISSUES_URL,
                match_params={"status_id": "open", "limit": "25", "offset": "0"},
                status_code=500,
            )

        # When / Then
        with pytest.raises(RedmineConnectionError):
            await redmine_adapter.list_issues()
