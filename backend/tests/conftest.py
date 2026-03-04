"""テスト共通フィクスチャ。"""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.application.task.task_create_service import TaskCreateService
from app.infra.redmine.redmine_adapter import RedmineAdapter


@pytest.fixture
def mock_redmine_adapter() -> AsyncMock:
    """RedmineAdapter のモックフィクスチャ。"""
    mock = AsyncMock(spec=RedmineAdapter)
    return mock


@pytest.fixture
def task_create_service(mock_redmine_adapter: AsyncMock) -> TaskCreateService:
    """TaskCreateService のフィクスチャ。RedmineAdapter をモック化する。"""
    return TaskCreateService(redmine_adapter=mock_redmine_adapter)


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
    # TaskCreateService クラスのコンストラクタをモックに差し替える
    monkeypatch.setattr(
        "app.agent.tools.create_task_tool.TaskCreateService",
        lambda *args, **kwargs: mock,
    )
    # RedmineAdapter のコンストラクタもモック化（TaskCreateService への入力として渡されるため）
    monkeypatch.setattr(
        "app.agent.tools.create_task_tool.RedmineAdapter",
        lambda *args, **kwargs: AsyncMock(spec=RedmineAdapter),
    )
    return mock
