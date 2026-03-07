"""FEAT-003: TaskUpdate エンティティの単体テスト（DSD-008 TC-E01〜E02）。

DSD-008 では Task.from_redmine_response と記載されているが、
FEAT-003 の実装は TaskUpdate.from_redmine_response に対応する。

TDD Green フェーズ: 実装済みの TaskUpdate エンティティに対してテストを実行する。
"""
from __future__ import annotations

import pytest

from app.domain.task.task_update import TaskUpdate


# ---------------------------------------------------------------------------
# TC-E01: TaskUpdate.from_redmine_response - 全フィールドが揃ったレスポンス（正常系）
# ---------------------------------------------------------------------------


class TestTaskUpdateFromRedmineResponse:
    """TC-E01: 正常なRedmineレスポンスからTaskUpdateを生成（正常系）。"""

    def test_from_redmine_response_full(self) -> None:
        """全フィールドが揃ったRedmine Issueレスポンスから正しいTaskUpdateを生成する。

        Given: 全フィールドが揃ったRedmine Issueレスポンス
        When: TaskUpdate.from_redmine_response(data) を呼び出す
        Then: 正しい属性を持つTaskUpdateオブジェクトが生成される
        """
        # Given
        redmine_response = {
            "issue": {
                "id": 123,
                "subject": "設計書作成",
                "status": {"id": 2, "name": "進行中"},
                "priority": {"id": 2, "name": "通常"},
                "assigned_to": {"id": 1, "name": "山田 太郎"},
                "due_date": "2026-03-31",
                "updated_on": "2026-03-03T10:00:00Z",
            }
        }
        # When
        task = TaskUpdate.from_redmine_response(redmine_response)
        # Then
        assert task.redmine_issue_id == 123
        assert task.title == "設計書作成"
        assert task.status.id == 2
        assert task.status.name == "進行中"
        assert task.assignee == "山田 太郎"
        assert str(task.due_date) == "2026-03-31"

    def test_from_redmine_response_priority(self) -> None:
        """優先度フィールドが正しく変換される。

        Given: priority.id=3（高）のRedmine Issueレスポンス
        When: TaskUpdate.from_redmine_response(data) を呼び出す
        Then: priority.id=3, priority.name="高" のTaskUpdateが生成される
        """
        redmine_response = {
            "issue": {
                "id": 100,
                "subject": "緊急タスク",
                "status": {"id": 1, "name": "未着手"},
                "priority": {"id": 3, "name": "高"},
                "assigned_to": {"id": 2, "name": "鈴木 花子"},
                "due_date": None,
                "updated_on": "2026-03-03T10:00:00Z",
            }
        }
        task = TaskUpdate.from_redmine_response(redmine_response)
        assert task.priority.id == 3
        assert task.priority.name == "高"


# ---------------------------------------------------------------------------
# TC-E02: TaskUpdate.from_redmine_response - オプションフィールドがnull（正常系）
# ---------------------------------------------------------------------------


class TestTaskUpdateFromRedmineResponseNullableFields:
    """TC-E02: オプションフィールドがnullのRedmineレスポンスからTaskUpdateを生成（正常系）。"""

    def test_from_redmine_response_nullable_fields(self) -> None:
        """assigned_to・due_dateがnullのレスポンスから正しいTaskUpdateを生成する。

        Given: assigned_to・due_dateがnullのRedmine Issueレスポンス
        When: TaskUpdate.from_redmine_response(data) を呼び出す
        Then: assigneeはNone、due_dateはNoneのTaskUpdateオブジェクトが生成される
        """
        # Given
        redmine_response = {
            "issue": {
                "id": 456,
                "subject": "タスクタイトル",
                "status": {"id": 1, "name": "未着手"},
                "priority": {"id": 2, "name": "通常"},
                "due_date": None,
                "updated_on": "2026-03-03T10:00:00Z",
            }
        }
        # When
        task = TaskUpdate.from_redmine_response(redmine_response)
        # Then
        assert task.assignee is None
        assert task.due_date is None

    def test_from_redmine_response_missing_assigned_to_key(self) -> None:
        """assigned_to キー自体が存在しない場合、assigneeがNoneになる。

        Given: assigned_toキーが存在しないRedmine Issueレスポンス
        When: TaskUpdate.from_redmine_response(data) を呼び出す
        Then: assigneeはNoneのTaskUpdateオブジェクトが生成される
        """
        redmine_response = {
            "issue": {
                "id": 789,
                "subject": "キー欠落テスト",
                "status": {"id": 2, "name": "進行中"},
                "priority": {"id": 1, "name": "低"},
                "due_date": None,
                "updated_on": "2026-03-03T10:00:00Z",
            }
        }
        task = TaskUpdate.from_redmine_response(redmine_response)
        assert task.assignee is None
        assert task.redmine_issue_id == 789

    def test_from_redmine_response_notes_is_none_by_default(self) -> None:
        """from_redmine_response で生成した TaskUpdate の notes は常に None。

        Given: 通常のRedmine Issueレスポンス
        When: TaskUpdate.from_redmine_response(data) を呼び出す
        Then: notes は None
        """
        redmine_response = {
            "issue": {
                "id": 1,
                "subject": "新規タスク",
                "status": {"id": 1, "name": "未着手"},
                "priority": {"id": 2, "name": "通常"},
                "due_date": None,
                "updated_on": "2026-03-03T10:00:00Z",
            }
        }
        task = TaskUpdate.from_redmine_response(redmine_response)
        assert task.notes is None
