"""タスクダッシュボード API レスポンススキーマ（FEAT-006）。

DSD-003_FEAT-006 のレスポンス仕様に基づく Pydantic モデル。
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class TaskSummarySchema(BaseModel):
    """タスクサマリーのレスポンススキーマ。"""

    id: int
    title: str
    status: str
    status_label: str
    priority: str
    priority_label: str
    assignee_name: Optional[str] = None
    due_date: Optional[str] = None
    urgency: str
    redmine_url: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class UrgencySummarySchema(BaseModel):
    """urgency 別件数サマリー。"""

    overdue: int = 0
    high: int = 0
    medium: int = 0
    normal: int = 0


class TaskListMetaSchema(BaseModel):
    """タスク一覧レスポンスのメタデータ。"""

    total: int
    urgency_summary: UrgencySummarySchema


class TaskListResponseSchema(BaseModel):
    """タスク一覧取得エンドポイントのレスポンス。"""

    data: list[TaskSummarySchema]
    meta: TaskListMetaSchema


class ErrorDetailSchema(BaseModel):
    """エラー詳細スキーマ。"""

    field: Optional[str] = None
    message: str


class ErrorSchema(BaseModel):
    """エラーレスポンス本体。"""

    code: str
    message: str
    details: list[ErrorDetailSchema] = []


class ErrorResponseSchema(BaseModel):
    """エラーレスポンスのラッパー。"""

    error: ErrorSchema
