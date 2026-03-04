"""自然言語日付解析ユーティリティ（FEAT-004）。

DSD-001_FEAT-004 セクション 8 に従い実装する。
「明日」「3日後」「来週金曜」「2026-03-14」「3/14」などの表現を date オブジェクトに変換する。
"""
from __future__ import annotations

import re
from datetime import date, timedelta


# 曜日名から Python の weekday() 値へのマッピング（0=月曜, 6=日曜）
_WEEKDAY_MAP: dict[str, int] = {
    "月": 0,
    "火": 1,
    "水": 2,
    "木": 3,
    "金": 4,
    "土": 5,
    "日": 6,
    "月曜": 0,
    "火曜": 1,
    "水曜": 2,
    "木曜": 3,
    "金曜": 4,
    "土曜": 5,
    "日曜": 6,
    "月曜日": 0,
    "火曜日": 1,
    "水曜日": 2,
    "木曜日": 3,
    "金曜日": 4,
    "土曜日": 5,
    "日曜日": 6,
}


class DateParser:
    """自然言語の日付表現を date オブジェクトに変換するパーサー。

    FEAT-004 のユースケース UC-006（タスクの期日変更）で使用する。

    対応する表現:
        - 相対日付: 「明日」「N日後」「N週間後」
        - 曜日指定: 「今週○曜日」「来週○曜日」
        - ISO 8601: 「YYYY-MM-DD」
        - M/D 形式: 「M/D」（過去日の場合は翌年として解釈）

    Args:
        base_date: 相対日付計算の基準日。省略時は実行時の当日を使用する。
    """

    def __init__(self, base_date: date | None = None) -> None:
        self._base_date = base_date or date.today()

    def parse(self, text: str) -> date:
        """日付表現の文字列を date オブジェクトに変換する。

        Args:
            text: 日付表現の文字列。

        Returns:
            解析された date オブジェクト。

        Raises:
            ValueError: 日付を解析できない場合。エラーメッセージに「日付を解析できません」を含む。
        """
        text = text.strip()

        if not text:
            raise ValueError(f"日付を解析できません: {text!r}")

        # ISO 8601 形式（YYYY-MM-DD）
        result = self._parse_iso_format(text)
        if result is not None:
            return result

        # 相対日付: 「明日」
        if text == "明日":
            return self._base_date + timedelta(days=1)

        # 相対日付: 「N日後」
        result = self._parse_n_days_later(text)
        if result is not None:
            return result

        # 相対日付: 「N週間後」
        result = self._parse_n_weeks_later(text)
        if result is not None:
            return result

        # 今週・来週 の曜日指定
        result = self._parse_weekday(text)
        if result is not None:
            return result

        # M/D 形式
        result = self._parse_month_day(text)
        if result is not None:
            return result

        raise ValueError(f"日付を解析できません: {text!r}")

    def _parse_iso_format(self, text: str) -> date | None:
        """ISO 8601 形式（YYYY-MM-DD）を解析する。"""
        # YYYY-MM-DD パターン（完全一致）
        match = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", text)
        if match:
            try:
                return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                # 不正な日付（例: 2026-13-01）
                raise ValueError(f"日付を解析できません: {text!r}")
        return None

    def _parse_n_days_later(self, text: str) -> date | None:
        """「N日後」形式を解析する。"""
        match = re.fullmatch(r"(\d+)日後", text)
        if match:
            n = int(match.group(1))
            return self._base_date + timedelta(days=n)
        return None

    def _parse_n_weeks_later(self, text: str) -> date | None:
        """「N週間後」形式を解析する。"""
        match = re.fullmatch(r"(\d+)週間後", text)
        if match:
            n = int(match.group(1))
            return self._base_date + timedelta(weeks=n)
        return None

    def _parse_weekday(self, text: str) -> date | None:
        """「今週○曜日」「来週○曜日」形式を解析する。

        曜日名の後に「日」が付く場合も対応する（例: 「今週火曜日」）。
        """
        # 今週・来週の判定
        is_next_week: bool | None = None
        rest = text

        if text.startswith("今週"):
            is_next_week = False
            rest = text[2:]
        elif text.startswith("来週"):
            is_next_week = True
            rest = text[2:]
        else:
            return None

        # 残りの文字列から曜日を取得
        weekday_num: int | None = None
        for name, num in sorted(_WEEKDAY_MAP.items(), key=lambda x: -len(x[0])):
            if rest == name or rest.startswith(name):
                weekday_num = num
                break

        if weekday_num is None:
            return None

        # 基準日の曜日
        base_weekday = self._base_date.weekday()

        if is_next_week:
            # 来週：基準日の翌週（月〜日）の指定曜日
            # 来週月曜日 = 基準日 + (7 - base_weekday + 0) 日
            days_to_next_monday = (7 - base_weekday) % 7
            if days_to_next_monday == 0:
                days_to_next_monday = 7  # 今日が月曜の場合は7日後が来週月曜
            next_monday = self._base_date + timedelta(days=days_to_next_monday)
            return next_monday + timedelta(days=weekday_num)
        else:
            # 今週：今週の指定曜日（基準日を含む週の月〜日）
            days_to_this_monday = base_weekday  # 今週月曜日までの日数
            this_monday = self._base_date - timedelta(days=days_to_this_monday)
            target = this_monday + timedelta(days=weekday_num)
            return target

    def _parse_month_day(self, text: str) -> date | None:
        """「M/D」形式を解析する。

        過去の日付になる場合は翌年として解釈する。
        """
        match = re.fullmatch(r"(\d{1,2})/(\d{1,2})", text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            try:
                target = date(self._base_date.year, month, day)
            except ValueError:
                raise ValueError(f"日付を解析できません: {text!r}")

            # 過去の日付（基準日より前）は翌年として解釈
            if target < self._base_date:
                try:
                    target = date(self._base_date.year + 1, month, day)
                except ValueError:
                    raise ValueError(f"日付を解析できません: {text!r}")
            return target
        return None
