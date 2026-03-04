"""タスクダッシュボード API ルーター（FEAT-006）。

DSD-003_FEAT-006 の仕様に基づく FastAPI ルーター。
GET /api/v1/tasks エンドポイントを提供する。
"""
from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.domain.exceptions import RedmineConnectionError
from app.task.schemas import (
    ErrorResponseSchema,
    ErrorSchema,
    TaskListMetaSchema,
    TaskListResponseSchema,
    TaskSummarySchema,
    UrgencySummarySchema,
)

logger = logging.getLogger(__name__)

# status パラメータの許容値
VALID_STATUS_VALUES = {
    "new",
    "in_progress",
    "feedback",
    "resolved",
    "closed",
    "rejected",
    "all",
}

# urgency パラメータの許容値
VALID_URGENCY_VALUES = {"overdue", "high", "medium", "normal"}


def create_task_router(dashboard_service: object) -> APIRouter:
    """TaskDashboardService を注入した APIRouter を生成して返す。

    Args:
        dashboard_service: TaskDashboardService インスタンス（テスト時はモック注入可能）。

    Returns:
        FastAPI の APIRouter。
    """
    router = APIRouter(tags=["tasks"])

    @router.get(
        "/tasks",
        response_model=TaskListResponseSchema,
        summary="タスク一覧取得",
        description="Redmine から全タスクを取得し、urgency・status_label を付加して返す。",
    )
    async def get_tasks(
        status: Optional[str] = Query(
            default=None,
            description="ステータスフィルタ（new/in_progress/feedback/resolved/closed/rejected/all）",
        ),
        urgency: Optional[str] = Query(
            default=None,
            description="緊急度フィルタ（overdue/high/medium/normal）",
        ),
    ) -> JSONResponse:
        """タスク一覧を取得して返す。"""
        # バリデーション
        if status is not None and status not in VALID_STATUS_VALUES:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "入力値が不正です",
                        "details": [
                            {
                                "field": "status",
                                "message": (
                                    "statusは new, in_progress, feedback, "
                                    "resolved, closed, rejected, all のいずれかを指定してください"
                                ),
                            }
                        ],
                    }
                },
            )

        if urgency is not None and urgency not in VALID_URGENCY_VALUES:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "入力値が不正です",
                        "details": [
                            {
                                "field": "urgency",
                                "message": (
                                    "urgencyは overdue, high, medium, normal のいずれかを指定してください"
                                ),
                            }
                        ],
                    }
                },
            )

        # status="all" は全件取得なのでフィルタなしとして扱う
        status_filter = None if status == "all" else status

        try:
            tasks = await dashboard_service.get_tasks(
                status_filter=status_filter,
                urgency_filter=urgency,
            )
        except RedmineConnectionError as e:
            logger.error("get_tasks failed: %s", str(e))
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "Redmineへの接続に失敗しました。しばらく後に再試行してください。",
                        "details": [],
                    }
                },
            )
        except Exception as e:
            logger.error("get_tasks unexpected error: %s", str(e))
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_ERROR",
                        "message": "サーバー内部エラーが発生しました。",
                        "details": [],
                    }
                },
            )

        # urgency_summary の集計
        urgency_summary = UrgencySummarySchema(
            overdue=sum(1 for t in tasks if t.urgency == "overdue"),
            high=sum(1 for t in tasks if t.urgency == "high"),
            medium=sum(1 for t in tasks if t.urgency == "medium"),
            normal=sum(1 for t in tasks if t.urgency == "normal"),
        )

        response_data = TaskListResponseSchema(
            data=[TaskSummarySchema.model_validate(t) for t in tasks],
            meta=TaskListMetaSchema(
                total=len(tasks),
                urgency_summary=urgency_summary,
            ),
        )

        return JSONResponse(
            status_code=200,
            content=response_data.model_dump(),
        )

    return router
