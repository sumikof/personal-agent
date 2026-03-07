"""FEAT-003: UpdateTaskRequest バリデーションの単体テスト（DSD-008 TC-VAL01〜VAL04）。

設計差異メモ: DSD-008 では `app.presentation.schemas.task_update` のパスを指定しているが、
実際の実装は `app.api.v1.schemas.task_update` に配置されている。

TDD Green フェーズ: 実装済みの UpdateTaskRequest に対してテストを実行する。
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.api.v1.schemas.task_update import UpdateTaskRequest


# ---------------------------------------------------------------------------
# TC-VAL01: UpdateTaskRequest - status_id有効値（正常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskRequestValidStatusId:
    """TC-VAL01: UpdateTaskRequest - status_id有効値（正常系）。"""

    @pytest.mark.parametrize("status_id", [1, 2, 3, 5])
    def test_valid_status_id(self, status_id: int) -> None:
        """有効なstatus_id（1, 2, 3, 5のいずれか）でバリデーションエラーなしで生成される。

        Given: 有効なstatus_id（1, 2, 3, 5のいずれか）
        When: UpdateTaskRequest(status_id=status_id) を作成する
        Then: バリデーションエラーなしでオブジェクトが生成される
        """
        req = UpdateTaskRequest(status_id=status_id)
        assert req.status_id == status_id

    def test_valid_notes_only(self) -> None:
        """notesのみ指定した場合もバリデーションエラーなし。

        Given: notes="テストコメント"（status_id は None）
        When: UpdateTaskRequest(notes="テストコメント") を作成する
        Then: バリデーションエラーなしでオブジェクトが生成される
        """
        req = UpdateTaskRequest(notes="テストコメント")
        assert req.notes == "テストコメント"
        assert req.status_id is None

    def test_valid_both_status_id_and_notes(self) -> None:
        """status_id と notes 両方を指定した場合もバリデーションエラーなし。

        Given: status_id=3、notes="完了しました"
        When: UpdateTaskRequest(status_id=3, notes="完了しました") を作成する
        Then: バリデーションエラーなしでオブジェクトが生成される
        """
        req = UpdateTaskRequest(status_id=3, notes="完了しました")
        assert req.status_id == 3
        assert req.notes == "完了しました"


# ---------------------------------------------------------------------------
# TC-VAL02: UpdateTaskRequest - status_id無効値（異常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskRequestInvalidStatusId:
    """TC-VAL02: UpdateTaskRequest - status_id無効値（異常系）。"""

    @pytest.mark.parametrize("invalid_id", [0, 4, 6, 10, -1])
    def test_invalid_status_id_raises_validation_error(self, invalid_id: int) -> None:
        """無効なstatus_idで ValidationError が発生する。

        Given: 無効なstatus_id（{1,2,3,5}以外）
        When: UpdateTaskRequest(status_id=invalid_id) を作成する
        Then: ValidationError が発生する
        """
        with pytest.raises(ValidationError):
            UpdateTaskRequest(status_id=invalid_id)


# ---------------------------------------------------------------------------
# TC-VAL03: UpdateTaskRequest - notesが空文字（異常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskRequestBlankNotes:
    """TC-VAL03: UpdateTaskRequest - notesが空文字（異常系）。"""

    @pytest.mark.parametrize("blank_notes", ["", "  ", "\n"])
    def test_blank_notes_raises_validation_error(self, blank_notes: str) -> None:
        """空文字またはスペースのみのnotesで ValidationError が発生する。

        Given: 空文字またはスペースのみのnotes
        When: UpdateTaskRequest(notes=blank_notes) を作成する
        Then: ValidationError が発生する
        """
        with pytest.raises(ValidationError):
            UpdateTaskRequest(notes=blank_notes)


# ---------------------------------------------------------------------------
# TC-VAL04: UpdateTaskRequest - 全フィールドがNone（異常系）
# ---------------------------------------------------------------------------


class TestUpdateTaskRequestNoFields:
    """TC-VAL04: UpdateTaskRequest - 全フィールドがNone（異常系）。"""

    def test_no_fields_raises_validation_error(self) -> None:
        """更新フィールドが1つもない（全てNone）と ValidationError が発生する。

        Given: 更新フィールドが1つもない（全てNone）
        When: UpdateTaskRequest() を作成する
        Then: ValidationError が発生する
        """
        with pytest.raises(ValidationError):
            UpdateTaskRequest()
