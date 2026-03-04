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
