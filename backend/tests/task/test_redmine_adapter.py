"""RedmineAdapter の単体テスト（TDD: TC-BE-A001〜TC-BE-A005）。"""
from __future__ import annotations

from datetime import date

import pytest

from app.task.domain.models import TaskSummary


class TestRedmineAdapter:
    """RedmineAdapter.to_task_summary / to_task_summaries のテスト。"""

    def setup_method(self) -> None:
        from app.task.domain.adapters import RedmineAdapter

        self.adapter = RedmineAdapter()
        self.today = date(2026, 3, 3)

    # TC-BE-A001: 完全なIssueデータの変換（正常系）
    def test_to_task_summary_full_issue(self) -> None:
        # Given
        issue = {
            "id": 123,
            "subject": "API基本設計書の作成",
            "status": {"id": 2, "name": "In Progress"},
            "priority": {"id": 3, "name": "High"},
            "assigned_to": {"id": 1, "name": "山田 太郎"},
            "due_date": "2026-03-06",
            "created_on": "2026-03-01T09:00:00Z",
            "updated_on": "2026-03-03T10:00:00Z",
        }

        # When
        result = self.adapter.to_task_summary(issue, self.today)

        # Then
        assert isinstance(result, TaskSummary)
        assert result.id == 123
        assert result.title == "API基本設計書の作成"
        assert result.status == "in_progress"
        assert result.status_label == "進行中"
        assert result.priority == "high"
        assert result.priority_label == "高"
        assert result.assignee_name == "山田 太郎"
        assert result.due_date == "2026-03-06"
        assert result.urgency == "high"  # today=3/3, due_date=3/6 → days_diff=3 → high
        assert "localhost:8080/issues/123" in result.redmine_url

    # TC-BE-A002: 担当者なしのIssue変換（正常系）
    def test_to_task_summary_no_assignee(self) -> None:
        # Given
        issue = {
            "id": 124,
            "subject": "担当者なしタスク",
            "status": {"id": 1, "name": "New"},
            "priority": {"id": 2, "name": "Normal"},
            "assigned_to": None,  # 担当者なし
            "due_date": None,
            "created_on": "2026-03-02T14:00:00Z",
            "updated_on": "2026-03-03T09:00:00Z",
        }

        # When
        result = self.adapter.to_task_summary(issue, self.today)

        # Then
        assert result.assignee_name is None

    # TC-BE-A003: 期日なしのIssue変換（正常系）
    def test_to_task_summary_no_due_date(self) -> None:
        # Given
        issue = {
            "id": 125,
            "subject": "期日なしタスク",
            "status": {"id": 2, "name": "In Progress"},
            "priority": {"id": 2, "name": "Normal"},
            "assigned_to": None,
            "due_date": None,
            "created_on": "2026-03-01T09:00:00Z",
            "updated_on": "2026-03-03T09:00:00Z",
        }

        # When
        result = self.adapter.to_task_summary(issue, self.today)

        # Then
        assert result.due_date is None
        assert result.urgency == "normal"

    # TC-BE-A004: 未知のステータス名の変換（正常系）
    def test_to_task_summary_unknown_status(self) -> None:
        # Given
        issue = {
            "id": 126,
            "subject": "テスト中タスク",
            "status": {"id": 99, "name": "Testing"},  # マッピング外のステータス
            "priority": {"id": 2, "name": "Normal"},
            "assigned_to": None,
            "due_date": None,
            "created_on": "2026-03-01T09:00:00Z",
            "updated_on": "2026-03-03T09:00:00Z",
        }

        # When
        result = self.adapter.to_task_summary(issue, self.today)

        # Then
        assert result.status == "testing"   # 小文字変換
        assert result.status_label == "Testing"  # 英語のまま

    # TC-BE-A005: 複数Issue一括変換（正常系）
    def test_to_task_summaries_multiple(self) -> None:
        # Given: 3件のIssue
        issues = [
            {
                "id": i,
                "subject": f"タスク{i}",
                "status": {"id": 1, "name": "New"},
                "priority": {"id": 2, "name": "Normal"},
                "assigned_to": None,
                "due_date": None,
                "created_on": "2026-03-01T09:00:00Z",
                "updated_on": "2026-03-01T09:00:00Z",
            }
            for i in range(1, 4)
        ]

        # When
        results = self.adapter.to_task_summaries(issues, self.today)

        # Then
        assert len(results) == 3
        assert results[0].id == 1
        assert results[1].id == 2
        assert results[2].id == 3
