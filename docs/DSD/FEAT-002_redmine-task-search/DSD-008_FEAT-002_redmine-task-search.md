# DSD-008_FEAT-002 単体テスト設計書（Redmineタスク検索・一覧表示）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-008_FEAT-002 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-002 |
| 機能名 | Redmineタスク検索・一覧表示（redmine-task-search） |
| 入力元 | DSD-001_FEAT-002, DSD-002_FEAT-002, DSD-003_FEAT-002, DSD-005_FEAT-002 |
| ステータス | 初版 |

---

## 目次

1. TDD 方針
2. テスト対象一覧
3. conftest.py / フィクスチャ設計
4. バックエンド単体テスト設計
5. フロントエンド単体テスト設計
6. カバレッジ目標
7. テスト実行コマンド

---

## 1. TDD 方針

### 1.1 Red → Green → Refactor サイクル

DSD-008 で定義するテストケースを実装前に記述し（Red）、実装によってテストをパスさせ（Green）、コードを整理（Refactor）する。

```
Red   : テストを書く → pytest でテスト失敗を確認
Green : 最小限の実装でテストをパスさせる
Refactor: 可読性・保守性を高めながらテストが引き続きパスすることを確認
```

### 1.2 テストの命名規則

```
test_{テスト対象}_{条件}_{期待する結果}
```

例:
- `test_search_tasks_tool_with_open_status_returns_markdown_list`
- `test_list_issues_when_connection_error_raises_redmine_connection_error`
- `test_build_redmine_params_when_all_status_maps_to_asterisk`

### 1.3 Given-When-Then 記法

各テストケースは Given-When-Then で記述する。

```python
async def test_example():
    # Given: テストの前提条件
    adapter = MockRedmineAdapter(...)

    # When: テスト対象の操作
    result = await service.search_tasks(status="open")

    # Then: 期待する結果
    assert len(result) == 2
```

---

## 2. テスト対象一覧

### 2.1 バックエンド

| テスト対象 | モジュール | テストファイル |
|---|---|---|
| `search_tasks_tool` 関数 | `app/agent/tools/search_tasks_tool.py` | `tests/agent/tools/test_search_tasks_tool.py` |
| `_format_markdown_list` 関数 | `app/agent/tools/search_tasks_tool.py` | `tests/agent/tools/test_search_tasks_tool.py` |
| `TaskSearchService.search_tasks` | `app/application/task/task_search_service.py` | `tests/application/task/test_task_search_service.py` |
| `TaskSearchService._build_redmine_params` | `app/application/task/task_search_service.py` | `tests/application/task/test_task_search_service.py` |
| `TaskSearchService._format_task` | `app/application/task/task_search_service.py` | `tests/application/task/test_task_search_service.py` |
| `RedmineAdapter.list_issues` | `app/infra/redmine/redmine_adapter.py` | `tests/infra/redmine/test_redmine_adapter_list.py` |
| `GET /api/v1/tasks` エンドポイント | `app/api/v1/tasks.py` | `tests/api/v1/test_tasks_api.py` |

### 2.2 フロントエンド

| テスト対象 | コンポーネント/フック | テストファイル |
|---|---|---|
| `MarkdownContent` リンクレンダリング | `src/components/chat/MarkdownContent.tsx` | `src/components/chat/__tests__/MarkdownContent.test.tsx` |
| `MarkdownContent` 太字レンダリング | `src/components/chat/MarkdownContent.tsx` | `src/components/chat/__tests__/MarkdownContent.test.tsx` |
| `AgentStatusBar` search_tasks バッジ | `src/components/chat/AgentStatusBar.tsx` | `src/components/chat/__tests__/AgentStatusBar.test.tsx` |
| `useChat` tool_call SSE ハンドラ | `src/hooks/useChat.ts` | `src/hooks/__tests__/useChat.test.ts` |

---

## 3. conftest.py / フィクスチャ設計

### 3.1 バックエンド conftest.py

```python
# tests/conftest.py
from __future__ import annotations

import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_redmine_adapter() -> MagicMock:
    """RedmineAdapter の Mock オブジェクト。

    list_issues・create_issue メソッドを AsyncMock として提供する。
    """
    adapter = MagicMock()
    adapter.list_issues = AsyncMock()
    adapter.create_issue = AsyncMock()
    return adapter


@pytest.fixture
def task_search_service(mock_redmine_adapter: MagicMock):
    """TaskSearchService インスタンス（Redmine Adapter をモック化）。"""
    from app.application.task.task_search_service import TaskSearchService
    return TaskSearchService(redmine_adapter=mock_redmine_adapter)


@pytest.fixture
def sample_redmine_issue() -> dict:
    """Redmine GET /issues.json レスポンスのサンプルチケット 1 件。"""
    return {
        "id": 123,
        "project": {"id": 1, "name": "パーソナルエージェント開発"},
        "tracker": {"id": 1, "name": "バグ"},
        "status": {"id": 1, "name": "新規"},
        "priority": {"id": 3, "name": "高"},
        "author": {"id": 1, "name": "Redmine Admin"},
        "assigned_to": None,
        "subject": "設計書レビュー",
        "description": "DSD-001〜DSD-008 のレビューを実施する",
        "start_date": "2026-03-01",
        "due_date": "2026-03-03",
        "done_ratio": 0,
        "is_private": False,
        "estimated_hours": None,
        "created_on": "2026-02-20T09:00:00Z",
        "updated_on": "2026-03-01T14:30:00Z",
        "closed_on": None,
    }


@pytest.fixture
def sample_redmine_issues_response(sample_redmine_issue: dict) -> dict:
    """Redmine GET /issues.json の成功レスポンス（3 件）。"""
    issue2 = {**sample_redmine_issue, "id": 124, "subject": "API テスト実施",
               "priority": {"id": 2, "name": "通常"}, "assigned_to": None, "description": None}
    issue3 = {**sample_redmine_issue, "id": 125, "subject": "ドキュメント更新",
               "priority": {"id": 1, "name": "低"}, "description": ""}
    return {
        "issues": [sample_redmine_issue, issue2, issue3],
        "total_count": 3,
        "offset": 0,
        "limit": 25,
    }


@pytest.fixture
def empty_redmine_response() -> dict:
    """Redmine GET /issues.json の 0 件レスポンス。"""
    return {
        "issues": [],
        "total_count": 0,
        "offset": 0,
        "limit": 25,
    }
```

### 3.2 pytest.ini 設定

```ini
# pyproject.toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = [
    "unit: 単体テスト",
    "integration: 結合テスト",
]
```

---

## 4. バックエンド単体テスト設計

### 4.1 search_tasks_tool 関数テスト

```python
# tests/agent/tools/test_search_tasks_tool.py
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agent.tools.search_tasks_tool import search_tasks_tool, _format_markdown_list


class TestSearchTasksTool:
    """search_tasks_tool 関数の単体テスト。"""

    # ------------------------------------------------------------------ #
    # TC-001: status="open"、due_date あり → Markdown タスク一覧を返す     #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_tool_with_open_status_returns_markdown_list(
        self, sample_tasks: list[dict]
    ):
        """
        Given: status="open", due_date="2026-03-03" を指定
        When:  search_tasks_tool を呼び出す
        Then:  Markdown 形式のタスク一覧文字列が返る
        """
        # Given
        mock_service = MagicMock()
        mock_service.search_tasks = AsyncMock(return_value=sample_tasks)

        with patch(
            "app.agent.tools.search_tasks_tool.TaskSearchService",
            return_value=mock_service,
        ), patch("app.agent.tools.search_tasks_tool.RedmineAdapter"), patch(
            "app.agent.tools.search_tasks_tool.get_settings"
        ):
            # When
            result = await search_tasks_tool.ainvoke({
                "status": "open",
                "due_date": "2026-03-03",
            })

        # Then
        assert isinstance(result, str)
        assert "タスク一覧" in result
        assert "設計書レビュー" in result
        assert "http://localhost:8080/issues/123" in result

    # ------------------------------------------------------------------ #
    # TC-002: 0 件の場合 → 「該当するタスクはありません」を返す              #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_tool_with_no_results_returns_empty_message(self):
        """
        Given: 検索結果が 0 件
        When:  search_tasks_tool を呼び出す
        Then:  「該当するタスクはありません」を含む文字列が返る
        """
        # Given
        mock_service = MagicMock()
        mock_service.search_tasks = AsyncMock(return_value=[])

        with patch(
            "app.agent.tools.search_tasks_tool.TaskSearchService",
            return_value=mock_service,
        ), patch("app.agent.tools.search_tasks_tool.RedmineAdapter"), patch(
            "app.agent.tools.search_tasks_tool.get_settings"
        ):
            # When
            result = await search_tasks_tool.ainvoke({
                "keyword": "存在しないタスク",
            })

        # Then
        assert "該当するタスクはありません" in result
        assert "存在しないタスク" in result

    # ------------------------------------------------------------------ #
    # TC-003: Redmine 接続エラー → エラーメッセージ文字列を返す（例外を上げない）#
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_tool_when_connection_error_returns_error_message(self):
        """
        Given: Redmine が接続不能
        When:  search_tasks_tool を呼び出す
        Then:  エラーメッセージ文字列が返る（例外を上げず LLM に渡す）
        """
        # Given
        from app.domain.exceptions import RedmineConnectionError
        mock_service = MagicMock()
        mock_service.search_tasks = AsyncMock(
            side_effect=RedmineConnectionError("接続タイムアウト")
        )

        with patch(
            "app.agent.tools.search_tasks_tool.TaskSearchService",
            return_value=mock_service,
        ), patch("app.agent.tools.search_tasks_tool.RedmineAdapter"), patch(
            "app.agent.tools.search_tasks_tool.get_settings"
        ):
            # When
            result = await search_tasks_tool.ainvoke({})

        # Then
        assert "失敗" in result
        assert isinstance(result, str)  # 例外ではなく文字列で返す

    # ------------------------------------------------------------------ #
    # TC-004: limit=200 → min(200, 100) = 100 件で呼び出す                  #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_tool_clamps_limit_to_100(self):
        """
        Given: limit=200 を指定（最大値を超える）
        When:  search_tasks_tool を呼び出す
        Then:  TaskSearchService.search_tasks が limit=100 で呼ばれる
        """
        # Given
        mock_service = MagicMock()
        mock_service.search_tasks = AsyncMock(return_value=[])

        with patch(
            "app.agent.tools.search_tasks_tool.TaskSearchService",
            return_value=mock_service,
        ), patch("app.agent.tools.search_tasks_tool.RedmineAdapter"), patch(
            "app.agent.tools.search_tasks_tool.get_settings"
        ):
            # When
            await search_tasks_tool.ainvoke({"limit": 200})

        # Then
        call_kwargs = mock_service.search_tasks.call_args.kwargs
        assert call_kwargs["limit"] == 100

    # ------------------------------------------------------------------ #
    # TC-005: keyword が 30 文字を超える場合でもログエラーは出ない            #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_tool_with_long_keyword_does_not_raise(self):
        """
        Given: 100 文字のキーワードを指定
        When:  search_tasks_tool を呼び出す
        Then:  正常に処理される（ログで 30 文字に切り詰め）
        """
        # Given
        mock_service = MagicMock()
        mock_service.search_tasks = AsyncMock(return_value=[])

        with patch(
            "app.agent.tools.search_tasks_tool.TaskSearchService",
            return_value=mock_service,
        ), patch("app.agent.tools.search_tasks_tool.RedmineAdapter"), patch(
            "app.agent.tools.search_tasks_tool.get_settings"
        ):
            # When
            result = await search_tasks_tool.ainvoke({"keyword": "あ" * 100})

        # Then
        assert isinstance(result, str)  # 例外なし


class TestFormatMarkdownList:
    """_format_markdown_list 関数の単体テスト。"""

    # ------------------------------------------------------------------ #
    # TC-006: 3 件のタスク → 番号付き Markdown リストを返す                  #
    # ------------------------------------------------------------------ #
    def test_format_markdown_list_returns_numbered_list(self):
        """
        Given: 3 件のタスクリスト
        When:  _format_markdown_list を呼び出す
        Then:  「1.」「2.」「3.」で始まる Markdown テキストが返る
        """
        # Given
        tasks = [
            {"id": "1", "title": "タスクA", "priority": "high",
             "due_date": "2026-03-03", "url": "http://localhost:8080/issues/1", "status": "新規"},
            {"id": "2", "title": "タスクB", "priority": "normal",
             "due_date": None, "url": "http://localhost:8080/issues/2", "status": "新規"},
            {"id": "3", "title": "タスクC", "priority": "urgent",
             "due_date": "2026-03-05", "url": "http://localhost:8080/issues/3", "status": "進行中"},
        ]

        # When
        result = _format_markdown_list(tasks)

        # Then
        assert "1. " in result
        assert "2. " in result
        assert "3. " in result
        assert "タスクA" in result
        assert "タスクB" in result
        assert "タスクC" in result

    # ------------------------------------------------------------------ #
    # TC-007: 高優先度タスク → **高** で太字表示される                         #
    # ------------------------------------------------------------------ #
    def test_format_markdown_list_bold_high_priority(self):
        """
        Given: priority="high" のタスク
        When:  _format_markdown_list を呼び出す
        Then:  「**高**」が含まれる
        """
        # Given
        tasks = [{"id": "1", "title": "重要なタスク", "priority": "high",
                  "due_date": None, "url": "http://localhost:8080/issues/1", "status": "新規"}]

        # When
        result = _format_markdown_list(tasks)

        # Then
        assert "**高**" in result

    # ------------------------------------------------------------------ #
    # TC-008: 緊急優先度タスク → **🔴 緊急** で表示される                      #
    # ------------------------------------------------------------------ #
    def test_format_markdown_list_urgent_priority_shows_emoji(self):
        """
        Given: priority="urgent" のタスク
        When:  _format_markdown_list を呼び出す
        Then:  「**🔴 緊急**」が含まれる
        """
        # Given
        tasks = [{"id": "1", "title": "緊急タスク", "priority": "urgent",
                  "due_date": "2026-03-03", "url": "http://localhost:8080/issues/1", "status": "新規"}]

        # When
        result = _format_markdown_list(tasks)

        # Then
        assert "**🔴 緊急**" in result

    # ------------------------------------------------------------------ #
    # TC-009: due_date 指定あり → ヘッダに期日を含む                          #
    # ------------------------------------------------------------------ #
    def test_format_markdown_list_with_due_date_includes_date_in_header(self):
        """
        Given: due_date="2026-03-03" を指定
        When:  _format_markdown_list を呼び出す
        Then:  ヘッダに「2026-03-03 期限」が含まれる
        """
        # Given
        tasks = [{"id": "1", "title": "タスク", "priority": "normal",
                  "due_date": "2026-03-03", "url": "http://localhost:8080/issues/1", "status": "新規"}]

        # When
        result = _format_markdown_list(tasks, due_date="2026-03-03")

        # Then
        assert "2026-03-03 期限" in result


@pytest.fixture
def sample_tasks() -> list[dict]:
    return [
        {
            "id": "123", "title": "設計書レビュー", "priority": "high",
            "due_date": "2026-03-03", "url": "http://localhost:8080/issues/123",
            "status": "新規", "description": "...", "project_id": 1,
            "project_name": "テスト", "created_at": "2026-02-20T09:00:00Z",
            "updated_at": "2026-03-01T14:30:00Z",
        },
        {
            "id": "124", "title": "API テスト実施", "priority": "normal",
            "due_date": "2026-03-03", "url": "http://localhost:8080/issues/124",
            "status": "新規", "description": None, "project_id": 1,
            "project_name": "テスト", "created_at": "2026-02-22T10:00:00Z",
            "updated_at": "2026-03-02T09:00:00Z",
        },
    ]
```

### 4.2 TaskSearchService テスト

```python
# tests/application/task/test_task_search_service.py
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.application.task.task_search_service import TaskSearchService, STATUS_MAP
from app.domain.exceptions import RedmineConnectionError


class TestTaskSearchServiceSearchTasks:
    """TaskSearchService.search_tasks の単体テスト。"""

    # ------------------------------------------------------------------ #
    # TC-010: status="open" → list_issues が status_id="open" で呼ばれる   #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_with_open_status_calls_adapter_with_correct_params(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: status="open" で検索
        When:  search_tasks を呼び出す
        Then:  RedmineAdapter.list_issues が status_id="open" で呼ばれる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = sample_redmine_issues_response

        # When
        result = await task_search_service.search_tasks(status="open")

        # Then
        assert len(result) == 3
        call_kwargs = mock_redmine_adapter.list_issues.call_args.kwargs
        assert call_kwargs["status_id"] == "open"

    # ------------------------------------------------------------------ #
    # TC-011: status="all" → status_id="*" でAdapterが呼ばれる             #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_with_all_status_maps_to_asterisk(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        empty_redmine_response: dict,
    ):
        """
        Given: status="all" で検索
        When:  search_tasks を呼び出す
        Then:  RedmineAdapter.list_issues が status_id="*" で呼ばれる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = empty_redmine_response

        # When
        await task_search_service.search_tasks(status="all")

        # Then
        call_kwargs = mock_redmine_adapter.list_issues.call_args.kwargs
        assert call_kwargs["status_id"] == "*"

    # ------------------------------------------------------------------ #
    # TC-012: status=None → デフォルト status_id="open" で呼ばれる          #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_with_no_status_defaults_to_open(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        empty_redmine_response: dict,
    ):
        """
        Given: status=None（フィルタなし）
        When:  search_tasks を呼び出す
        Then:  RedmineAdapter.list_issues が status_id="open" で呼ばれる（デフォルト）
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = empty_redmine_response

        # When
        await task_search_service.search_tasks(status=None)

        # Then
        call_kwargs = mock_redmine_adapter.list_issues.call_args.kwargs
        assert call_kwargs["status_id"] == "open"

    # ------------------------------------------------------------------ #
    # TC-013: due_date 指定あり → adapter に due_date が渡される             #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_with_due_date_passes_to_adapter(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: due_date="2026-03-03" を指定
        When:  search_tasks を呼び出す
        Then:  RedmineAdapter.list_issues が due_date="2026-03-03" で呼ばれる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = sample_redmine_issues_response

        # When
        await task_search_service.search_tasks(due_date="2026-03-03")

        # Then
        call_kwargs = mock_redmine_adapter.list_issues.call_args.kwargs
        assert call_kwargs["due_date"] == "2026-03-03"

    # ------------------------------------------------------------------ #
    # TC-014: keyword 指定あり → adapter に subject_like が渡される          #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_with_keyword_passes_subject_like_to_adapter(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        empty_redmine_response: dict,
    ):
        """
        Given: keyword="設計書" を指定
        When:  search_tasks を呼び出す
        Then:  RedmineAdapter.list_issues が subject_like="設計書" で呼ばれる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = empty_redmine_response

        # When
        await task_search_service.search_tasks(keyword="設計書")

        # Then
        call_kwargs = mock_redmine_adapter.list_issues.call_args.kwargs
        assert call_kwargs["subject_like"] == "設計書"

    # ------------------------------------------------------------------ #
    # TC-015: Redmine 接続エラー → RedmineConnectionError が伝播する         #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_when_connection_error_propagates_exception(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
    ):
        """
        Given: Redmine への接続に失敗する
        When:  search_tasks を呼び出す
        Then:  RedmineConnectionError が伝播する
        """
        # Given
        mock_redmine_adapter.list_issues.side_effect = RedmineConnectionError(
            "接続タイムアウト"
        )

        # When / Then
        with pytest.raises(RedmineConnectionError):
            await task_search_service.search_tasks(status="open")

    # ------------------------------------------------------------------ #
    # TC-016: 結果を内部形式に変換 → priority.id=3 が "high" に変換される    #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_converts_priority_id_to_name(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: Redmine レスポンスに priority.id=3 のタスクが含まれる
        When:  search_tasks を呼び出す
        Then:  変換後のタスクの priority が "high" になる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = sample_redmine_issues_response
        # sample_redmine_issues_response の 1 件目: priority.id=3（高）

        # When
        result = await task_search_service.search_tasks()

        # Then
        assert result[0]["priority"] == "high"

    # ------------------------------------------------------------------ #
    # TC-017: 結果の URL → "{REDMINE_URL}/issues/{id}" 形式              #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_search_tasks_generates_correct_url(
        self,
        mock_redmine_adapter: MagicMock,
        task_search_service: TaskSearchService,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: Redmine レスポンスに id=123 のタスクが含まれる
        When:  search_tasks を呼び出す
        Then:  変換後のタスクの url が 正しい形式になる
        """
        # Given
        mock_redmine_adapter.list_issues.return_value = sample_redmine_issues_response

        # When
        with pytest.MonkeyPatch.context() as mp:
            # Settings の redmine_url をモック
            import app.application.task.task_search_service as svc_module
            mock_settings = MagicMock()
            mock_settings.redmine_url = "http://localhost:8080"
            mp.setattr(svc_module, "get_settings", lambda: mock_settings)
            result = await task_search_service.search_tasks()

        # Then
        assert result[0]["url"] == "http://localhost:8080/issues/123"


class TestBuildRedmineParams:
    """TaskSearchService._build_redmine_params の単体テスト。"""

    # ------------------------------------------------------------------ #
    # TC-018: 全パラメータ指定 → すべてのパラメータが dict に含まれる          #
    # ------------------------------------------------------------------ #
    def test_build_redmine_params_with_all_params(
        self, task_search_service: TaskSearchService
    ):
        """
        Given: status, due_date, keyword, project_id, limit を全指定
        When:  _build_redmine_params を呼び出す
        Then:  すべてのパラメータが dict に含まれる
        """
        # When
        params = task_search_service._build_redmine_params(
            status="closed",
            due_date="2026-03-03",
            keyword="設計書",
            project_id=1,
            limit=50,
        )

        # Then
        assert params["status_id"] == "closed"
        assert params["due_date"] == "2026-03-03"
        assert params["subject_like"] == "設計書"
        assert params["project_id"] == 1
        assert params["limit"] == 50

    # ------------------------------------------------------------------ #
    # TC-019: limit=200 → 100 にクランプされる                               #
    # ------------------------------------------------------------------ #
    def test_build_redmine_params_clamps_limit_to_100(
        self, task_search_service: TaskSearchService
    ):
        """
        Given: limit=200（最大値超え）
        When:  _build_redmine_params を呼び出す
        Then:  params["limit"] が 100 になる
        """
        # When
        params = task_search_service._build_redmine_params(
            status=None, due_date=None, keyword=None, project_id=None, limit=200
        )

        # Then
        assert params["limit"] == 100

    # ------------------------------------------------------------------ #
    # TC-020: status="all" → status_id="*" に変換される                    #
    # ------------------------------------------------------------------ #
    @pytest.mark.parametrize("status_input,expected_status_id", [
        ("open", "open"),
        ("closed", "closed"),
        ("all", "*"),
    ])
    def test_build_redmine_params_status_mapping(
        self,
        task_search_service: TaskSearchService,
        status_input: str,
        expected_status_id: str,
    ):
        """
        Given: status が "open" / "closed" / "all" のいずれか
        When:  _build_redmine_params を呼び出す
        Then:  status_id が Redmine の正しい値に変換される
        """
        # When
        params = task_search_service._build_redmine_params(
            status=status_input, due_date=None, keyword=None, project_id=None, limit=25
        )

        # Then
        assert params["status_id"] == expected_status_id


### 4.3 RedmineAdapter.list_issues テスト

```python
# tests/infra/redmine/test_redmine_adapter_list.py
from __future__ import annotations

import pytest
import httpx
from pytest_httpx import HTTPXMock

from app.infra.redmine.redmine_adapter import RedmineAdapter
from app.domain.exceptions import (
    RedmineConnectionError,
    RedmineAuthError,
    RedmineNotFoundError,
    RedmineAPIError,
)

REDMINE_URL = "http://localhost:8080"
API_KEY = "test_api_key"


@pytest.fixture
def redmine_adapter() -> RedmineAdapter:
    return RedmineAdapter(base_url=REDMINE_URL, api_key=API_KEY)


class TestRedmineAdapterListIssues:
    """RedmineAdapter.list_issues の単体テスト（pytest-httpx を使用）。"""

    # ------------------------------------------------------------------ #
    # TC-021: 正常系 → 200 OK でチケット一覧が返る                           #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_returns_issues_on_success(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: Redmine が 200 OK と issues 配列を返す
        When:  list_issues を呼び出す
        Then:  issues 配列と total_count が返る
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=f"{REDMINE_URL}/issues.json",
            match_params={"status_id": "open", "limit": "25", "offset": "0"},
            json=sample_redmine_issues_response,
            status_code=200,
        )

        # When
        result = await redmine_adapter.list_issues(status_id="open", limit=25)

        # Then
        assert len(result["issues"]) == 3
        assert result["total_count"] == 3

    # ------------------------------------------------------------------ #
    # TC-022: due_date パラメータ → URL に含まれる                           #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_sends_due_date_in_query(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
        sample_redmine_issues_response: dict,
    ):
        """
        Given: due_date="2026-03-03" を指定
        When:  list_issues を呼び出す
        Then:  HTTP リクエストのクエリパラメータに due_date=2026-03-03 が含まれる
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=f"{REDMINE_URL}/issues.json",
            json=sample_redmine_issues_response,
            status_code=200,
        )

        # When
        await redmine_adapter.list_issues(due_date="2026-03-03")

        # Then
        request = httpx_mock.get_requests()[0]
        assert "due_date=2026-03-03" in str(request.url)

    # ------------------------------------------------------------------ #
    # TC-023: subject_like パラメータ → URL に subject=keyword が含まれる    #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_maps_subject_like_to_subject_param(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
        empty_redmine_response: dict,
    ):
        """
        Given: subject_like="設計書" を指定
        When:  list_issues を呼び出す
        Then:  HTTP リクエストのクエリパラメータに subject=設計書（URLエンコード済み）が含まれる
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=f"{REDMINE_URL}/issues.json",
            json=empty_redmine_response,
            status_code=200,
        )

        # When
        await redmine_adapter.list_issues(subject_like="設計書")

        # Then
        request = httpx_mock.get_requests()[0]
        assert "subject=" in str(request.url)

    # ------------------------------------------------------------------ #
    # TC-024: 401 Unauthorized → RedmineAuthError を上げる（リトライなし）   #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_raises_auth_error_on_401(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
    ):
        """
        Given: Redmine が 401 Unauthorized を返す
        When:  list_issues を呼び出す
        Then:  RedmineAuthError が発生する（リトライなし）
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=f"{REDMINE_URL}/issues.json",
            status_code=401,
        )

        # When / Then
        with pytest.raises(RedmineAuthError):
            await redmine_adapter.list_issues()

    # ------------------------------------------------------------------ #
    # TC-025: 404 Not Found → RedmineNotFoundError を上げる                 #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_raises_not_found_error_on_404(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
    ):
        """
        Given: Redmine が 404 Not Found を返す（存在しない project_id）
        When:  list_issues を呼び出す
        Then:  RedmineNotFoundError が発生する
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=f"{REDMINE_URL}/issues.json",
            status_code=404,
        )

        # When / Then
        with pytest.raises(RedmineNotFoundError):
            await redmine_adapter.list_issues(project_id=9999)

    # ------------------------------------------------------------------ #
    # TC-026: ConnectError × 3 回 → RedmineConnectionError（3リトライ後）   #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_raises_connection_error_after_3_retries(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
    ):
        """
        Given: Redmine が ConnectError を 3 回連続で発生させる
        When:  list_issues を呼び出す
        Then:  RedmineConnectionError が発生する（3 回リトライ後）
        """
        # Given: 3 回のリクエストすべてで ConnectError
        httpx_mock.add_exception(httpx.ConnectError("接続失敗"), is_reusable=True)

        # When / Then
        with pytest.raises(RedmineConnectionError):
            await redmine_adapter.list_issues()

    # ------------------------------------------------------------------ #
    # TC-027: API キーが X-Redmine-API-Key ヘッダに含まれる                   #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_sends_api_key_in_header(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
        empty_redmine_response: dict,
    ):
        """
        Given: API キーを設定した RedmineAdapter
        When:  list_issues を呼び出す
        Then:  HTTP リクエストヘッダに X-Redmine-API-Key が含まれる
        """
        # Given
        httpx_mock.add_response(
            method="GET",
            url=f"{REDMINE_URL}/issues.json",
            json=empty_redmine_response,
            status_code=200,
        )

        # When
        await redmine_adapter.list_issues()

        # Then
        request = httpx_mock.get_requests()[0]
        assert request.headers["X-Redmine-API-Key"] == API_KEY

    # ------------------------------------------------------------------ #
    # TC-028: 5xx エラー 3 回 → RedmineConnectionError（3リトライ後）         #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_list_issues_retries_on_500_error(
        self,
        redmine_adapter: RedmineAdapter,
        httpx_mock: HTTPXMock,
    ):
        """
        Given: Redmine が 500 Internal Server Error を 3 回連続で返す
        When:  list_issues を呼び出す
        Then:  RedmineConnectionError が発生する（3 回リトライ後）
        """
        # Given
        httpx_mock.add_response(status_code=500, is_reusable=True)

        # When / Then
        with pytest.raises(RedmineConnectionError):
            await redmine_adapter.list_issues()
```

### 4.4 GET /api/v1/tasks エンドポイントテスト

```python
# tests/api/v1/test_tasks_api.py
from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock, patch

from app.main import app


class TestGetTasksAPI:
    """GET /api/v1/tasks エンドポイントの単体テスト。"""

    # ------------------------------------------------------------------ #
    # TC-029: 正常系 → 200 OK でタスク一覧が返る                             #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_get_tasks_returns_200_with_task_list(self, sample_tasks_from_service):
        """
        Given: TaskSearchService が 2 件のタスクを返す
        When:  GET /api/v1/tasks にリクエストする
        Then:  200 OK でタスク一覧が返る
        """
        # Given
        with patch(
            "app.api.v1.tasks.RedmineAdapter"
        ) as MockAdapter, patch(
            "app.api.v1.tasks.get_settings"
        ) as mock_settings:
            mock_adapter_instance = MagicMock()
            mock_adapter_instance.list_issues = AsyncMock(
                return_value={
                    "issues": [
                        {"id": 123, "project": {"id": 1, "name": "テスト"},
                         "tracker": {"id": 1, "name": "バグ"},
                         "status": {"id": 1, "name": "新規"},
                         "priority": {"id": 3, "name": "高"},
                         "author": {"id": 1, "name": "Admin"},
                         "assigned_to": None,
                         "subject": "設計書レビュー", "description": "詳細",
                         "start_date": None, "due_date": "2026-03-03",
                         "done_ratio": 0, "is_private": False,
                         "estimated_hours": None,
                         "created_on": "2026-02-20T09:00:00Z",
                         "updated_on": "2026-03-01T14:30:00Z",
                         "closed_on": None},
                    ],
                    "total_count": 1,
                    "offset": 0,
                    "limit": 25,
                }
            )
            MockAdapter.return_value = mock_adapter_instance
            mock_settings.return_value.redmine_url = "http://localhost:8080"
            mock_settings.return_value.redmine_api_key = "test_key"

            # When
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/tasks?status=open")

        # Then
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "tasks" in data["data"]
        assert "pagination" in data["data"]
        assert len(data["data"]["tasks"]) == 1
        assert data["data"]["tasks"][0]["title"] == "設計書レビュー"

    # ------------------------------------------------------------------ #
    # TC-030: status=invalid → 422 Unprocessable Entity                   #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_get_tasks_invalid_status_returns_422(self):
        """
        Given: status に無効な値 "invalid" を指定
        When:  GET /api/v1/tasks にリクエストする
        Then:  422 または 400 でバリデーションエラーが返る
        """
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/tasks?status=invalid")

        assert response.status_code in (400, 422)

    # ------------------------------------------------------------------ #
    # TC-031: Redmine 接続エラー → 503 REDMINE_UNAVAILABLE                 #
    # ------------------------------------------------------------------ #
    @pytest.mark.asyncio
    async def test_get_tasks_redmine_error_returns_503(self):
        """
        Given: Redmine への接続に失敗する
        When:  GET /api/v1/tasks にリクエストする
        Then:  503 Service Unavailable が返る
        """
        from app.domain.exceptions import RedmineConnectionError

        with patch("app.api.v1.tasks.RedmineAdapter") as MockAdapter, patch(
            "app.api.v1.tasks.get_settings"
        ) as mock_settings:
            mock_adapter_instance = MagicMock()
            mock_adapter_instance.list_issues = AsyncMock(
                side_effect=RedmineConnectionError("接続失敗")
            )
            MockAdapter.return_value = mock_adapter_instance
            mock_settings.return_value.redmine_url = "http://localhost:8080"
            mock_settings.return_value.redmine_api_key = "test_key"

            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/tasks")

        assert response.status_code == 503
        assert response.json()["error"]["code"] == "REDMINE_UNAVAILABLE"
```

---

## 5. フロントエンド単体テスト設計

### 5.1 MarkdownContent コンポーネントテスト

```tsx
// src/components/chat/__tests__/MarkdownContent.test.tsx
import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MarkdownContent } from "../MarkdownContent";

describe("MarkdownContent", () => {
  // ------------------------------------------------------------------ //
  // TC-032: Redmine URL → target="_blank" で新しいタブで開く              //
  // ------------------------------------------------------------------ //
  it("renders Redmine issue URL as external link with target blank", () => {
    /**
     * Given: Redmine チケット URL を含む Markdown テキスト
     * When:  MarkdownContent をレンダリングする
     * Then:  <a target="_blank" rel="noopener noreferrer"> としてレンダリングされる
     */
    // Given
    const content = "[設計書レビュー](http://localhost:8080/issues/123)";

    // When
    render(<MarkdownContent content={content} />);

    // Then
    const link = screen.getByRole("link", { name: /設計書レビュー/ });
    expect(link).toHaveAttribute("href", "http://localhost:8080/issues/123");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
  });

  // ------------------------------------------------------------------ //
  // TC-033: **高** → <strong> タグで太字表示される                         //
  // ------------------------------------------------------------------ //
  it("renders bold text for high priority tasks", () => {
    /**
     * Given: **高** を含む Markdown テキスト
     * When:  MarkdownContent をレンダリングする
     * Then:  <strong> タグでレンダリングされる
     */
    // Given
    const content = "1. [タスク](http://localhost:8080/issues/1) - **高**";

    // When
    render(<MarkdownContent content={content} />);

    // Then
    const boldText = screen.getByText("高");
    expect(boldText.tagName).toBe("STRONG");
  });

  // ------------------------------------------------------------------ //
  // TC-034: ## ヘッダ → h2 タグでレンダリングされる                         //
  // ------------------------------------------------------------------ //
  it("renders h2 heading for task list header", () => {
    /**
     * Given: ## タスク一覧（3件）を含む Markdown テキスト
     * When:  MarkdownContent をレンダリングする
     * Then:  <h2> タグでレンダリングされる
     */
    // Given
    const content = "## タスク一覧（3件）";

    // When
    render(<MarkdownContent content={content} />);

    // Then
    const heading = screen.getByRole("heading", { level: 2 });
    expect(heading).toHaveTextContent("タスク一覧（3件）");
  });

  // ------------------------------------------------------------------ //
  // TC-035: isStreaming=true → カーソル要素が表示される                     //
  // ------------------------------------------------------------------ //
  it("shows streaming cursor when isStreaming is true", () => {
    /**
     * Given: isStreaming=true
     * When:  MarkdownContent をレンダリングする
     * Then:  animate-pulse のカーソル要素が表示される
     */
    // Given / When
    const { container } = render(
      <MarkdownContent content="テキスト" isStreaming={true} />
    );

    // Then
    const cursor = container.querySelector(".animate-pulse");
    expect(cursor).toBeInTheDocument();
  });

  // ------------------------------------------------------------------ //
  // TC-036: isStreaming=false → カーソル要素が表示されない                  //
  // ------------------------------------------------------------------ //
  it("does not show streaming cursor when isStreaming is false", () => {
    /**
     * Given: isStreaming=false（デフォルト）
     * When:  MarkdownContent をレンダリングする
     * Then:  animate-pulse のカーソル要素は表示されない
     */
    // Given / When
    const { container } = render(<MarkdownContent content="テキスト" />);

    // Then
    const cursor = container.querySelector(".animate-pulse");
    expect(cursor).not.toBeInTheDocument();
  });

  // ------------------------------------------------------------------ //
  // TC-037: 複数リンク → すべてのリンクが target="_blank" で表示される        //
  // ------------------------------------------------------------------ //
  it("renders multiple issue links all with target blank", () => {
    /**
     * Given: 3 件のタスク URL を含む Markdown テキスト
     * When:  MarkdownContent をレンダリングする
     * Then:  すべてのリンクが target="_blank" でレンダリングされる
     */
    // Given
    const content = `## タスク一覧（3件）

1. [タスクA](http://localhost:8080/issues/1) - **高**
2. [タスクB](http://localhost:8080/issues/2) - 通常
3. [タスクC](http://localhost:8080/issues/3) - 低`;

    // When
    render(<MarkdownContent content={content} />);

    // Then
    const links = screen.getAllByRole("link");
    expect(links).toHaveLength(3);
    links.forEach((link) => {
      expect(link).toHaveAttribute("target", "_blank");
    });
  });
});
```

### 5.2 AgentStatusBar コンポーネントテスト（FEAT-002 追加分）

```tsx
// src/components/chat/__tests__/AgentStatusBar.test.tsx（FEAT-002 追加テスト）
import React from "react";
import { render, screen } from "@testing-library/react";
import { AgentStatusBar } from "../AgentStatusBar";

describe("AgentStatusBar - FEAT-002", () => {
  // ------------------------------------------------------------------ //
  // TC-038: tool_calling + search_tasks → 「タスク検索」バッジが表示される   //
  // ------------------------------------------------------------------ //
  it("shows task search badge when search_tasks tool is called", () => {
    /**
     * Given: status="tool_calling", toolName="search_tasks"
     * When:  AgentStatusBar をレンダリングする
     * Then:  「タスク検索」バッジと「Redmine からタスクを検索しています」が表示される
     */
    // Given / When
    render(
      <AgentStatusBar
        status="tool_calling"
        currentToolCall={{ toolName: "search_tasks", status: "running" }}
      />
    );

    // Then
    expect(screen.getByText("タスク検索")).toBeInTheDocument();
    expect(
      screen.getByText(/Redmine からタスクを検索しています/)
    ).toBeInTheDocument();
  });

  // ------------------------------------------------------------------ //
  // TC-039: status="idle" → 何も表示されない                               //
  // ------------------------------------------------------------------ //
  it("renders nothing when status is idle", () => {
    /**
     * Given: status="idle"
     * When:  AgentStatusBar をレンダリングする
     * Then:  コンポーネントが null を返す（何も表示されない）
     */
    // Given / When
    const { container } = render(
      <AgentStatusBar status="idle" currentToolCall={null} />
    );

    // Then
    expect(container).toBeEmptyDOMElement();
  });
});
```

### 5.3 useChat フック SSE ハンドラテスト（FEAT-002 追加分）

```tsx
// src/hooks/__tests__/useChat.test.ts（FEAT-002 追加テスト）
import { renderHook, act, waitFor } from "@testing-library/react";
import { useChat } from "../useChat";
import { server } from "../../mocks/server";  // MSW サーバー
import { http, HttpResponse } from "msw";

describe("useChat - FEAT-002 search_tasks tool", () => {
  // ------------------------------------------------------------------ //
  // TC-040: SSE で tool_call search_tasks → agentStatus が tool_calling  //
  // ------------------------------------------------------------------ //
  it("sets agentStatus to tool_calling when search_tasks tool_call event received", async () => {
    /**
     * Given: SSE ストリームが tool_call search_tasks イベントを送信する
     * When:  sendMessage を呼び出す
     * Then:  agentStatus が "tool_calling" になる
     */
    // Given: MSW でフェイク SSE レスポンスを設定
    server.use(
      http.post(
        "/api/v1/conversations/:id/messages",
        () => {
          const stream = new ReadableStream({
            start(controller) {
              const enc = new TextEncoder();
              controller.enqueue(
                enc.encode(
                  'event: tool_call\ndata: {"type":"tool_call","tool_name":"search_tasks","tool_call_id":"call_001","input":{"status":"open"}}\n\n'
                )
              );
              controller.close();
            },
          });
          return new HttpResponse(stream, {
            headers: { "Content-Type": "text/event-stream" },
          });
        }
      )
    );

    // When
    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("未完了タスク一覧を見せて");
    });

    // Then
    await waitFor(() => {
      expect(result.current.state.currentToolCall?.toolName).toBe("search_tasks");
    });
  });

  // ------------------------------------------------------------------ //
  // TC-041: SSE で tool_result → agentStatus が generating に遷移する     //
  // ------------------------------------------------------------------ //
  it("sets agentStatus to generating after tool_result event", async () => {
    /**
     * Given: SSE ストリームが tool_call → tool_result イベントを送信する
     * When:  sendMessage を呼び出す
     * Then:  tool_result 受信後に agentStatus が "generating" になる
     */
    // Given
    server.use(
      http.post(
        "/api/v1/conversations/:id/messages",
        () => {
          const stream = new ReadableStream({
            start(controller) {
              const enc = new TextEncoder();
              controller.enqueue(
                enc.encode(
                  'event: tool_call\ndata: {"type":"tool_call","tool_name":"search_tasks","tool_call_id":"call_001","input":{}}\n\n'
                )
              );
              controller.enqueue(
                enc.encode(
                  'event: tool_result\ndata: {"type":"tool_result","tool_call_id":"call_001","output":"## タスク一覧（0件）","status":"success"}\n\n'
                )
              );
              controller.close();
            },
          });
          return new HttpResponse(stream, {
            headers: { "Content-Type": "text/event-stream" },
          });
        }
      )
    );

    // When
    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("タスク一覧");
    });

    // Then
    await waitFor(() => {
      expect(result.current.state.agentStatus).toBe("generating");
    });
  });

  // ------------------------------------------------------------------ //
  // TC-042: content_delta → メッセージ内容が逐次更新される（Markdown含む）  //
  // ------------------------------------------------------------------ //
  it("appends content_delta to message content progressively", async () => {
    /**
     * Given: SSE ストリームが 3 回の content_delta を送信する（Markdown テキスト）
     * When:  sendMessage を呼び出す
     * Then:  メッセージの content が 3 回分連結された文字列になる
     */
    // Given
    server.use(
      http.post(
        "/api/v1/conversations/:id/messages",
        () => {
          const stream = new ReadableStream({
            start(controller) {
              const enc = new TextEncoder();
              const events = [
                'event: message_start\ndata: {"type":"message_start","message_id":"msg_001"}\n\n',
                'event: content_delta\ndata: {"type":"content_delta","delta":"## タスク一覧（3件）\\n\\n","message_id":"msg_001"}\n\n',
                'event: content_delta\ndata: {"type":"content_delta","delta":"1. [設計書レビュー](http://localhost:8080/issues/123)","message_id":"msg_001"}\n\n',
                'event: content_delta\ndata: {"type":"content_delta","delta":" - **高**\\n","message_id":"msg_001"}\n\n',
                'event: message_end\ndata: {"type":"message_end","message_id":"msg_001","finish_reason":"end_turn"}\n\n',
              ];
              events.forEach((event) => controller.enqueue(enc.encode(event)));
              controller.close();
            },
          });
          return new HttpResponse(stream, {
            headers: { "Content-Type": "text/event-stream" },
          });
        }
      )
    );

    // When
    const { result } = renderHook(() => useChat());
    await act(async () => {
      await result.current.sendMessage("今日のタスクは？");
    });

    // Then
    await waitFor(() => {
      const assistantMessages = result.current.state.messages.filter(
        (m) => m.role === "assistant"
      );
      expect(assistantMessages.length).toBeGreaterThan(0);
      const content = assistantMessages[assistantMessages.length - 1].content;
      expect(content).toContain("## タスク一覧（3件）");
      expect(content).toContain("設計書レビュー");
      expect(content).toContain("**高**");
    });
  });
});
```

---

## 6. カバレッジ目標

### 6.1 バックエンド

| モジュール | カバレッジ目標 | 備考 |
|---|---|---|
| `app/agent/tools/search_tasks_tool.py` | 85%以上 | ツール関数・フォーマット関数 |
| `app/application/task/task_search_service.py` | 90%以上 | パラメータ変換・ACL 変換 |
| `app/infra/redmine/redmine_adapter.py` | 85%以上 | `list_issues` + リトライロジック |
| `app/api/v1/tasks.py` | 80%以上 | エンドポイント・エラーハンドリング |
| **全体** | **80%以上** | `pytest-cov` で計測 |

### 6.2 フロントエンド

| コンポーネント/フック | カバレッジ目標 | 備考 |
|---|---|---|
| `MarkdownContent.tsx` | 85%以上 | リンク・太字・ヘッダのレンダリング |
| `AgentStatusBar.tsx` | 80%以上 | search_tasks バッジ |
| `useChat.ts`（SSE 部分） | 80%以上 | tool_call・content_delta ハンドラ |
| **全体** | **80%以上** | Jest + `@testing-library/react` |

---

## 7. テスト実行コマンド

### 7.1 バックエンド

```bash
# 全テスト実行
cd backend
pytest

# カバレッジレポート付き
pytest --cov=app --cov-report=term-missing --cov-report=html

# FEAT-002 関連のみ実行
pytest tests/agent/tools/test_search_tasks_tool.py \
       tests/application/task/test_task_search_service.py \
       tests/infra/redmine/test_redmine_adapter_list.py \
       tests/api/v1/test_tasks_api.py \
       -v

# 特定テストクラスのみ実行
pytest tests/application/task/test_task_search_service.py::TestTaskSearchServiceSearchTasks -v

# マーカー指定実行
pytest -m unit -v
```

### 7.2 フロントエンド

```bash
# 全テスト実行
cd frontend
npm test

# ウォッチモード
npm test -- --watch

# FEAT-002 関連のみ実行
npm test -- --testPathPattern="MarkdownContent|AgentStatusBar|useChat"

# カバレッジレポート
npm test -- --coverage --coverageDirectory=coverage

# 特定テストファイルのみ
npm test src/components/chat/__tests__/MarkdownContent.test.tsx
```

### 7.3 TDD サイクルの実行順序

```bash
# Red フェーズ: テスト失敗を確認
pytest tests/application/task/test_task_search_service.py -v
# → FAILED (ImportError または AssertionError)

# Green フェーズ: 実装後にテスト成功を確認
# app/application/task/task_search_service.py を実装する
pytest tests/application/task/test_task_search_service.py -v
# → PASSED

# Refactor フェーズ: コード整理後にすべてのテストがパスすることを確認
pytest -v
# → PASSED (全テスト)
```
