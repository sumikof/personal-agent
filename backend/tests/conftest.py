"""テスト共通フィクスチャ。"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.task.task_create_service import TaskCreateService
from app.infra.redmine.redmine_adapter import RedmineAdapter


@pytest.fixture
def mock_redmine_adapter() -> MagicMock:
    """RedmineAdapter の Mock オブジェクト。

    list_issues・create_issue メソッドを AsyncMock として提供する。
    """
    adapter = MagicMock()
    adapter.list_issues = AsyncMock()
    adapter.create_issue = AsyncMock()
    return adapter


@pytest.fixture
def task_create_service(mock_redmine_adapter: MagicMock) -> TaskCreateService:
    """TaskCreateService のフィクスチャ。RedmineAdapter をモック化する。"""
    return TaskCreateService(redmine_adapter=mock_redmine_adapter)


@pytest.fixture
def task_search_service(mock_redmine_adapter: MagicMock):
    """TaskSearchService インスタンス（Redmine Adapter をモック化）。"""
    from app.application.task.task_search_service import TaskSearchService
    return TaskSearchService(redmine_adapter=mock_redmine_adapter)


@pytest.fixture
def redmine_adapter() -> RedmineAdapter:
    """テスト用 RedmineAdapter（httpx-mock と組み合わせて使用）。"""
    return RedmineAdapter(
        base_url="http://localhost:8080",
        api_key="test-api-key",
    )


@pytest.fixture
def mock_task_create_service(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """TaskCreateService のモックフィクスチャ（create_task_tool テスト用）。

    create_task_tool モジュール内の TaskCreateService のインスタンス化をモック化する。
    """
    mock = AsyncMock(spec=TaskCreateService)
    monkeypatch.setattr(
        "app.agent.tools.create_task_tool.TaskCreateService",
        lambda *args, **kwargs: mock,
    )
    monkeypatch.setattr(
        "app.agent.tools.create_task_tool.RedmineAdapter",
        lambda *args, **kwargs: AsyncMock(spec=RedmineAdapter),
    )
    return mock


@pytest.fixture
def sample_redmine_issue() -> dict:
    """Redmine GET /issues.json レスポンスのサンプルチケット 1 件。"""
    return {
        "id": 123,
        "project": {"id": 1, "name": "パーソナルエージェント開発"},
        "tracker": {"id": 1, "name": "バグ"},
        "status": {"id": 1, "name": "新規"},
        "priority": {"id": 3, "name": "高"},
        "author": {"id": 1, "name": "Redmine Admin"},
        "assigned_to": None,
        "subject": "設計書レビュー",
        "description": "DSD-001〜DSD-008 のレビューを実施する",
        "start_date": "2026-03-01",
        "due_date": "2026-03-03",
        "done_ratio": 0,
        "is_private": False,
        "estimated_hours": None,
        "created_on": "2026-02-20T09:00:00Z",
        "updated_on": "2026-03-01T14:30:00Z",
        "closed_on": None,
    }


@pytest.fixture
def sample_redmine_issues_response(sample_redmine_issue: dict) -> dict:
    """Redmine GET /issues.json の成功レスポンス（3 件）。"""
    issue2 = {**sample_redmine_issue, "id": 124, "subject": "API テスト実施",
               "priority": {"id": 2, "name": "通常"}, "assigned_to": None, "description": None}
    issue3 = {**sample_redmine_issue, "id": 125, "subject": "ドキュメント更新",
               "priority": {"id": 1, "name": "低"}, "description": ""}
    return {
        "issues": [sample_redmine_issue, issue2, issue3],
        "total_count": 3,
        "offset": 0,
        "limit": 25,
    }


@pytest.fixture
def empty_redmine_response() -> dict:
    """Redmine GET /issues.json の 0 件レスポンス。"""
    return {
        "issues": [],
        "total_count": 0,
        "offset": 0,
        "limit": 25,
    }
