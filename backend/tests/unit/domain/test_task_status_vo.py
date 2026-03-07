"""FEAT-003: TaskStatusVO 値オブジェクトの単体テスト（DSD-008 TC-S01〜S03）。

TDD Red フェーズ: テストを先に書き、実装が存在しない状態で失敗させる。
Green フェーズ: 最小実装でグリーンにする。
"""
from __future__ import annotations

import pytest

from app.domain.task.value_objects import TaskStatusVO


# ---------------------------------------------------------------------------
# TC-S01: TaskStatusVO.from_id - 有効なステータスID（正常系）
# ---------------------------------------------------------------------------


class TestTaskStatusVOFromId:
    """TC-S01: TaskStatusVO.from_id - 有効なステータスID（正常系）。"""

    @pytest.mark.parametrize(
        "status_id, expected_name",
        [
            (1, "未着手"),
            (2, "進行中"),
            (3, "完了"),
            (5, "却下"),
        ],
    )
    def test_from_id_valid(self, status_id: int, expected_name: str) -> None:
        """有効なステータスID（1, 2, 3, 5）から正しい TaskStatusVO オブジェクトを生成する。

        Given: 有効なステータスID（1, 2, 3, 5のいずれか）
        When: TaskStatusVO.from_id(status_id) を呼び出す
        Then: 正しい名称のTaskStatusVOオブジェクトが返される
        """
        status = TaskStatusVO.from_id(status_id)
        assert status.id == status_id
        assert status.name == expected_name


# ---------------------------------------------------------------------------
# TC-S02: TaskStatusVO.from_id - 無効なステータスID（異常系）
# ---------------------------------------------------------------------------


class TestTaskStatusVOFromIdInvalid:
    """TC-S02: TaskStatusVO.from_id - 無効なステータスID（異常系）。"""

    @pytest.mark.parametrize("invalid_id", [0, 4, 6, 100, -1])
    def test_from_id_invalid_raises_value_error(self, invalid_id: int) -> None:
        """無効なステータスID（{1,2,3,5}以外）で ValueError が発生する。

        Given: 無効なステータスID（{1,2,3,5}以外）
        When: TaskStatusVO.from_id(invalid_id) を呼び出す
        Then: ValueError が発生する
        """
        with pytest.raises(ValueError, match="無効なステータスID"):
            TaskStatusVO.from_id(invalid_id)


# ---------------------------------------------------------------------------
# TC-S03: TaskStatusVO.validate_id - 検証
# ---------------------------------------------------------------------------


class TestTaskStatusVOValidateId:
    """TC-S03: TaskStatusVO.validate_id - 有効・無効の判定。"""

    @pytest.mark.parametrize(
        "status_id, expected",
        [
            (1, True),
            (2, True),
            (3, True),
            (5, True),
            (0, False),
            (4, False),
            (6, False),
            (10, False),
        ],
    )
    def test_validate_id(self, status_id: int, expected: bool) -> None:
        """有効なIDはTrue、無効なIDはFalseが返される。

        Given: ステータスID
        When: TaskStatusVO.validate_id(status_id) を呼び出す
        Then: 有効なIDはTrue、無効なIDはFalseが返される
        """
        assert TaskStatusVO.validate_id(status_id) == expected
