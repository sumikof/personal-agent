"""ドメイン層の例外定義。"""
from __future__ import annotations


class DomainError(Exception):
    """ドメイン層の基底例外クラス。"""

    def __init__(self, message: str = "") -> None:
        self.message = message
        super().__init__(message)


class TaskValidationError(DomainError):
    """タスクのバリデーションエラー。

    タスクタイトルの未入力・長さ超過・優先度不正などのバリデーション違反時に発生する。
    """

    def __init__(self, message: str = "", field: str = "") -> None:
        self.field = field
        super().__init__(message)


class RedmineConnectionError(DomainError):
    """Redmine への接続失敗エラー。

    ネットワーク接続エラー・タイムアウト時に発生する。
    """

    def __init__(self, message: str = "Redmine への接続に失敗しました") -> None:
        super().__init__(message)


class RedmineAuthError(DomainError):
    """Redmine の認証エラー。

    API キーが無効または権限不足の場合に発生する。
    """

    def __init__(self, message: str = "Redmine API キーの認証に失敗しました") -> None:
        super().__init__(message)


class RedmineAPIError(DomainError):
    """Redmine API のエラーレスポンス。

    Redmine が 4xx/5xx のエラーレスポンスを返した場合に発生する。
    """

    def __init__(
        self,
        message: str = "Redmine API エラーが発生しました",
        status_code: int = 0,
    ) -> None:
        self.status_code = status_code
        super().__init__(message)


class RedmineNotFoundError(DomainError):
    """Redmine のリソース未存在エラー。

    指定したプロジェクト・チケットが存在しない場合に発生する。
    """

    def __init__(self, message: str = "指定したリソースが見つかりません") -> None:
        super().__init__(message)


class NotFoundException(DomainError):
    """リソース未存在エラー。

    指定したリソースが存在しない場合、または論理削除済みの場合に発生する。
    """

    def __init__(self, message: str = "指定したリソースが見つかりません") -> None:
        self.status_code = 404
        super().__init__(message)


class AgentExecutionError(DomainError):
    """エージェント実行エラー。

    LangGraphワークフロー実行中にエラーが発生した場合に raise される。
    """

    def __init__(self, message: str = "エージェント実行エラーが発生しました") -> None:
        super().__init__(message)


# FEAT-003: Redmineタスク更新・進捗報告 用の例外

class TaskNotFoundError(DomainError):
    """指定された Issue ID のタスクが存在しない場合に発生する。"""

    def __init__(self, issue_id: int) -> None:
        self.issue_id = issue_id
        super().__init__(f"タスク #{issue_id} は存在しません")


class TaskDeleteOperationForbiddenError(DomainError):
    """エージェント経由のタスク削除試行時に発生する（BR-02）。"""

    def __init__(self) -> None:
        super().__init__(
            "エージェント経由のタスク削除操作は禁止されています（BR-02）。"
            "削除はRedmine Web UIから行ってください。"
        )


class InvalidStatusIdError(ValueError):
    """無効なステータスIDが指定された場合に発生する。"""

    def __init__(self, status_id: int, valid_ids: set[int]) -> None:
        self.status_id = status_id
        super().__init__(
            f"無効なステータスID: {status_id}。有効値: {sorted(valid_ids)}"
        )


# FEAT-004: タスク優先度・スケジュール調整 用の例外

class InvalidPriorityError(ValueError):
    """無効な優先度IDが指定された場合に発生する（FEAT-004）。"""

    def __init__(self, priority_id: int) -> None:
        self.priority_id = priority_id
        super().__init__(
            f"無効な優先度ID: {priority_id}。有効値: {{1, 2, 3, 4, 5}}"
        )
