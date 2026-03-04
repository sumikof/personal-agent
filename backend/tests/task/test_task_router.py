"""TaskRouter の単体テスト（TDD: TC-BE-R001〜TC-BE-R004）。"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.domain.exceptions import RedmineConnectionError
from app.task.domain.models import TaskSummary


def make_task_summary(
    id: int = 1,
    title: str = "テストタスク",
    status: str = "in_progress",
    status_label: str = "進行中",
    priority: str = "normal",
    priority_label: str = "通常",
    urgency: str = "normal",
    due_date: str | None = None,
    assignee_name: str | None = None,
) -> TaskSummary:
    """テスト用 TaskSummary を生成するヘルパー。"""
    return TaskSummary(
        id=id,
        title=title,
        status=status,
        status_label=status_label,
        priority=priority,
        priority_label=priority_label,
        assignee_name=assignee_name,
        due_date=due_date,
        urgency=urgency,
        redmine_url=f"http://localhost:8080/issues/{id}",
        created_at="2026-03-01T09:00:00Z",
        updated_at="2026-03-03T09:00:00Z",
    )


@pytest.fixture
def mock_dashboard_service() -> MagicMock:
    """TaskDashboardService のモック。"""
    service = MagicMock()
    service.get_tasks = AsyncMock(return_value=[
        make_task_summary(1, "タスク1", urgency="overdue"),
        make_task_summary(2, "タスク2", urgency="high"),
        make_task_summary(3, "タスク3", urgency="normal"),
    ])
    return service


@pytest.fixture
def test_client(mock_dashboard_service: MagicMock) -> TestClient:
    """テスト用 FastAPI クライアント。"""
    from fastapi import FastAPI
    from app.task.router import create_task_router

    app = FastAPI()
    router = create_task_router(dashboard_service=mock_dashboard_service)
    app.include_router(router, prefix="/api/v1")

    return TestClient(app)


class TestTaskRouter:
    """TaskRouter のテストクラス。"""

    # TC-BE-R001: GET /api/v1/tasks — 全件取得（正常系）
    def test_get_tasks_returns_200(self, test_client: TestClient) -> None:
        # When
        response = test_client.get("/api/v1/tasks")

        # Then
        assert response.status_code == 200
        body = response.json()
        assert "data" in body
        assert "meta" in body
        assert len(body["data"]) == 3
        assert body["meta"]["total"] == 3

    # TC-BE-R002: レスポンス構造の検証
    def test_get_tasks_response_structure(self, test_client: TestClient) -> None:
        # When
        response = test_client.get("/api/v1/tasks")
        body = response.json()

        # Then: data 配列の1件目が TaskSummary のフィールドを持つ
        task = body["data"][0]
        assert "id" in task
        assert "title" in task
        assert "status" in task
        assert "status_label" in task
        assert "priority" in task
        assert "priority_label" in task
        assert "urgency" in task
        assert "redmine_url" in task
        assert "created_at" in task
        assert "updated_at" in task

    # TC-BE-R003: urgency_summary の集計確認
    def test_get_tasks_urgency_summary(self, test_client: TestClient) -> None:
        # When
        response = test_client.get("/api/v1/tasks")
        body = response.json()

        # Then: urgency_summary が正しく集計されている
        summary = body["meta"]["urgency_summary"]
        assert summary["overdue"] == 1
        assert summary["high"] == 1
        assert summary["medium"] == 0
        assert summary["normal"] == 1

    # TC-BE-R004: Redmine 接続失敗時に 503 を返す
    def test_get_tasks_returns_503_on_connection_error(
        self,
        mock_dashboard_service: MagicMock,
    ) -> None:
        from fastapi import FastAPI
        from app.task.router import create_task_router

        # Given: Redmine 接続失敗をシミュレート
        mock_dashboard_service.get_tasks = AsyncMock(
            side_effect=RedmineConnectionError("接続失敗")
        )
        app = FastAPI()
        router = create_task_router(dashboard_service=mock_dashboard_service)
        app.include_router(router, prefix="/api/v1")
        client = TestClient(app, raise_server_exceptions=False)

        # When
        response = client.get("/api/v1/tasks")

        # Then
        assert response.status_code == 503
        body = response.json()
        assert body["error"]["code"] == "SERVICE_UNAVAILABLE"

    # TC-BE-R005: status フィルタパラメータの転送
    def test_get_tasks_passes_status_filter(
        self,
        test_client: TestClient,
        mock_dashboard_service: MagicMock,
    ) -> None:
        # When
        test_client.get("/api/v1/tasks?status=in_progress")

        # Then: サービスに status_filter="in_progress" が渡される
        mock_dashboard_service.get_tasks.assert_called_once_with(
            status_filter="in_progress",
            urgency_filter=None,
        )

    # TC-BE-R006: urgency フィルタパラメータの転送
    def test_get_tasks_passes_urgency_filter(
        self,
        test_client: TestClient,
        mock_dashboard_service: MagicMock,
    ) -> None:
        # When
        test_client.get("/api/v1/tasks?urgency=overdue")

        # Then: サービスに urgency_filter="overdue" が渡される
        mock_dashboard_service.get_tasks.assert_called_once_with(
            status_filter=None,
            urgency_filter="overdue",
        )
