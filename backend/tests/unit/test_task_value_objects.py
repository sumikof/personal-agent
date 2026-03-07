"""TaskStatusVO / TaskPriorityVO 値オブジェクトの単体テスト（FEAT-003）。

DSD-008_FEAT-003 の 4.1 に従い実装する。
TDD: テストを先に書き、実装が通るように実装を進める。

テストケース:
    TC-S01: TaskStatusVO.from_id - 有効なステータスID（正常系）
    TC-S02: TaskStatusVO.from_id - 無効なステータスID（異常系）
    TC-S03: TaskStatusVO.validate_id - 検証
"""
from __future__ import annotations

import pytest

from app.domain.task.value_objects import TaskPriorityVO, TaskStatusVO


# ---------------------------------------------------------------------------
# TC-S01: TaskStatusVO.from_id - 有効なステータスID（正常系）
# ---------------------------------------------------------------------------


class TestTaskStatusVOFromId:
    """TaskStatusVO.from_id の正常系テスト。"""

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
        """TC-S01: 有効なステータスID から正しい名称の TaskStatusVO が返される。

        Given: 有効なステータスID（1, 2, 3, 5 のいずれか）
        When: TaskStatusVO.from_id(status_id) を呼び出す
        Then: 正しい名称の TaskStatusVO オブジェクトが返される
        """
        # When
        status = TaskStatusVO.from_id(status_id)

        # Then
        assert status.id == status_id
        assert status.name == expected_name

    def test_from_id_returns_frozen_object(self) -> None:
        """from_id が返すオブジェクトは frozen（不変）であること。"""
        status = TaskStatusVO.from_id(1)
        with pytest.raises(Exception):  # FrozenInstanceError
            status.id = 99  # type: ignore[misc]


# ---------------------------------------------------------------------------
# TC-S02: TaskStatusVO.from_id - 無効なステータスID（異常系）
# ---------------------------------------------------------------------------


class TestTaskStatusVOFromIdInvalid:
    """TaskStatusVO.from_id の異常系テスト。"""

    @pytest.mark.parametrize("invalid_id", [0, 4, 6, 100, -1])
    def test_from_id_invalid_raises_value_error(self, invalid_id: int) -> None:
        """TC-S02: 無効なステータスID で ValueError が発生する。

        Given: 無効なステータスID（{1,2,3,5} 以外）
        When: TaskStatusVO.from_id(invalid_id) を呼び出す
        Then: ValueError が発生する
        """
        with pytest.raises(ValueError, match="無効なステータスID"):
            TaskStatusVO.from_id(invalid_id)


# ---------------------------------------------------------------------------
# TC-S03: TaskStatusVO.validate_id - 検証
# ---------------------------------------------------------------------------


class TestTaskStatusVOValidateId:
    """TaskStatusVO.validate_id のテスト。"""

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
        """TC-S03: 有効なIDはTrue、無効なIDはFalseが返される。

        Given: ステータスID
        When: TaskStatusVO.validate_id(status_id) を呼び出す
        Then: 有効な場合は True、無効な場合は False が返される
        """
        assert TaskStatusVO.validate_id(status_id) == expected


# ---------------------------------------------------------------------------
# TaskStatusVO の環境変数対応テスト
# ---------------------------------------------------------------------------


class TestTaskStatusVOEnvVar:
    """TaskStatusVO が環境変数でステータスIDを設定できることのテスト。"""

    def test_custom_status_id_via_env_var(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """環境変数でステータスIDをカスタマイズできること。

        Given: REDMINE_STATUS_ID_CLOSED=10 に設定する
        When: TaskStatusVO.from_id(10) を呼び出す
        Then: name="完了" の TaskStatusVO が返される
        """
        monkeypatch.setenv("REDMINE_STATUS_ID_CLOSED", "10")

        status = TaskStatusVO.from_id(10)

        assert status.id == 10
        assert status.name == "完了"

    def test_default_closed_id_3_not_valid_when_env_changed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """環境変数で完了IDを変更すると、デフォルトの3が無効になること。

        Given: REDMINE_STATUS_ID_CLOSED=10 に設定する
        When: TaskStatusVO.from_id(3) を呼び出す
        Then: ValueError が発生する（3は完了IDではなくなる）
        """
        monkeypatch.setenv("REDMINE_STATUS_ID_CLOSED", "10")

        with pytest.raises(ValueError, match="無効なステータスID"):
            TaskStatusVO.from_id(3)


# ---------------------------------------------------------------------------
# TaskPriorityVO のテスト
# ---------------------------------------------------------------------------


class TestTaskPriorityVOFromId:
    """TaskPriorityVO.from_id のテスト。"""

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
        """有効な優先度IDから正しい名称の TaskPriorityVO が返される。

        Given: 有効な優先度ID（1-5）
        When: TaskPriorityVO.from_id(priority_id) を呼び出す
        Then: 正しい名称の TaskPriorityVO が返される
        """
        priority = TaskPriorityVO.from_id(priority_id)

        assert priority.id == priority_id
        assert priority.name == expected_name

    @pytest.mark.parametrize("invalid_id", [0, 6, -1, 100])
    def test_from_id_invalid_raises_value_error(self, invalid_id: int) -> None:
        """無効な優先度IDで ValueError が発生する。

        Given: 無効な優先度ID（{1,2,3,4,5} 以外）
        When: TaskPriorityVO.from_id(invalid_id) を呼び出す
        Then: ValueError が発生する
        """
        with pytest.raises(ValueError, match="無効な優先度ID"):
            TaskPriorityVO.from_id(invalid_id)
