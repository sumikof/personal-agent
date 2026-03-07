"""TaskUrgency.from_due_date の単体テスト（TDD: TC-BE-U001〜TC-BE-U009）。"""
from __future__ import annotations

from datetime import date

import pytest

from app.task.domain.models import TaskUrgency


class TestTaskUrgency:
    """TaskUrgency.from_due_date の境界値テスト。"""

    # TC-BE-U001: 期限超過（due_date < today）
    def test_overdue(self) -> None:
        today = date(2026, 3, 3)
        result = TaskUrgency.from_due_date("2026-03-01", today)
        assert result == TaskUrgency.OVERDUE
        assert result.value == "overdue"

    # TC-BE-U002: 当日（高緊急度）
    def test_high_same_day(self) -> None:
        today = date(2026, 3, 3)
        result = TaskUrgency.from_due_date("2026-03-03", today)
        assert result == TaskUrgency.HIGH

    # TC-BE-U003: 1日後（高緊急度）
    def test_high_1day_later(self) -> None:
        today = date(2026, 3, 3)
        result = TaskUrgency.from_due_date("2026-03-04", today)
        assert result == TaskUrgency.HIGH

    # TC-BE-U004: 3日後（高緊急度の境界値）
    def test_high_urgency_boundary_3days(self) -> None:
        today = date(2026, 3, 3)
        result = TaskUrgency.from_due_date("2026-03-06", today)
        assert result == TaskUrgency.HIGH

    # TC-BE-U005: 4日後（中緊急度の境界値）
    def test_medium_urgency_boundary_4days(self) -> None:
        today = date(2026, 3, 3)
        result = TaskUrgency.from_due_date("2026-03-07", today)
        assert result == TaskUrgency.MEDIUM

    # TC-BE-U006: 7日後（中緊急度の上限境界値）
    def test_medium_urgency_boundary_7days(self) -> None:
        today = date(2026, 3, 3)
        result = TaskUrgency.from_due_date("2026-03-10", today)
        assert result == TaskUrgency.MEDIUM

    # TC-BE-U007: 8日後（通常緊急度の境界値）
    def test_normal_urgency_boundary_8days(self) -> None:
        today = date(2026, 3, 3)
        result = TaskUrgency.from_due_date("2026-03-11", today)
        assert result == TaskUrgency.NORMAL

    # TC-BE-U008: 期日なし（通常緊急度）
    def test_no_due_date_returns_normal(self) -> None:
        today = date(2026, 3, 3)
        result = TaskUrgency.from_due_date(None, today)
        assert result == TaskUrgency.NORMAL

    # TC-BE-U009: 不正な日付フォーマット（異常系）
    def test_invalid_date_format_returns_normal(self) -> None:
        today = date(2026, 3, 3)
        result = TaskUrgency.from_due_date("2026/03/01", today)
        assert result == TaskUrgency.NORMAL
