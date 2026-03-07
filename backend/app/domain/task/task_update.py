"""FEAT-003 用タスクエンティティ（タスク更新専用）。

DSD-001_FEAT-003 の 4.1 に従い実装する。
既存の Task エンティティ (task.py) は FEAT-001/002 互換のため残置し、
本モジュールは FEAT-003（タスク更新・進捗報告）専用のドメインオブジェクトを提供する。
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.domain.task.value_objects import TaskPriorityVO, TaskStatusVO


@dataclass
class TaskUpdate:
    """Redmine Issue に対応するタスクエンティティ（FEAT-003）。

    タスク更新操作の主体となるエンティティ。
    Redmine API レスポンスからの写像・変換役を持つ。
    """

    redmine_issue_id: int
    title: str
    status: TaskStatusVO
    priority: TaskPriorityVO
    assignee: str | None
    due_date: date | None
    notes: str | None
    updated_at: datetime

    @classmethod
    def from_redmine_response(cls, data: dict) -> "TaskUpdate":
        """Redmine API レスポンスの Issue オブジェクトから TaskUpdate を生成する。

        Args:
            data: Redmine API レスポンス辞書（"issue" キーを含む、またはissue辞書直接）。

        Returns:
            対応する TaskUpdate エンティティ。
        """
        issue = data.get("issue", data)
        return cls(
            redmine_issue_id=issue["id"],
            title=issue["subject"],
            status=TaskStatusVO.from_id(issue["status"]["id"]),
            priority=TaskPriorityVO.from_id(issue["priority"]["id"]),
            assignee=issue.get("assigned_to", {}).get("name") if issue.get("assigned_to") else None,
            due_date=date.fromisoformat(issue["due_date"]) if issue.get("due_date") else None,
            notes=None,
            updated_at=datetime.fromisoformat(issue["updated_on"].replace("Z", "+00:00")),
        )
