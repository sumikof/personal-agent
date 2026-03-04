"""FEAT-004: DateParser（自然言語日付解析）の単体テスト。

TDD Red フェーズ: テストを先に書き、実装が存在しない状態で失敗させる。
"""
from __future__ import annotations

from datetime import date

import pytest

from app.domain.utils.date_parser import DateParser


# ---------------------------------------------------------------------------
# 4.3 DateParser のテスト
# ---------------------------------------------------------------------------


class TestDateParserRelativeDays:
    """TC-DP01: 相対日付の解析 - 「明日」「N日後」「N週間後」（正常系）。"""

    @pytest.mark.parametrize(
        "text, base_date, expected",
        [
            ("明日", date(2026, 3, 3), date(2026, 3, 4)),
            ("3日後", date(2026, 3, 3), date(2026, 3, 6)),
            ("1週間後", date(2026, 3, 3), date(2026, 3, 10)),
            ("2週間後", date(2026, 3, 3), date(2026, 3, 17)),
        ],
    )
    def test_relative_days(self, text: str, base_date: date, expected: date) -> None:
        """相対日付表現（「明日」「N日後」）から正しいdateオブジェクトが返される。

        Given: 相対日付表現（「明日」「N日後」）と基準日
        When: DateParser(base_date).parse(text) を呼び出す
        Then: 正しいdateオブジェクトが返される
        """
        parser = DateParser(base_date=base_date)
        result = parser.parse(text)
        assert result == expected


class TestDateParserWeekday:
    """TC-DP02: 曜日指定の解析 - 「今週○曜日」「来週○曜日」（正常系）。"""

    # 2026-03-03 は火曜日
    @pytest.mark.parametrize(
        "text, base_date, expected",
        [
            ("来週金曜", date(2026, 3, 3), date(2026, 3, 13)),    # 翌週金曜
            ("来週月曜", date(2026, 3, 3), date(2026, 3, 9)),     # 翌週月曜
            ("今週金曜", date(2026, 3, 3), date(2026, 3, 6)),     # 今週金曜
            ("今週火曜日", date(2026, 3, 3), date(2026, 3, 3)),   # 今日が火曜日 → 今日
        ],
    )
    def test_weekday(self, text: str, base_date: date, expected: date) -> None:
        """曜日指定の日付表現から正しいdateオブジェクトが返される。

        Given: 曜日指定の日付表現（「来週金曜」等）と基準日
        When: DateParser(base_date).parse(text) を呼び出す
        Then: 次に来る指定曜日のdateオブジェクトが返される
        """
        parser = DateParser(base_date=base_date)
        result = parser.parse(text)
        assert result == expected


class TestDateParserIsoFormat:
    """TC-DP03: ISO 8601形式の解析（正常系）。"""

    @pytest.mark.parametrize(
        "text, expected",
        [
            ("2026-03-14", date(2026, 3, 14)),
            ("2026-12-31", date(2026, 12, 31)),
            ("2027-01-01", date(2027, 1, 1)),
        ],
    )
    def test_iso_format(self, text: str, expected: date) -> None:
        """ISO 8601形式の日付文字列から正しいdateオブジェクトが返される。

        Given: ISO 8601形式の日付文字列（YYYY-MM-DD）
        When: DateParser().parse(text) を呼び出す
        Then: 正しいdateオブジェクトが返される
        """
        parser = DateParser()
        result = parser.parse(text)
        assert result == expected


class TestDateParserInvalidText:
    """TC-DP04: 解析できない文字列（異常系）。"""

    @pytest.mark.parametrize(
        "invalid_text",
        [
            "あさって以降",    # 不明瞭な表現
            "いつか",          # 特定できない
            "ABC",             # 英数字のみ
            "",                # 空文字列
            "XXXX-YY-ZZ",      # 不正なISO形式
        ],
    )
    def test_invalid_text_raises_value_error(self, invalid_text: str) -> None:
        """解析できない日付表現でValueErrorが発生する。

        Given: 解析できない日付表現
        When: DateParser().parse(invalid_text) を呼び出す
        Then: ValueError が発生する
        """
        parser = DateParser()
        with pytest.raises(ValueError, match="日付を解析できません"):
            parser.parse(invalid_text)


class TestDateParserMonthDayFormat:
    """TC-DP05: M/D形式の解析（正常系）。"""

    @pytest.mark.parametrize(
        "text, base_date, expected",
        [
            ("3/14", date(2026, 3, 3), date(2026, 3, 14)),   # 同年
            ("1/5", date(2026, 12, 3), date(2027, 1, 5)),    # 年をまたぐ（来年）
        ],
    )
    def test_month_day_format(self, text: str, base_date: date, expected: date) -> None:
        """M/D形式の日付文字列から正しいdateオブジェクトが返される。

        Given: M/D形式の日付文字列
        When: DateParser(base_date).parse(text) を呼び出す
        Then: 今年（または来年）の指定月日のdateオブジェクトが返される
              過去の日付になる場合は来年として解釈する
        """
        parser = DateParser(base_date=base_date)
        result = parser.parse(text)
        assert result == expected
