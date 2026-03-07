"""タスク更新 API のリクエスト/レスポンス Pydantic モデル（FEAT-003）。

DSD-001_FEAT-003 の 2.1 および DSD-003_FEAT-003 に従い実装する。
"""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.domain.task.value_objects import TaskStatusVO


class UpdateTaskRequest(BaseModel):
    """PUT /api/v1/tasks/{id} のリクエストスキーマ。

    status_id または notes のいずれか少なくとも1つは必須。
    両方 None の場合は ValidationError を発生させる。

    status_id が指定される場合は有効値（環境変数で設定した値）のいずれかであること。
    notes が指定される場合は空文字列・スペースのみは不可。
    """

    status_id: int | None = Field(
        default=None,
        description=(
            "新しいステータスID。"
            "有効値は環境変数 REDMINE_STATUS_ID_* で設定する（デフォルト: 1=未着手, 2=進行中, 3=完了, 5=却下）。"
        ),
    )
    notes: str | None = Field(
        default=None,
        description="ステータス変更時に追加するコメント、またはコメントのみを追加する場合の内容。",
    )

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "UpdateTaskRequest":
        """status_id または notes のいずれか少なくとも1つが必須。"""
        if self.status_id is None and self.notes is None:
            raise ValueError(
                "status_id または notes のいずれか少なくとも1つを指定してください"
            )
        return self

    @model_validator(mode="after")
    def validate_status_id(self) -> "UpdateTaskRequest":
        """status_id が指定された場合は有効値であること。"""
        if self.status_id is not None and not TaskStatusVO.validate_id(self.status_id):
            raise ValueError(
                f"無効なステータスID: {self.status_id}。"
                f"有効値: {sorted(TaskStatusVO.get_valid_ids())}"
            )
        return self

    @model_validator(mode="after")
    def validate_notes_not_blank(self) -> "UpdateTaskRequest":
        """notes が指定された場合は空文字列・スペースのみは不可。"""
        if self.notes is not None and not self.notes.strip():
            raise ValueError("コメント内容は空にできません（スペースのみ不可）")
        return self
