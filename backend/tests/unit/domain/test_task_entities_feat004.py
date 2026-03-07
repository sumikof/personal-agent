"""FEAT-004: Task エンティティ（entities.py）の単体テスト（DSD-008 TC-E03〜E05）。

TDD Red フェーズ: テストを先に書き、実装が存在しない状態で失敗させる。
"""
from __future__ import annotations

from datetime import date

import pytest

from app.domain.task.entities import Task


# ---------------------------------------------------------------------------
# TC-E03: Task.from_redmine_response - priority・due_dateフィールドを含む（正常系）
# ---------------------------------------------------------------------------


class TestTaskFromRedmineResponseFeat004:
    """TC-E03: priority・due_dateフィールドを含むTaskの生成（正常系）。"""

    def test_from_redmine_response_with_priority_and_due_date(self) -> None:
        """priority（id=4, name="緊急"）とdue_date（"2026-03-10"）が設定されたRedmineレスポンスからTaskを生成する。

        Given: priority（id=4, name="緊急"）とdue_date（"2026-03-10"）が設定されたRedmineレスポンス
        When: Task.from_redmine_response(data) を呼び出す
        Then: Task.priority.id == 4、Task.due_date == date(2026, 3, 10) のTaskが生成される
        """
        # Given
        redmine_response = {
            "issue": {
                "id": 123,
                "subject": "設計書作成",
                "status": {"id": 2, "name": "進行中"},
                "priority": {"id": 4, "name": "緊急"},
                "due_date": "2026-03-10",
                "start_date": "2026-03-01",
                "done_ratio": 60,
                "updated_on": "2026-03-03T10:00:00Z",
            }
        }
        # When
        task = Task.from_redmine_response(redmine_response)
        # Then
        assert task.priority.id == 4
        assert task.priority.name == "緊急"
        assert task.due_date == date(2026, 3, 10)
        assert task.start_date == date(2026, 3, 1)

    # TC-E04: due_dateがnullのTaskの生成（正常系）
    def test_from_redmine_response_null_due_date(self) -> None:
        """due_dateがnull（期日未設定）のRedmineレスポンスからTaskを生成する。

        Given: due_dateがnull（期日未設定）のRedmineレスポンス
        When: Task.from_redmine_response(data) を呼び出す
        Then: Task.due_date is None である
        """
        redmine_response = {
            "issue": {
                "id": 456,
                "subject": "期日なしタスク",
                "status": {"id": 1, "name": "未着手"},
                "priority": {"id": 2, "name": "通常"},
                "due_date": None,
                "start_date": None,
                "done_ratio": 0,
                "updated_on": "2026-03-03T10:00:00Z",
            }
        }
        task = Task.from_redmine_response(redmine_response)
        assert task.due_date is None
        assert task.start_date is None

    # TC-E05: priorityフィールドが欠如している場合のデフォルト値（正常系）
    def test_from_redmine_response_missing_priority(self) -> None:
        """priorityフィールドが存在しないRedmineレスポンスからTaskを生成する。

        Given: priorityフィールドが存在しないRedmineレスポンス
        When: Task.from_redmine_response(data) を呼び出す
        Then: Task.priority.id == 2（通常）のデフォルト値が設定される
        """
        redmine_response = {
            "issue": {
                "id": 789,
                "subject": "優先度なしタスク",
                "status": {"id": 1, "name": "未着手"},
                # "priority" フィールドが存在しない
                "due_date": None,
                "done_ratio": 0,
                "updated_on": "2026-03-03T10:00:00Z",
            }
        }
        task = Task.from_redmine_response(redmine_response)
        assert task.priority.id == 2
        assert task.priority.name == "通常"
