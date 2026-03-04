"""タスク検索 REST API エンドポイント（FEAT-002）。"""
from __future__ import annotations

import logging
import math
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.application.task.task_search_service import TaskSearchService
from app.config import get_settings
from app.domain.exceptions import RedmineAuthError, RedmineConnectionError
from app.infra.redmine.redmine_adapter import RedmineAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["tasks"])


class TaskResponse(BaseModel):
    """タスク情報レスポンスモデル。"""

    id: str
    title: str
    description: str | None
    status: str
    priority: str
    due_date: str | None
    project_id: int | None
    project_name: str
    url: str
    created_at: str | None
    updated_at: str | None


class PaginationResponse(BaseModel):
    """ページネーション情報レスポンスモデル。"""

    total_count: int
    page: int
    per_page: int
    total_pages: int


class TaskListData(BaseModel):
    """タスク一覧レスポンスのデータ部。"""

    tasks: list[TaskResponse]
    pagination: PaginationResponse


class TaskListResponse(BaseModel):
    """GET /api/v1/tasks のレスポンス。"""

    data: TaskListData


STATUS_MAP = {"open": "open", "closed": "closed", "all": "*"}


@router.get("/tasks", response_model=TaskListResponse)
async def get_tasks(
    status: Annotated[str, Query(pattern=r"^(open|closed|all)$")] = "open",
    due_date: Annotated[
        str | None,
        Query(pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD 形式"),
    ] = None,
    keyword: Annotated[
        str | None,
        Query(min_length=1, max_length=100, description="タイトル部分一致検索"),
    ] = None,
    project_id: Annotated[
        int | None, Query(ge=1, description="Redmine プロジェクト ID")
    ] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 25,
) -> TaskListResponse:
    """Redmine タスク一覧を取得する REST API。

    チャット（エージェント）を経由せず、直接タスクを取得する。
    """
    settings = get_settings()
    adapter = RedmineAdapter(
        base_url=settings.redmine_url,
        api_key=settings.redmine_api_key,
    )
    service = TaskSearchService(redmine_adapter=adapter)

    logger.info(
        "api_get_tasks_called status=%s due_date=%s keyword=%s project_id=%s page=%d per_page=%d",
        status,
        due_date,
        keyword[:30] if keyword else None,
        project_id,
        page,
        per_page,
    )

    try:
        offset = (page - 1) * per_page
        status_id = STATUS_MAP.get(status, "open")

        response = await adapter.list_issues(
            status_id=status_id,
            limit=per_page,
            offset=offset,
            due_date=due_date,
            subject_like=keyword,
            project_id=project_id,
        )

        raw_issues = response.get("issues", [])
        total_count = response.get("total_count", len(raw_issues))
        tasks = [service._format_task(issue) for issue in raw_issues]
        total_pages = max(1, math.ceil(total_count / per_page))

        logger.info(
            "api_get_tasks_succeeded result_count=%d total_count=%d",
            len(tasks),
            total_count,
        )

        return TaskListResponse(
            data=TaskListData(
                tasks=[TaskResponse(**task) for task in tasks],
                pagination=PaginationResponse(
                    total_count=total_count,
                    page=page,
                    per_page=per_page,
                    total_pages=total_pages,
                ),
            )
        )

    except RedmineConnectionError as e:
        logger.error("api_get_tasks_redmine_connection_error error=%s", str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "REDMINE_UNAVAILABLE",
                    "message": "Redmine サーバーへの接続に失敗しました。",
                    "details": [],
                }
            },
        ) from e

    except RedmineAuthError as e:
        logger.error("api_get_tasks_redmine_auth_error error=%s", str(e))
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "code": "REDMINE_AUTH_ERROR",
                    "message": "Redmine API キーの設定を確認してください。",
                    "details": [],
                }
            },
        ) from e

    except Exception as e:
        logger.error("api_get_tasks_unexpected_error error=%s", str(e))
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "サーバー内部エラーが発生しました。",
                    "details": [],
                }
            },
        ) from e
