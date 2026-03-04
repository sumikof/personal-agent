"""FEAT-004: TaskPriority・DueDate 値オブジェクトの単体テスト。

TDD Red フェーズ: テストを先に書き、実装が存在しない状態で失敗させる。
"""
from __future__ import annotations

from datetime import date

import pytest

from app.domain.task.value_objects import DueDate, TaskPriority


# ---------------------------------------------------------------------------
# 4.1 TaskPriority 値オブジェクトのテスト
# ---------------------------------------------------------------------------


class TestTaskPriorityFromId:
    """TC-P01: TaskPriority.from_id - 有効な優先度ID（正常系）。"""

    @pytest.mark.parametrize(
        "priority_id, expected_name",
        [
            (1, "低"),
            (2, "通常"),
            (3, "高"),
            (4, "緊急"),
            (5, "即座に"),
        ],
    )
    def test_from_id_valid(self, priority_id: int, expected_name: str) -> None:
        """有効な優先度ID（1〜5）から正しいTaskPriorityオブジェクトを生成する。

        Given: 有効な優先度ID（1〜5のいずれか）
        When: TaskPriority.from_id(priority_id) を呼び出す
        Then: 正しい名称のTaskPriorityオブジェクトが返される
        """
        priority = TaskPriority.from_id(priority_id)
        assert priority.id == priority_id
        assert priority.name == expected_name

    @pytest.mark.parametrize("invalid_id", [0, 6, 10, -1, 100])
    def test_from_id_invalid_raises_value_error(self, invalid_id: int) -> None:
        """TC-P02: 無効な優先度ID（{1,2,3,4,5}以外）でValueErrorが発生する。

        Given: 無効な優先度ID（{1,2,3,4,5}以外）
        When: TaskPriority.from_id(invalid_id) を呼び出す
        Then: ValueError が発生する
              エラーメッセージに「無効な優先度ID」が含まれる
        """
        with pytest.raises(ValueError, match="無効な優先度ID"):
            TaskPriority.from_id(invalid_id)

    @pytest.mark.parametrize(
        "priority_id, expected",
        [
            (1, True),
            (2, True),
            (3, True),
            (4, True),
            (5, True),
            (0, False),
            (6, False),
            (-1, False),
            (100, False),
        ],
    )
    def test_validate_id(self, priority_id: int, expected: bool) -> None:
        """TC-P03: TaskPriority.validate_id - 有効・無効の判定。

        Given: 優先度ID
        When: TaskPriority.validate_id(priority_id) を呼び出す
        Then: 有効なIDはTrue、無効なIDはFalseが返される
        """
        assert TaskPriority.validate_id(priority_id) == expected


# ---------------------------------------------------------------------------
# 4.2 DueDate 値オブジェクトのテスト
# ---------------------------------------------------------------------------


class TestDueDateIsPast:
    """TC-DD01: DueDate.is_past - 過去日付の判定（正常系）。"""

    @pytest.mark.parametrize(
        "due_date_value, reference_date, expected",
        [
            (date(2026, 3, 1), date(2026, 3, 3), True),   # 2日前 → 過去
            (date(2026, 3, 3), date(2026, 3, 3), False),  # 当日 → 過去ではない
            (date(2026, 3, 10), date(2026, 3, 3), False), # 未来 → 過去ではない
        ],
    )
    def test_is_past(
        self, due_date_value: date, reference_date: date, expected: bool
    ) -> None:
        """参照日より前の場合はTrue、そうでない場合はFalseが返される。

        Given: DueDateオブジェクトと参照日
        When: due_date.is_past(reference_date) を呼び出す
        Then: 参照日より前の場合はTrue、そうでない場合はFalseが返される
        """
        due_date = DueDate(value=due_date_value)
        assert due_date.is_past(reference_date) == expected


class TestDueDateDaysUntil:
    """TC-DD02: DueDate.days_until - 期日までの日数計算。"""

    @pytest.mark.parametrize(
        "due_date_value, reference_date, expected_days",
        [
            (date(2026, 3, 10), date(2026, 3, 3), 7),   # 7日後
            (date(2026, 3, 3), date(2026, 3, 3), 0),    # 当日
            (date(2026, 3, 1), date(2026, 3, 3), -2),   # 2日超過（負数）
        ],
    )
    def test_days_until(
        self, due_date_value: date, reference_date: date, expected_days: int
    ) -> None:
        """参照日から期日までの日数が返される（負数は超過を表す）。

        Given: DueDateオブジェクトと参照日
        When: due_date.days_until(reference_date) を呼び出す
        Then: 参照日から期日までの日数が返される（負数は超過を表す）
        """
        due_date = DueDate(value=due_date_value)
        assert due_date.days_until(reference_date) == expected_days


class TestDueDateIsWithinWeek:
    """TC-DD03: DueDate.is_within_week - 今週以内の判定。"""

    @pytest.mark.parametrize(
        "due_date_value, reference_date, expected",
        [
            (date(2026, 3, 10), date(2026, 3, 3), True),  # 7日後 → 今週以内
            (date(2026, 3, 9), date(2026, 3, 3), True),   # 6日後 → 今週以内
            (date(2026, 3, 11), date(2026, 3, 3), False), # 8日後 → 今週超過
            (date(2026, 3, 3), date(2026, 3, 3), True),   # 当日 → 今週以内
            (date(2026, 3, 2), date(2026, 3, 3), False),  # 昨日（過去） → 今週以内ではない
        ],
    )
    def test_is_within_week(
        self, due_date_value: date, reference_date: date, expected: bool
    ) -> None:
        """参照日から7日以内（0〜7日）の場合はTrue、それ以外はFalseが返される。

        Given: DueDateオブジェクトと参照日
        When: due_date.is_within_week(reference_date) を呼び出す
        Then: 参照日から7日以内（0〜7日）の場合はTrue、それ以外はFalseが返される
        """
        due_date = DueDate(value=due_date_value)
        assert due_date.is_within_week(reference_date) == expected


class TestDueDateInvalidType:
    """TC-DD04: DueDate - 不正な型（異常系）。"""

    def test_invalid_type_raises_type_error(self) -> None:
        """date型以外の値（文字列）でTypeErrorが発生する。

        Given: date型以外の値（文字列）
        When: DueDate(value="2026-03-10") を呼び出す
        Then: TypeError が発生する
        """
        with pytest.raises(TypeError, match="date型"):
            DueDate(value="2026-03-10")  # type: ignore[arg-type]
