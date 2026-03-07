"""Redmine REST API アダプター。"""
from __future__ import annotations

import asyncio
import logging

import httpx

from app.domain.exceptions import (
    RedmineAPIError,
    RedmineAuthError,
    RedmineConnectionError,
    RedmineNotFoundError,
    TaskNotFoundError,
)

logger = logging.getLogger(__name__)

MAX_RETRY_COUNT = 3
RETRY_DELAYS = [1.0, 2.0, 4.0]  # 秒（指数バックオフ）


class RedmineAdapter:
    """Redmine REST API を呼び出すアダプタークラス。

    HTTP リクエストのリトライ・エラーハンドリング・認証ヘッダーの付与を担う。
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    def _get_headers(self) -> dict[str, str]:
        """Redmine API リクエスト用のヘッダーを返す。"""
        return {
            "X-Redmine-API-Key": self._api_key,
            "Content-Type": "application/json",
        }

    def _handle_error(self, response: httpx.Response) -> None:
        """HTTP レスポンスのエラーをドメイン例外に変換する。

        Raises:
            RedmineAuthError: HTTP 401 の場合。
            RedmineNotFoundError: HTTP 404 の場合。
            RedmineAPIError: HTTP 4xx（401/404 以外）の場合。
        """
        if response.status_code == 401:
            raise RedmineAuthError("Redmine API キーの認証に失敗しました（HTTP 401）")

        if response.status_code == 404:
            raise RedmineNotFoundError("指定したリソースが見つかりません（HTTP 404）")

        if 400 <= response.status_code < 500:
            # エラーメッセージを抽出
            error_messages: list[str] = []
            try:
                body = response.json()
                if "errors" in body:
                    error_messages = body["errors"]
            except Exception:
                pass

            message = (
                "、".join(error_messages)
                if error_messages
                else f"Redmine API エラー（HTTP {response.status_code}）"
            )
            raise RedmineAPIError(message, status_code=response.status_code)

    async def _retry_request(
        self,
        method: str,
        url: str,
        **kwargs: object,
    ) -> httpx.Response:
        """HTTP リクエストをリトライ付きで実行する。

        接続エラーまたは 5xx エラー時に最大3回リトライする。
        リトライ間隔は指数バックオフ（1秒→2秒→4秒）。
        401/404 などのクライアントエラーはリトライしない。
        """
        last_error: Exception | None = None

        for attempt in range(MAX_RETRY_COUNT):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=self._get_headers(),
                        **kwargs,
                    )

                # 4xx エラーはリトライせずに即時エラー処理
                if 400 <= response.status_code < 500:
                    self._handle_error(response)
                    return response  # _handle_error が例外を上げるので到達しない

                # 5xx エラーはリトライ対象
                if response.status_code >= 500:
                    logger.warning(
                        "redmine_server_error_retrying attempt=%d status_code=%d url=%s",
                        attempt + 1,
                        response.status_code,
                        url,
                    )
                    last_error = RedmineAPIError(
                        f"Redmine サーバーエラー: {response.status_code}",
                        status_code=response.status_code,
                    )
                    if attempt < MAX_RETRY_COUNT - 1:
                        await asyncio.sleep(RETRY_DELAYS[attempt])
                    continue

                return response

            except (httpx.ConnectError, httpx.TimeoutException) as e:
                logger.warning(
                    "redmine_connection_error_retrying attempt=%d error=%s url=%s",
                    attempt + 1,
                    str(e),
                    url,
                )
                last_error = RedmineConnectionError(f"Redmine 接続エラー: {str(e)}")
                if attempt < MAX_RETRY_COUNT - 1:
                    await asyncio.sleep(RETRY_DELAYS[attempt])

        # 全リトライ失敗
        logger.error("redmine_all_retries_failed max_retries=%d url=%s", MAX_RETRY_COUNT, url)
        # 5xx エラーによるリトライ失敗は RedmineConnectionError として返す（サーバー側の問題）
        if isinstance(last_error, RedmineAPIError) and last_error.status_code >= 500:
            raise RedmineConnectionError(
                f"Redmine サーバーが応答しません（HTTP {last_error.status_code}）"
            )
        raise last_error or RedmineConnectionError("Redmine への接続に失敗しました")

    async def create_issue(
        self,
        subject: str,
        project_id: int,
        description: str | None = None,
        priority_id: int = 2,
        due_date: str | None = None,
        status_id: int = 1,
    ) -> dict:
        """Redmine に Issue（チケット）を作成する。

        Args:
            subject: チケットのタイトル（件名）。
            project_id: Redmine プロジェクト ID。
            description: チケットの詳細説明（任意）。
            priority_id: 優先度 ID（1=低/2=通常/3=高/4=緊急）。デフォルト: 2（通常）。
            due_date: 期日（YYYY-MM-DD 形式）。
            status_id: ステータス ID（デフォルト: 1=新規）。

        Returns:
            Redmine API レスポンスの辞書（"issue" キーを含む）。

        Raises:
            RedmineConnectionError: 接続タイムアウト・ネットワークエラーの場合。
            RedmineAuthError: API キーが無効な場合（HTTP 401）。
            RedmineNotFoundError: プロジェクトが存在しない場合（HTTP 404）。
            RedmineAPIError: その他の API エラーの場合。
        """
        url = f"{self._base_url}/issues.json"

        # リクエストボディ構築
        issue_params: dict[str, object] = {
            "project_id": project_id,
            "subject": subject,
            "priority_id": priority_id,
            "status_id": status_id,
        }
        if description:
            issue_params["description"] = description
        if due_date:
            issue_params["due_date"] = due_date

        payload = {"issue": issue_params}

        logger.info(
            "redmine_create_issue subject=%s project_id=%d priority_id=%d",
            subject[:50],
            project_id,
            priority_id,
        )

        response = await self._retry_request("POST", url, json=payload)

        logger.info(
            "redmine_create_issue_succeeded status_code=%d",
            response.status_code,
        )

        return response.json()

    async def get_issue(self, issue_id: int) -> dict:
        """Redmine から Issue（チケット）を取得する（FEAT-003）。

        Args:
            issue_id: 取得対象の Redmine Issue ID。

        Returns:
            Redmine API レスポンスの辞書（"issue" キーを含む）。

        Raises:
            TaskNotFoundError: チケットが存在しない場合（HTTP 404）。
            RedmineConnectionError: 接続タイムアウト・ネットワークエラーの場合。
            RedmineAuthError: API キーが無効な場合（HTTP 401）。
            RedmineAPIError: その他の API エラーの場合。
        """
        url = f"{self._base_url}/issues/{issue_id}.json"

        logger.debug("redmine_get_issue issue_id=%d", issue_id)

        try:
            response = await self._retry_request("GET", url)
        except RedmineNotFoundError:
            raise TaskNotFoundError(issue_id)
        except RedmineConnectionError:
            raise

        logger.debug(
            "redmine_get_issue_succeeded issue_id=%d status_code=%d",
            issue_id,
            response.status_code,
        )

        return response.json()

    async def update_issue(self, issue_id: int, payload: dict) -> dict:
        """Redmine の Issue（チケット）を更新する（FEAT-003）。

        Redmine の PUT /issues/{id}.json は成功時に 204 No Content を返すため、
        更新後に GET /issues/{id}.json で最新状態を取得して返す。

        Args:
            issue_id: 更新対象の Redmine Issue ID。
            payload: 更新内容（{"issue": {...}} 形式）。

        Returns:
            更新後の Redmine API レスポンスの辞書（"issue" キーを含む）。

        Raises:
            TaskNotFoundError: チケットが存在しない場合（HTTP 404）。
            ValueError: Redmine バリデーションエラーの場合（HTTP 422）。
            RedmineConnectionError: 接続タイムアウト・ネットワークエラーの場合。
            RedmineAuthError: API キーが無効な場合（HTTP 401）。
            RedmineAPIError: その他の API エラーの場合。
        """
        url = f"{self._base_url}/issues/{issue_id}.json"

        logger.debug(
            "redmine_update_issue issue_id=%d payload_keys=%s",
            issue_id,
            list(payload.get("issue", {}).keys()),
        )

        try:
            await self._retry_request("PUT", url, json=payload)
        except RedmineNotFoundError:
            raise TaskNotFoundError(issue_id)
        except RedmineAPIError as e:
            # 422 バリデーションエラーは ValueError として再送出
            if e.status_code == 422:
                raise ValueError(str(e.message)) from e
            raise
        except RedmineConnectionError:
            raise

        logger.info("redmine_update_issue_succeeded issue_id=%d", issue_id)

        # 更新後の最新状態を GET で取得して返す
        return await self.get_issue(issue_id)

    async def list_issues(
        self,
        status_id: str = "open",
        limit: int = 25,
        offset: int = 0,
        due_date: str | None = None,
        subject_like: str | None = None,
        project_id: int | None = None,
    ) -> dict:
        """Redmine から Issue（チケット）の一覧を取得する（FEAT-002）。

        Args:
            status_id: ステータスフィルタ（"open"/"closed"/"*" など）。デフォルト: "open"。
            limit: 取得件数上限（デフォルト: 25）。
            offset: 取得開始位置（ページネーション用）。
            due_date: 期日フィルタ（YYYY-MM-DD 形式）。
            subject_like: タイトル部分一致検索キーワード（Redmine の subject パラメータ）。
            project_id: プロジェクト ID フィルタ。

        Returns:
            Redmine API レスポンスの辞書。キー: issues, total_count, offset, limit。

        Raises:
            RedmineConnectionError: 接続タイムアウト・ネットワークエラーの場合。
            RedmineAuthError: API キーが無効な場合（HTTP 401）。
            RedmineNotFoundError: プロジェクトが存在しない場合（HTTP 404）。
            RedmineAPIError: その他の API エラーの場合。
        """
        url = f"{self._base_url}/issues.json"

        # クエリパラメータ構築
        params: dict[str, str | int] = {
            "status_id": status_id,
            "limit": limit,
            "offset": offset,
        }
        if due_date is not None:
            params["due_date"] = due_date
        if subject_like is not None:
            # Redmine の subject パラメータとして渡す
            params["subject"] = subject_like
        if project_id is not None:
            params["project_id"] = project_id

        logger.debug(
            "redmine_list_issues status_id=%s limit=%d offset=%d",
            status_id,
            limit,
            offset,
        )

        response = await self._retry_request("GET", url, params=params)

        logger.debug(
            "redmine_list_issues_succeeded status_code=%d",
            response.status_code,
        )

        return response.json()
