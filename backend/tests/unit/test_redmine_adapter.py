"""RedmineAdapter の単体テスト（TDD: TC-012〜TC-017）。"""
from __future__ import annotations

import pytest
import pytest_httpx
import httpx

from app.domain.exceptions import (
    RedmineAPIError,
    RedmineAuthError,
    RedmineConnectionError,
)
from app.infra.redmine.redmine_adapter import RedmineAdapter


class TestCreateIssueSuccess:
    """TC-012: タスク作成成功（正常系）"""

    @pytest.mark.asyncio
    async def test_create_issue_success(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: pytest_httpx.HTTPXMock,
    ) -> None:
        """
        Given: 正常な Redmine API レスポンス（201 Created）
        When: create_issue を呼び出す
        Then: Issue 情報の辞書が返る
        """
        # Given: Redmine API のレスポンスをモック化
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/issues.json",
            status_code=201,
            json={
                "issue": {
                    "id": 124,
                    "subject": "設計書レビュー",
                    "status": {"id": 1, "name": "新規"},
                    "priority": {"id": 3, "name": "高"},
                    "due_date": "2026-03-31",
                    "created_on": "2026-03-03T10:00:00Z",
                }
            },
        )

        # When
        result = await redmine_adapter.create_issue(
            subject="設計書レビュー",
            project_id=1,
            priority_id=3,
            due_date="2026-03-31",
        )

        # Then
        assert result["issue"]["id"] == 124
        assert result["issue"]["subject"] == "設計書レビュー"


class TestCreateIssueRetry:
    """リトライのテスト"""

    @pytest.mark.asyncio
    async def test_create_issue_connection_timeout_retries_three_times_then_raises(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: pytest_httpx.HTTPXMock,
    ) -> None:
        """TC-013: 接続タイムアウトで最大 3 回リトライして RedmineConnectionError
        Given: Redmine への接続が毎回タイムアウトする
        When: create_issue を呼び出す
        Then: 3 回リトライ後に RedmineConnectionError が発生する
        """
        # Given: 全リクエストでタイムアウトを発生させる
        httpx_mock.add_exception(httpx.ConnectTimeout("Connection timed out"))
        httpx_mock.add_exception(httpx.ConnectTimeout("Connection timed out"))
        httpx_mock.add_exception(httpx.ConnectTimeout("Connection timed out"))

        # When / Then
        with pytest.raises(RedmineConnectionError) as exc_info:
            await redmine_adapter.create_issue(
                subject="テストタスク",
                project_id=1,
            )

        assert "接続" in exc_info.value.message
        # 3 回リトライされたことを確認
        assert len(httpx_mock.get_requests()) == 3

    @pytest.mark.asyncio
    async def test_create_issue_server_error_retries_three_times(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: pytest_httpx.HTTPXMock,
    ) -> None:
        """TC-016: HTTP 503 で 3 回リトライして RedmineAPIError
        Given: Redmine が 503 Service Unavailable を返し続ける
        When: create_issue を呼び出す
        Then: 3 回リトライ後に RedmineAPIError が発生する
        """
        # Given: 3 回すべて 503 を返す
        for _ in range(3):
            httpx_mock.add_response(
                method="POST",
                url="http://localhost:8080/issues.json",
                status_code=503,
            )

        # When / Then
        with pytest.raises(RedmineAPIError):
            await redmine_adapter.create_issue(
                subject="テストタスク",
                project_id=1,
            )

        assert len(httpx_mock.get_requests()) == 3


class TestCreateIssueErrors:
    """エラーハンドリングのテスト"""

    @pytest.mark.asyncio
    async def test_create_issue_with_invalid_api_key_raises_auth_error(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: pytest_httpx.HTTPXMock,
    ) -> None:
        """TC-014: HTTP 401 で RedmineAuthError（リトライなし）
        Given: API キーが無効（Redmine が 401 Unauthorized を返す）
        When: create_issue を呼び出す
        Then: RedmineAuthError が発生する（リトライなし）
        """
        # Given
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/issues.json",
            status_code=401,
        )

        # When / Then
        with pytest.raises(RedmineAuthError):
            await redmine_adapter.create_issue(
                subject="テストタスク",
                project_id=1,
            )

        # リトライしていないことを確認（リクエストは 1 回のみ）
        assert len(httpx_mock.get_requests()) == 1

    @pytest.mark.asyncio
    async def test_create_issue_with_invalid_project_raises_api_error_with_message(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: pytest_httpx.HTTPXMock,
    ) -> None:
        """TC-015: HTTP 422 で Redmine エラーメッセージを含む RedmineAPIError
        Given: 存在しないプロジェクト ID を指定（Redmine が 422 を返す）
        When: create_issue を呼び出す
        Then: Redmine のエラーメッセージを含む RedmineAPIError が発生する
        """
        # Given
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/issues.json",
            status_code=422,
            json={"errors": ["プロジェクトを入力してください"]},
        )

        # When / Then
        with pytest.raises(RedmineAPIError) as exc_info:
            await redmine_adapter.create_issue(
                subject="テストタスク",
                project_id=99999,
            )

        assert "プロジェクト" in exc_info.value.message

    @pytest.mark.asyncio
    async def test_create_issue_includes_api_key_header(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: pytest_httpx.HTTPXMock,
    ) -> None:
        """TC-017: リクエストに X-Redmine-API-Key ヘッダーが含まれる
        Given: RedmineAdapter が初期化されている
        When: create_issue を呼び出す
        Then: X-Redmine-API-Key ヘッダーがリクエストに含まれる
        """
        # Given
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/issues.json",
            status_code=201,
            json={
                "issue": {
                    "id": 124,
                    "subject": "テスト",
                    "status": {"id": 1, "name": "新規"},
                    "priority": {"id": 2, "name": "通常"},
                    "due_date": None,
                    "created_on": "2026-03-03T10:00:00Z",
                }
            },
        )

        # When
        await redmine_adapter.create_issue(subject="テスト", project_id=1)

        # Then
        requests = httpx_mock.get_requests()
        assert len(requests) == 1
        assert "X-Redmine-API-Key" in requests[0].headers
        assert requests[0].headers["X-Redmine-API-Key"] == "test-api-key"
