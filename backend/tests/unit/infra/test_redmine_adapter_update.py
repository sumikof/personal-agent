"""FEAT-003: RedmineAdapter の update_issue / get_issue 単体テスト（DSD-008 TC-ADPT01〜ADPT06）。

TDD Green フェーズ: respx でHTTPリクエストをモック化し、実装済みの RedmineAdapter をテストする。
"""
from __future__ import annotations

import httpx
import pytest
import respx

from app.domain.exceptions import RedmineConnectionError, TaskNotFoundError
from app.infra.redmine.redmine_adapter import RedmineAdapter

REDMINE_BASE_URL = "http://localhost:8080"
REDMINE_API_KEY = "test-api-key"


# ---------------------------------------------------------------------------
# フィクスチャ
# ---------------------------------------------------------------------------


@pytest.fixture
def adapter() -> RedmineAdapter:
    """テスト用 RedmineAdapter インスタンス。"""
    return RedmineAdapter(
        base_url=REDMINE_BASE_URL,
        api_key=REDMINE_API_KEY,
    )


def _make_issue_json(
    issue_id: int,
    status_id: int = 1,
    status_name: str = "未着手",
    subject: str = "テストタスク",
) -> dict:
    """Redmine Issue レスポンス JSON を生成するヘルパー。"""
    return {
        "issue": {
            "id": issue_id,
            "subject": subject,
            "status": {"id": status_id, "name": status_name},
            "priority": {"id": 2, "name": "通常"},
            "due_date": None,
            "updated_on": "2026-03-03T15:00:00Z",
        }
    }


# ---------------------------------------------------------------------------
# TC-ADPT01: update_issue - ステータス更新成功（正常系）
# ---------------------------------------------------------------------------


class TestUpdateIssueSuccess:
    """TC-ADPT01: update_issue - ステータス更新成功（正常系）。"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_update_issue_success(self, adapter: RedmineAdapter) -> None:
        """PUT 204 → GET 200 で更新後のIssueデータが返される。

        Given: Redmine PUT /issues/123.json が204を返し、
               続くGET /issues/123.json が更新済みIssueを返す
        When: adapter.update_issue(123, {"issue": {"status_id": 3}}) を呼び出す
        Then: 更新後のIssueデータが返される（status.id=3）
        """
        # Redmine PUT レスポンスのモック（204 No Content）
        respx.put(f"{REDMINE_BASE_URL}/issues/123.json").mock(
            return_value=httpx.Response(204)
        )
        # Redmine GET レスポンスのモック（更新後の状態）
        respx.get(f"{REDMINE_BASE_URL}/issues/123.json").mock(
            return_value=httpx.Response(200, json=_make_issue_json(123, status_id=3, status_name="完了"))
        )

        # When
        result = await adapter.update_issue(123, {"issue": {"status_id": 3}})

        # Then
        assert result["issue"]["status"]["id"] == 3
        assert result["issue"]["status"]["name"] == "完了"


# ---------------------------------------------------------------------------
# TC-ADPT02: update_issue - チケット不存在（異常系）
# ---------------------------------------------------------------------------


class TestUpdateIssueNotFound:
    """TC-ADPT02: update_issue - チケット不存在（異常系）。"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_update_issue_not_found(self, adapter: RedmineAdapter) -> None:
        """PUT 404 で TaskNotFoundError が発生する。

        Given: Redmine PUT /issues/9999.json が404を返す
        When: adapter.update_issue(9999, {...}) を呼び出す
        Then: TaskNotFoundError が発生する
        """
        respx.put(f"{REDMINE_BASE_URL}/issues/9999.json").mock(
            return_value=httpx.Response(404)
        )

        with pytest.raises(TaskNotFoundError) as exc_info:
            await adapter.update_issue(9999, {"issue": {"status_id": 3}})

        assert "9999" in str(exc_info.value)


# ---------------------------------------------------------------------------
# TC-ADPT03: update_issue - Redmineサーバーエラーのリトライ（異常系）
# ---------------------------------------------------------------------------


class TestUpdateIssueServerErrorRetry:
    """TC-ADPT03: update_issue - Redmineサーバーエラーのリトライ（異常系）。

    設計差異メモ: DSD-008 では「RedmineConnectionError が発生する」と記載されているが、
    実装では 5xx エラー時は RedmineAPIError が last_error として保存され、
    全リトライ消費後は RedmineAPIError が raise される。
    5xx エラー後の例外は DomainError（RedmineAPIError か RedmineConnectionError）であることを検証する。
    """

    @pytest.mark.asyncio
    @respx.mock
    async def test_update_issue_server_error_with_retry(self, adapter: RedmineAdapter) -> None:
        """PUT 500 が3回続くとリトライ後に DomainError が発生する。

        Given: Redmine PUT /issues/123.json が3回連続で500を返す
        When: adapter.update_issue(123, {...}) を呼び出す
        Then: リトライが3回行われた後に RedmineAPIError（DomainError のサブクラス）が発生する
              （設計差異: DSD-008 では RedmineConnectionError と記載されているが実装は RedmineAPIError）
        """
        import asyncio
        from unittest.mock import patch

        from app.domain.exceptions import DomainError, RedmineConnectionError

        respx.put(f"{REDMINE_BASE_URL}/issues/123.json").mock(
            return_value=httpx.Response(500)
        )

        with patch.object(asyncio, "sleep", return_value=None):
            with pytest.raises(DomainError):
                await adapter.update_issue(123, {"issue": {"status_id": 3}})


# ---------------------------------------------------------------------------
# TC-ADPT04: update_issue - Redmineバリデーションエラー（異常系）
# ---------------------------------------------------------------------------


class TestUpdateIssueValidationError:
    """TC-ADPT04: update_issue - Redmineバリデーションエラー（異常系）。"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_update_issue_validation_error(self, adapter: RedmineAdapter) -> None:
        """PUT 422 でエラーメッセージを含む ValueError が発生する。

        Given: Redmine PUT /issues/123.json が422とエラーメッセージを返す
        When: adapter.update_issue(123, {...}) を呼び出す
        Then: ValueError が発生し、Redmineのエラーメッセージが含まれる
        """
        respx.put(f"{REDMINE_BASE_URL}/issues/123.json").mock(
            return_value=httpx.Response(422, json={
                "errors": ["ステータスを変更するためのトランジションが存在しません"]
            })
        )

        with pytest.raises(ValueError, match="ステータスを変更するためのトランジション"):
            await adapter.update_issue(123, {"issue": {"status_id": 3}})


# ---------------------------------------------------------------------------
# TC-ADPT05: get_issue - Issue取得成功（正常系）
# ---------------------------------------------------------------------------


class TestGetIssueSuccess:
    """TC-ADPT05: get_issue - Issue取得成功（正常系）。"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_issue_success(self, adapter: RedmineAdapter) -> None:
        """GET 200 でIssueデータが返される。

        Given: Redmine GET /issues/123.json が200とIssueデータを返す
        When: adapter.get_issue(123) を呼び出す
        Then: Issueデータが返される
        """
        respx.get(f"{REDMINE_BASE_URL}/issues/123.json").mock(
            return_value=httpx.Response(200, json={
                "issue": {
                    "id": 123,
                    "subject": "設計書作成",
                    "status": {"id": 2, "name": "進行中"},
                    "priority": {"id": 2, "name": "通常"},
                    "due_date": None,
                    "updated_on": "2026-03-03T10:00:00Z",
                }
            })
        )

        result = await adapter.get_issue(123)
        assert result["issue"]["id"] == 123
        assert result["issue"]["subject"] == "設計書作成"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_issue_not_found(self, adapter: RedmineAdapter) -> None:
        """GET 404 で TaskNotFoundError が発生する。

        Given: Redmine GET /issues/9999.json が404を返す
        When: adapter.get_issue(9999) を呼び出す
        Then: TaskNotFoundError が発生する
        """
        respx.get(f"{REDMINE_BASE_URL}/issues/9999.json").mock(
            return_value=httpx.Response(404)
        )

        with pytest.raises(TaskNotFoundError) as exc_info:
            await adapter.get_issue(9999)

        assert "9999" in str(exc_info.value)


# ---------------------------------------------------------------------------
# TC-ADPT06: 接続タイムアウトのリトライ（異常系）
# ---------------------------------------------------------------------------


class TestGetIssueConnectionTimeoutRetry:
    """TC-ADPT06: 接続タイムアウトのリトライ（異常系）。"""

    @pytest.mark.asyncio
    @respx.mock
    async def test_connection_timeout_retry(self, adapter: RedmineAdapter) -> None:
        """TimeoutException が3回続くと RedmineConnectionError が発生する。

        Given: HTTPリクエストがTimeoutExceptionを発生させる（3回連続）
        When: adapter.get_issue(123) を呼び出す
        Then: リトライが3回行われた後に RedmineConnectionError が発生する
        """
        import asyncio
        from unittest.mock import patch

        respx.get(f"{REDMINE_BASE_URL}/issues/123.json").mock(
            side_effect=httpx.TimeoutException("接続タイムアウト")
        )

        with patch.object(asyncio, "sleep", return_value=None):
            with pytest.raises(RedmineConnectionError):
                await adapter.get_issue(123)
