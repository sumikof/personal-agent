"""Task エンティティ。"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.exceptions import TaskValidationError
from app.domain.task.task_priority import TaskPriority
from app.domain.task.task_status import TaskStatus


@dataclass
class Task:
    """Redmine のチケット（Issue）を表すエンティティ。

    ドメインオブジェクトとして、タスクに関するビジネスルールを内包する。
    Redmine が正のデータストアであるため、本システムでは Redmine の
    データを写像・変換する役割を持つ。
    """

    redmine_issue_id: str
    title: str
    status: TaskStatus
    priority: TaskPriority
    project_id: int
    description: str | None = None
    due_date: date | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self) -> None:
        """インスタンス生成時にドメイン不変条件を検証する。"""
        self.validate()

    def validate(self) -> None:
        """ドメイン不変条件を検証する。

        Raises:
            TaskValidationError: 不変条件に違反する場合。
        """
        if not self.title or not self.title.strip():
            raise TaskValidationError(
                "タスクタイトルは必須です",
                field="title",
            )
        if len(self.title) > 200:
            raise TaskValidationError(
                f"タスクタイトルは200文字以内です（現在: {len(self.title)} 文字）",
                field="title",
            )
        if self.project_id < 1:
            raise TaskValidationError(
                f"プロジェクト ID は 1 以上の整数です: {self.project_id}",
                field="project_id",
            )
