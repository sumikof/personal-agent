"""FEAT-004: タスクエンティティ・レポートエンティティ（entities.py）。

DSD-001_FEAT-004 セクション 4 に従い実装する。
TaskUpdate（FEAT-003）を参照しつつ、FEAT-004 向けに priority・due_date・start_date フィールドを持つ
Task エンティティと優先タスクレポート集約を提供する。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime

from app.domain.task.value_objects import TaskPriorityVO, TaskStatusVO


@dataclass
class Task:
    """Redmine Issue に対応するタスクエンティティ（FEAT-004）。

    TaskUpdate（FEAT-003）と異なり、start_date フィールドを追加している。
    FEAT-004 の優先度変更・期日変更・レポート生成で使用する。
    """

    redmine_issue_id: int
    title: str
    status: TaskStatusVO
    priority: TaskPriorityVO
    due_date: date | None
    start_date: date | None
    done_ratio: int
    updated_at: datetime

    @classmethod
    def from_redmine_response(cls, data: dict) -> "Task":
        """Redmine API レスポンスの Issue オブジェクトから Task を生成する。

        Args:
            data: Redmine API レスポンス辞書（"issue" キーを含む、またはissue辞書直接）。

        Returns:
            対応する Task エンティティ。

        Notes:
            - priority フィールドが存在しない場合は priority_id=2（通常）をデフォルトとして使用する。
            - due_date・start_date が null の場合は None を設定する。
        """
        issue = data.get("issue", data)

        # priority フィールドのデフォルト処理
        priority_data = issue.get("priority", {"id": 2, "name": "通常"})
        priority = TaskPriorityVO.from_id(priority_data.get("id", 2))

        # 日付フィールドの解析
        due_date_raw = issue.get("due_date")
        due_date = date.fromisoformat(due_date_raw) if due_date_raw else None

        start_date_raw = issue.get("start_date")
        start_date = date.fromisoformat(start_date_raw) if start_date_raw else None

        return cls(
            redmine_issue_id=issue["id"],
            title=issue["subject"],
            status=TaskStatusVO.from_id(issue["status"]["id"]),
            priority=priority,
            due_date=due_date,
            start_date=start_date,
            done_ratio=issue.get("done_ratio", 0),
            updated_at=datetime.fromisoformat(issue["updated_on"].replace("Z", "+00:00")),
        )


@dataclass
class TaskReportItem:
    """優先タスクレポートの個別項目（FEAT-004）。

    DSD-001_FEAT-004 セクション 4.1 に従う。
    """

    rank: int
    task: Task
    urgency_label: str
    days_until_due: int | None
    is_overdue: bool


@dataclass
class PriorityReport:
    """優先タスクレポートの集約（FEAT-004）。

    DSD-001_FEAT-004 セクション 4.1 に従う。
    未完了タスクを期日・優先度・緊急度で分類し、対応順序を提示する。
    """

    generated_at: date
    overdue_tasks: list[TaskReportItem]
    due_today_tasks: list[TaskReportItem]
    upcoming_tasks: list[TaskReportItem]
    no_due_date_tasks: list[TaskReportItem]
    total_open_count: int

    def to_markdown(self) -> str:
        """レポートを Markdown 形式の文字列に変換する。

        LangGraph エージェントの応答に組み込むための形式。

        Returns:
            Markdown 形式のレポート文字列。
        """
        lines = [
            f"## 優先タスクレポート（{self.generated_at.strftime('%Y年%m月%d日')}時点）",
            f"未完了タスク数: {self.total_open_count}件",
            "",
        ]

        if self.overdue_tasks:
            lines.append("### 🚨 期限超過（要対応）")
            for item in self.overdue_tasks:
                overdue_days = abs(item.days_until_due) if item.days_until_due is not None else "?"
                lines.append(
                    f"{item.rank}. **#{item.task.redmine_issue_id}** {item.task.title}"
                    f"（{overdue_days}日超過・優先度: {item.task.priority.name}）"
                )
            lines.append("")

        if self.due_today_tasks:
            lines.append("### ⚡ 今日期限")
            for item in self.due_today_tasks:
                lines.append(
                    f"{item.rank}. **#{item.task.redmine_issue_id}** {item.task.title}"
                    f"（優先度: {item.task.priority.name}）"
                )
            lines.append("")

        if self.upcoming_tasks:
            lines.append("### 📅 今週中")
            for item in self.upcoming_tasks:
                due_str = item.task.due_date.strftime("%m/%d") if item.task.due_date else ""
                lines.append(
                    f"{item.rank}. **#{item.task.redmine_issue_id}** {item.task.title}"
                    f"（期日: {due_str}・優先度: {item.task.priority.name}）"
                )
            lines.append("")

        if self.no_due_date_tasks:
            lines.append("### 📋 期日なし")
            for item in self.no_due_date_tasks:
                lines.append(
                    f"{item.rank}. **#{item.task.redmine_issue_id}** {item.task.title}"
                    f"（優先度: {item.task.priority.name}）"
                )

        return "\n".join(lines)
