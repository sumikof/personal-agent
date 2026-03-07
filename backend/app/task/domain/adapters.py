"""Redmine Issue → TaskSummary 変換アダプター（ACLパターン）。

CTX-001（タスク管理コンテキスト）の境界で、外部データモデル（Redmine Issue JSON）を
内部ドメインモデル（TaskSummary DTO）に変換する責務を担う。
"""
from __future__ import annotations

import os
from datetime import date
from typing import Optional

from app.task.domain.models import TaskSummary, TaskUrgency


class RedmineAdapter:
    """Redmine Issue JSON を内部ドメインモデル（TaskSummary）に変換するアダプター。

    BSD-009 の ACL（Anti-Corruption Layer）パターンに従い、
    Redmine の外部データ形式をドメインモデルに変換する。
    """

    # Redmine ステータス名（英語） → 日本語ラベルのマッピング
    STATUS_LABEL_MAP: dict[str, str] = {
        "New": "新規",
        "In Progress": "進行中",
        "Resolved": "解決済み",
        "Feedback": "フィードバック",
        "Closed": "完了",
        "Rejected": "却下",
    }

    # Redmine ステータス名 → 内部ステータスコード（snake_case）のマッピング
    STATUS_CODE_MAP: dict[str, str] = {
        "New": "new",
        "In Progress": "in_progress",
        "Resolved": "resolved",
        "Feedback": "feedback",
        "Closed": "closed",
        "Rejected": "rejected",
    }

    # Redmine 優先度名（英語） → 日本語ラベルのマッピング
    PRIORITY_LABEL_MAP: dict[str, str] = {
        "Low": "低",
        "Normal": "通常",
        "High": "高",
        "Urgent": "緊急",
        "Immediate": "即時",
    }

    def to_task_summary(self, issue: dict, today: date) -> TaskSummary:
        """Redmine Issue JSON を TaskSummary に変換する。

        Args:
            issue: Redmine API の issues[] の1要素。
            today: 今日の日付（期日チェック用）。

        Returns:
            TaskSummary DTO。
        """
        # ステータスの変換
        status_name: str = issue.get("status", {}).get("name", "New") or "New"
        status_code = self.STATUS_CODE_MAP.get(status_name, status_name.lower())
        status_label = self.STATUS_LABEL_MAP.get(status_name, status_name)

        # 優先度の変換
        priority_name: str = issue.get("priority", {}).get("name", "Normal") or "Normal"
        priority_code = priority_name.lower()
        priority_label = self.PRIORITY_LABEL_MAP.get(priority_name, priority_name)

        # 担当者名の取得
        assignee = issue.get("assigned_to")
        assignee_name: Optional[str] = assignee.get("name") if assignee else None

        # 期日の取得（"YYYY-MM-DD" 形式または None）
        due_date: Optional[str] = issue.get("due_date")

        # 緊急度の判定
        urgency = TaskUrgency.from_due_date(due_date, today)

        # Redmine URL の生成
        redmine_base_url = os.getenv("REDMINE_URL", "http://localhost:8080")
        redmine_url = f"{redmine_base_url}/issues/{issue['id']}"

        return TaskSummary(
            id=issue["id"],
            title=issue.get("subject", ""),
            status=status_code,
            status_label=status_label,
            priority=priority_code,
            priority_label=priority_label,
            assignee_name=assignee_name,
            due_date=due_date,
            urgency=urgency.value,
            redmine_url=redmine_url,
            created_at=issue.get("created_on", ""),
            updated_at=issue.get("updated_on", ""),
        )

    def to_task_summaries(
        self,
        issues: list[dict],
        today: Optional[date] = None,
    ) -> list[TaskSummary]:
        """複数の Redmine Issue JSON を TaskSummary リストに変換する。

        Args:
            issues: Redmine API の issues[] リスト。
            today: 今日の日付（省略時は date.today()）。

        Returns:
            TaskSummary のリスト。
        """
        if today is None:
            today = date.today()
        return [self.to_task_summary(issue, today) for issue in issues]
