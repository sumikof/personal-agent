"""GET /api/v1/tasks エンドポイントの単体テスト（FEAT-002）。"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app


SAMPLE_ISSUE = {
    "id": 123,
    "project": {"id": 1, "name": "テスト"},
    "tracker": {"id": 1, "name": "バグ"},
    "status": {"id": 1, "name": "新規"},
    "priority": {"id": 3, "name": "高"},
    "author": {"id": 1, "name": "Admin"},
    "assigned_to": None,
    "subject": "設計書レビュー",
    "description": "詳細",
    "start_date": None,
    "due_date": "2026-03-03",
    "done_ratio": 0,
    "is_private": False,
    "estimated_hours": None,
    "created_on": "2026-02-20T09:00:00Z",
    "updated_on": "2026-03-01T14:30:00Z",
    "closed_on": None,
}


class TestGetTasksAPI:
    """GET /api/v1/tasks エンドポイントの単体テスト。"""

    @pytest.mark.asyncio
    async def test_get_tasks_returns_200_with_task_list(self):
        """TC-029: 正常系 → 200 OK でタスク一覧が返る
        Given: RedmineAdapter が 1 件の Issue を返す
        When:  GET /api/v1/tasks にリクエストする
        Then:  200 OK でタスク一覧が返る
        """
        # Given
        with patch(
            "app.api.v1.tasks.RedmineAdapter"
        ) as MockAdapter, patch(
            "app.api.v1.tasks.get_settings"
        ) as mock_settings:
            mock_adapter_instance = MagicMock()
            mock_adapter_instance.list_issues = AsyncMock(
                return_value={
                    "issues": [SAMPLE_ISSUE],
                    "total_count": 1,
                    "offset": 0,
                    "limit": 25,
                }
            )
            MockAdapter.return_value = mock_adapter_instance
            mock_settings.return_value.redmine_url = "http://localhost:8080"
            mock_settings.return_value.redmine_api_key = "test_key"

            # When
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/tasks?status=open")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "tasks" in data["data"]
        assert "pagination" in data["data"]
        assert len(data["data"]["tasks"]) == 1
        assert data["data"]["tasks"][0]["title"] == "設計書レビュー"

    @pytest.mark.asyncio
    async def test_get_tasks_invalid_status_returns_422(self):
        """TC-030: status=invalid → 422 Unprocessable Entity
        Given: status に無効な値を指定
        When:  GET /api/v1/tasks にリクエストする
        Then:  422 でバリデーションエラーが返る
        """
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/tasks?status=invalid")

        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_get_tasks_redmine_error_returns_503(self):
        """TC-031: Redmine 接続エラー → 503 REDMINE_UNAVAILABLE
        Given: Redmine への接続に失敗する
        When:  GET /api/v1/tasks にリクエストする
        Then:  503 Service Unavailable が返る
        """
        from app.domain.exceptions import RedmineConnectionError

        with patch(
            "app.api.v1.tasks.RedmineAdapter"
        ) as MockAdapter, patch(
            "app.api.v1.tasks.get_settings"
        ) as mock_settings:
            mock_adapter_instance = MagicMock()
            mock_adapter_instance.list_issues = AsyncMock(
                side_effect=RedmineConnectionError("接続エラー")
            )
            MockAdapter.return_value = mock_adapter_instance
            mock_settings.return_value.redmine_url = "http://localhost:8080"
            mock_settings.return_value.redmine_api_key = "test_key"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/tasks")

        assert response.status_code == 503
        data = response.json()
        assert data["detail"]["error"]["code"] == "REDMINE_UNAVAILABLE"

    @pytest.mark.asyncio
    async def test_get_tasks_pagination(self):
        """TC-032: ページネーション → pagination フィールドが正しく返る
        Given: total_count=50, page=2, per_page=10
        When:  GET /api/v1/tasks?page=2&per_page=10 にリクエストする
        Then:  pagination.total_pages=5, pagination.page=2 が返る
        """
        with patch(
            "app.api.v1.tasks.RedmineAdapter"
        ) as MockAdapter, patch(
            "app.api.v1.tasks.get_settings"
        ) as mock_settings:
            mock_adapter_instance = MagicMock()
            mock_adapter_instance.list_issues = AsyncMock(
                return_value={
                    "issues": [SAMPLE_ISSUE],
                    "total_count": 50,
                    "offset": 10,
                    "limit": 10,
                }
            )
            MockAdapter.return_value = mock_adapter_instance
            mock_settings.return_value.redmine_url = "http://localhost:8080"
            mock_settings.return_value.redmine_api_key = "test_key"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/tasks?page=2&per_page=10")

        assert response.status_code == 200
        pagination = response.json()["data"]["pagination"]
        assert pagination["page"] == 2
        assert pagination["per_page"] == 10
        assert pagination["total_count"] == 50
        assert pagination["total_pages"] == 5

    @pytest.mark.asyncio
    async def test_get_tasks_empty_result(self):
        """TC-033: 0 件の場合 → 空の tasks リストで 200 OK
        Given: Redmine が 0 件を返す
        When:  GET /api/v1/tasks にリクエストする
        Then:  200 OK で空の tasks リストが返る
        """
        with patch(
            "app.api.v1.tasks.RedmineAdapter"
        ) as MockAdapter, patch(
            "app.api.v1.tasks.get_settings"
        ) as mock_settings:
            mock_adapter_instance = MagicMock()
            mock_adapter_instance.list_issues = AsyncMock(
                return_value={"issues": [], "total_count": 0, "offset": 0, "limit": 25}
            )
            MockAdapter.return_value = mock_adapter_instance
            mock_settings.return_value.redmine_url = "http://localhost:8080"
            mock_settings.return_value.redmine_api_key = "test_key"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/tasks")

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["tasks"] == []
        assert data["pagination"]["total_count"] == 0
