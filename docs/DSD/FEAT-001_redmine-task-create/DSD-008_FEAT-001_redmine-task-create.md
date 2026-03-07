# DSD-008_FEAT-001 単体テスト設計書（Redmineタスク作成）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-008_FEAT-001 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-001 |
| 機能名 | Redmineタスク作成（redmine-task-create） |
| 入力元 | DSD-001_FEAT-001, DSD-002_FEAT-001, DSD-003_FEAT-001, DSD-005_FEAT-001 |
| ステータス | 初版 |

---

## 目次

1. テスト設計方針
2. テスト対象一覧
3. テストモジュール詳細設計
   - create_task_tool 関数
   - TaskCreateService クラス
   - RedmineAdapter.create_issue メソッド
   - MessageBubble コンポーネント（フロントエンド）
   - MessageInput コンポーネント（フロントエンド）
   - useChat カスタムフック（フロントエンド）
4. テストフィクスチャ設計
5. モック設計
6. カバレッジ目標
7. テスト実行方法

---

## 1. テスト設計方針

### 1.1 TDD アプローチ

本設計書は TDD（テスト駆動開発）の「Red → Green → Refactor」サイクルを駆動する起点として機能する。

1. **Red フェーズ**: 本設計書のテストケースを先にコードとして記述し、失敗することを確認する
2. **Green フェーズ**: テストが通過する最小限の実装を行う
3. **Refactor フェーズ**: コードを整理・最適化する（テストは引き続き通過することを確認）

### 1.2 テストレベル

| テストレベル | ツール | 対象 |
|---|---|---|
| バックエンド単体テスト | pytest + pytest-asyncio + unittest.mock | サービス・アダプター・ツール関数 |
| フロントエンド単体テスト | Jest + React Testing Library | コンポーネント・カスタムフック |

### 1.3 モック方針

| 対象 | モック化 | 理由 |
|---|---|---|
| Redmine REST API | モック化 | 外部依存を排除し、ネットワーク不要でテストを実行する |
| Claude API | モック化 | 外部依存を排除し、コストなしでテストを実行する |
| PostgreSQL DB | テスト用 DB または モック化 | 単体テストではモック化し、結合テストでテスト DB を使用する |
| MCP Client | モック化 | RedmineAdapter の内部実装を直接テストする |

### 1.4 Given-When-Then パターン

すべてのテストケースは以下の Given-When-Then 形式で記述する:
- **Given**: テストの前提条件（入力データ・モックの設定）
- **When**: テスト対象の処理を実行する
- **Then**: 期待する結果を検証する

---

## 2. テスト対象一覧

| テスト対象 | ファイルパス | テストファイルパス | 優先度 |
|---|---|---|---|
| `create_task_tool` 関数 | `app/agent/tools/create_task_tool.py` | `tests/unit/test_create_task_tool.py` | 高 |
| `TaskCreateService.create_task` | `app/application/task/task_create_service.py` | `tests/unit/test_task_create_service.py` | 高 |
| `RedmineAdapter.create_issue` | `app/infra/redmine/redmine_adapter.py` | `tests/unit/test_redmine_adapter.py` | 高 |
| `TaskStatus` 値オブジェクト | `app/domain/task/task_status.py` | `tests/unit/test_task_status.py` | 中 |
| `TaskPriority` 値オブジェクト | `app/domain/task/task_priority.py` | `tests/unit/test_task_priority.py` | 中 |
| `MessageBubble` コンポーネント | `src/components/chat/MessageBubble.tsx` | `src/components/chat/__tests__/MessageBubble.test.tsx` | 高 |
| `MessageInput` コンポーネント | `src/components/chat/MessageInput.tsx` | `src/components/chat/__tests__/MessageInput.test.tsx` | 高 |
| `useChat` カスタムフック | `src/hooks/useChat.ts` | `src/hooks/__tests__/useChat.test.ts` | 高 |

---

## 3. テストモジュール詳細設計

---

### 3.1 create_task_tool 関数テスト

**テストファイル**: `tests/unit/test_create_task_tool.py`

**テスト対象関数のシグネチャ:**
```python
async def create_task_tool(
    title: str,
    description: str = "",
    priority: str = "normal",
    due_date: str = "",
    project_id: int = 1,
) -> str
```

#### TC-001: タスク作成成功（最小限の入力）

```python
@pytest.mark.asyncio
async def test_create_task_tool_with_title_only_returns_success_message(
    mock_task_create_service: AsyncMock,
) -> None:
    """
    Given: タイトルのみ指定（他はデフォルト値）
    When: create_task_tool を呼び出す
    Then: 成功メッセージ（タスク ID・URL 含む）が返る
    """
    # Given
    mock_task_create_service.create_task.return_value = {
        "id": "124",
        "title": "設計書レビュー",
        "status": "新規",
        "priority": "通常",
        "due_date": None,
        "project_id": 1,
        "url": "http://localhost:8080/issues/124",
        "created_at": "2026-03-03T10:00:00Z",
    }

    # When
    result = await create_task_tool(title="設計書レビュー")

    # Then
    assert "タスクを作成しました" in result
    assert "124" in result
    assert "http://localhost:8080/issues/124" in result
```

#### TC-002: タスク作成成功（全パラメータ指定）

```python
@pytest.mark.asyncio
async def test_create_task_tool_with_all_params_returns_success_message(
    mock_task_create_service: AsyncMock,
) -> None:
    """
    Given: タイトル・説明・優先度・期日・プロジェクト ID をすべて指定
    When: create_task_tool を呼び出す
    Then: 成功メッセージに期日情報が含まれる
    """
    # Given
    mock_task_create_service.create_task.return_value = {
        "id": "125",
        "title": "API 設計レビュー",
        "status": "新規",
        "priority": "高",
        "due_date": "2026-03-31",
        "project_id": 1,
        "url": "http://localhost:8080/issues/125",
        "created_at": "2026-03-03T10:00:00Z",
    }

    # When
    result = await create_task_tool(
        title="API 設計レビュー",
        description="DSD-003 の API 詳細設計書をレビューする",
        priority="high",
        due_date="2026-03-31",
        project_id=1,
    )

    # Then
    assert "タスクを作成しました" in result
    assert "125" in result
    assert "2026-03-31" in result
    assert "高" in result
```

#### TC-003: Redmine 接続失敗時のエラーメッセージ

```python
@pytest.mark.asyncio
async def test_create_task_tool_when_redmine_unavailable_returns_error_message(
    mock_task_create_service: AsyncMock,
) -> None:
    """
    Given: Redmine が接続不可（RedmineConnectionError が発生する）
    When: create_task_tool を呼び出す
    Then: エラーメッセージ文字列が返る（例外は発生しない）
    """
    # Given
    mock_task_create_service.create_task.side_effect = RedmineConnectionError(
        "Redmine への接続に失敗しました"
    )

    # When
    result = await create_task_tool(title="テストタスク")

    # Then
    assert "失敗" in result
    assert "エラー" in result
    # 例外が発生しないことを確認（ツール関数はエラーを文字列で返す）
```

#### TC-004: TaskCreateService の呼び出しパラメータ検証

```python
@pytest.mark.asyncio
async def test_create_task_tool_passes_correct_params_to_service(
    mock_task_create_service: AsyncMock,
) -> None:
    """
    Given: 特定のパラメータで create_task_tool を呼び出す
    When: create_task_tool を呼び出す
    Then: TaskCreateService.create_task が正しいパラメータで呼ばれる
    """
    # Given
    mock_task_create_service.create_task.return_value = {
        "id": "126", "title": "テスト", "status": "新規",
        "priority": "高", "due_date": None, "project_id": 2,
        "url": "http://localhost:8080/issues/126", "created_at": "2026-03-03T10:00:00Z",
    }

    # When
    await create_task_tool(
        title="テスト",
        priority="high",
        project_id=2,
    )

    # Then
    mock_task_create_service.create_task.assert_called_once_with(
        title="テスト",
        description=None,  # 空文字列は None に変換される
        priority="high",
        due_date=None,     # 空文字列は None に変換される
        project_id=2,
    )
```

---

### 3.2 TaskCreateService テスト

**テストファイル**: `tests/unit/test_task_create_service.py`

#### TC-005: タスク作成成功（正常系）

```python
@pytest.mark.asyncio
async def test_create_task_success(
    mock_redmine_adapter: AsyncMock,
    task_create_service: TaskCreateService,
) -> None:
    """
    Given: 有効なタスク作成パラメータと Redmine アダプターのモック
    When: create_task を呼び出す
    Then: タスクが作成され、正しいデータが返る
    """
    # Given
    title = "設計書レビュー"
    project_id = 1
    mock_redmine_adapter.create_issue.return_value = {
        "issue": {
            "id": 124,
            "subject": title,
            "status": {"id": 1, "name": "新規"},
            "priority": {"id": 2, "name": "通常"},
            "due_date": None,
            "created_on": "2026-03-03T10:00:00Z",
        }
    }

    # When
    result = await task_create_service.create_task(
        title=title,
        project_id=project_id,
    )

    # Then
    assert result["id"] == "124"
    assert result["title"] == title
    assert "url" in result
    assert "124" in result["url"]
    mock_redmine_adapter.create_issue.assert_called_once()
```

#### TC-006: タイトル空文字列でバリデーションエラー

```python
@pytest.mark.asyncio
async def test_create_task_with_empty_title_raises_validation_error(
    task_create_service: TaskCreateService,
) -> None:
    """
    Given: 空文字列のタイトル
    When: create_task を呼び出す
    Then: TaskValidationError が発生する（field="title"）
    """
    # When / Then
    with pytest.raises(TaskValidationError) as exc_info:
        await task_create_service.create_task(title="")

    assert exc_info.value.field == "title"
    assert "必須" in exc_info.value.message
```

#### TC-007: タイトル 201 文字でバリデーションエラー

```python
@pytest.mark.asyncio
async def test_create_task_with_title_exceeding_max_length_raises_validation_error(
    task_create_service: TaskCreateService,
) -> None:
    """
    Given: 201 文字のタイトル（最大 200 文字を超過）
    When: create_task を呼び出す
    Then: TaskValidationError が発生する
    """
    # Given
    long_title = "あ" * 201  # 201文字（制限超過）

    # When / Then
    with pytest.raises(TaskValidationError) as exc_info:
        await task_create_service.create_task(title=long_title)

    assert exc_info.value.field == "title"
    assert "200文字" in exc_info.value.message
```

#### TC-008: 不正な優先度でバリデーションエラー

```python
@pytest.mark.asyncio
async def test_create_task_with_invalid_priority_raises_validation_error(
    task_create_service: TaskCreateService,
) -> None:
    """
    Given: 有効でない優先度文字列（"critical"）
    When: create_task を呼び出す
    Then: TaskValidationError が発生する（field="priority"）
    """
    # When / Then
    with pytest.raises(TaskValidationError) as exc_info:
        await task_create_service.create_task(
            title="テストタスク",
            priority="critical",  # 無効な優先度
        )

    assert exc_info.value.field == "priority"
```

#### TC-009: Redmine 接続失敗で RedmineConnectionError が伝播

```python
@pytest.mark.asyncio
async def test_create_task_when_redmine_unavailable_raises_connection_error(
    mock_redmine_adapter: AsyncMock,
    task_create_service: TaskCreateService,
) -> None:
    """
    Given: Redmine アダプターが RedmineConnectionError を発生させる
    When: create_task を呼び出す
    Then: RedmineConnectionError が呼び出し元に伝播する
    """
    # Given
    mock_redmine_adapter.create_issue.side_effect = RedmineConnectionError()

    # When / Then
    with pytest.raises(RedmineConnectionError):
        await task_create_service.create_task(title="テストタスク")
```

#### TC-010: 存在しないプロジェクト ID で RedmineNotFoundError が伝播

```python
@pytest.mark.asyncio
async def test_create_task_with_nonexistent_project_raises_not_found_error(
    mock_redmine_adapter: AsyncMock,
    task_create_service: TaskCreateService,
) -> None:
    """
    Given: 存在しないプロジェクト ID（9999）を指定
    When: create_task を呼び出す
    Then: RedmineNotFoundError が発生する
    """
    # Given
    mock_redmine_adapter.create_issue.side_effect = RedmineNotFoundError(
        "プロジェクト ID 9999 が見つかりません"
    )

    # When / Then
    with pytest.raises(RedmineNotFoundError):
        await task_create_service.create_task(
            title="テストタスク",
            project_id=9999,
        )
```

#### TC-011: 優先度名称を ID に正しく変換する

```python
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "priority_name, expected_priority_id",
    [
        ("low", 1),
        ("normal", 2),
        ("high", 3),
        ("urgent", 4),
    ],
)
async def test_create_task_converts_priority_name_to_id(
    priority_name: str,
    expected_priority_id: int,
    mock_redmine_adapter: AsyncMock,
    task_create_service: TaskCreateService,
) -> None:
    """
    Given: 優先度名称文字列
    When: create_task を呼び出す
    Then: RedmineAdapter が正しい優先度 ID で呼ばれる
    """
    # Given
    mock_redmine_adapter.create_issue.return_value = {
        "issue": {
            "id": 124, "subject": "テスト",
            "status": {"id": 1, "name": "新規"},
            "priority": {"id": expected_priority_id, "name": ""},
            "due_date": None, "created_on": "2026-03-03T10:00:00Z",
        }
    }

    # When
    await task_create_service.create_task(
        title="テスト",
        priority=priority_name,
    )

    # Then
    mock_redmine_adapter.create_issue.assert_called_once()
    call_kwargs = mock_redmine_adapter.create_issue.call_args.kwargs
    assert call_kwargs["priority_id"] == expected_priority_id
```

---

### 3.3 RedmineAdapter テスト

**テストファイル**: `tests/unit/test_redmine_adapter.py`

#### TC-012: タスク作成成功（正常系）

```python
@pytest.mark.asyncio
async def test_create_issue_success(
    redmine_adapter: RedmineAdapter,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """
    Given: 正常な Redmine API レスポンス（201 Created）
    When: create_issue を呼び出す
    Then: Issue 情報の辞書が返る
    """
    # Given: Redmine API のレスポンスをモック化
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/issues.json",
        status_code=201,
        json={
            "issue": {
                "id": 124,
                "subject": "設計書レビュー",
                "status": {"id": 1, "name": "新規"},
                "priority": {"id": 3, "name": "高"},
                "due_date": "2026-03-31",
                "created_on": "2026-03-03T10:00:00Z",
            }
        },
    )

    # When
    result = await redmine_adapter.create_issue(
        subject="設計書レビュー",
        project_id=1,
        priority_id=3,
        due_date="2026-03-31",
    )

    # Then
    assert result["issue"]["id"] == 124
    assert result["issue"]["subject"] == "設計書レビュー"
```

#### TC-013: 接続タイムアウトで最大 3 回リトライして RedmineConnectionError

```python
@pytest.mark.asyncio
async def test_create_issue_connection_timeout_retries_three_times_then_raises(
    redmine_adapter: RedmineAdapter,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """
    Given: Redmine への接続が毎回タイムアウトする
    When: create_issue を呼び出す
    Then: 3 回リトライ後に RedmineConnectionError が発生する
    """
    # Given: 全リクエストでタイムアウトを発生させる
    httpx_mock.add_exception(httpx.ConnectTimeout("Connection timed out"))
    httpx_mock.add_exception(httpx.ConnectTimeout("Connection timed out"))
    httpx_mock.add_exception(httpx.ConnectTimeout("Connection timed out"))

    # When / Then
    with pytest.raises(RedmineConnectionError) as exc_info:
        await redmine_adapter.create_issue(
            subject="テストタスク",
            project_id=1,
        )

    assert "接続" in exc_info.value.message
    # 3 回リトライされたことを確認
    assert len(httpx_mock.get_requests()) == 3
```

#### TC-014: HTTP 401 で RedmineAuthError（リトライなし）

```python
@pytest.mark.asyncio
async def test_create_issue_with_invalid_api_key_raises_auth_error(
    redmine_adapter: RedmineAdapter,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """
    Given: API キーが無効（Redmine が 401 Unauthorized を返す）
    When: create_issue を呼び出す
    Then: RedmineAuthError が発生する（リトライなし）
    """
    # Given
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/issues.json",
        status_code=401,
    )

    # When / Then
    with pytest.raises(RedmineAuthError):
        await redmine_adapter.create_issue(
            subject="テストタスク",
            project_id=1,
        )

    # リトライしていないことを確認（リクエストは 1 回のみ）
    assert len(httpx_mock.get_requests()) == 1
```

#### TC-015: HTTP 422 で Redmine エラーメッセージを含む RedmineAPIError

```python
@pytest.mark.asyncio
async def test_create_issue_with_invalid_project_raises_api_error_with_message(
    redmine_adapter: RedmineAdapter,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """
    Given: 存在しないプロジェクト ID を指定（Redmine が 422 を返す）
    When: create_issue を呼び出す
    Then: Redmine のエラーメッセージを含む RedmineAPIError が発生する
    """
    # Given
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/issues.json",
        status_code=422,
        json={"errors": ["プロジェクトを入力してください"]},
    )

    # When / Then
    with pytest.raises(RedmineAPIError) as exc_info:
        await redmine_adapter.create_issue(
            subject="テストタスク",
            project_id=99999,
        )

    assert "プロジェクト" in exc_info.value.message
```

#### TC-016: HTTP 503 で 3 回リトライして RedmineAPIError

```python
@pytest.mark.asyncio
async def test_create_issue_server_error_retries_three_times(
    redmine_adapter: RedmineAdapter,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """
    Given: Redmine が 503 Service Unavailable を返し続ける
    When: create_issue を呼び出す
    Then: 3 回リトライ後に RedmineAPIError が発生する
    """
    # Given: 3 回すべて 503 を返す
    for _ in range(3):
        httpx_mock.add_response(
            method="POST",
            url="http://localhost:8080/issues.json",
            status_code=503,
        )

    # When / Then
    with pytest.raises(RedmineAPIError):
        await redmine_adapter.create_issue(
            subject="テストタスク",
            project_id=1,
        )

    assert len(httpx_mock.get_requests()) == 3
```

#### TC-017: リクエストに X-Redmine-API-Key ヘッダーが含まれる

```python
@pytest.mark.asyncio
async def test_create_issue_includes_api_key_header(
    redmine_adapter: RedmineAdapter,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    """
    Given: RedmineAdapter が初期化されている
    When: create_issue を呼び出す
    Then: X-Redmine-API-Key ヘッダーがリクエストに含まれる
    """
    # Given
    httpx_mock.add_response(
        method="POST",
        url="http://localhost:8080/issues.json",
        status_code=201,
        json={"issue": {"id": 124, "subject": "テスト", "status": {"id": 1, "name": "新規"},
                       "priority": {"id": 2, "name": "通常"}, "due_date": None,
                       "created_on": "2026-03-03T10:00:00Z"}},
    )

    # When
    await redmine_adapter.create_issue(subject="テスト", project_id=1)

    # Then
    requests = httpx_mock.get_requests()
    assert len(requests) == 1
    assert "X-Redmine-API-Key" in requests[0].headers
    # APIキーの値はログに含めないため、値の検証のみ
    assert requests[0].headers["X-Redmine-API-Key"] == "test-api-key"
```

---

### 3.4 MessageBubble コンポーネントテスト（フロントエンド）

**テストファイル**: `src/components/chat/__tests__/MessageBubble.test.tsx`

#### TC-018: ユーザーメッセージが右側に表示される

```tsx
describe("MessageBubble", () => {
  it("ユーザーメッセージが右側に表示されること（TC-018）", () => {
    // Given
    const message = {
      id: "1",
      role: "user" as const,
      content: "タスクを作成してください",
      createdAt: "2026-03-03T10:00:00Z",
    };

    // When
    render(<MessageBubble message={message} />);

    // Then
    const listItem = screen.getByRole("listitem");
    expect(listItem).toHaveClass("justify-end");
    expect(screen.getByText("タスクを作成してください")).toBeInTheDocument();
  });
```

#### TC-019: エージェントメッセージが左側に表示される

```tsx
  it("エージェントメッセージが左側に表示されること（TC-019）", () => {
    // Given
    const message = {
      id: "2",
      role: "assistant" as const,
      content: "タスクを作成しました。",
      createdAt: "2026-03-03T10:00:01Z",
    };

    // When
    render(<MessageBubble message={message} />);

    // Then
    const listItem = screen.getByRole("listitem");
    expect(listItem).toHaveClass("justify-start");
    expect(screen.getByText("タスクを作成しました。")).toBeInTheDocument();
  });
```

#### TC-020: ストリーミング中はカーソルアニメーションが表示される

```tsx
  it("isStreaming=true のときカーソルアニメーションが表示されること（TC-020）", () => {
    // Given
    const message = {
      id: "3",
      role: "assistant" as const,
      content: "処理中",
      createdAt: "2026-03-03T10:00:01Z",
    };

    // When
    render(<MessageBubble message={message} isStreaming={true} />);

    // Then
    const cursor = document.querySelector(".animate-pulse");
    expect(cursor).toBeInTheDocument();
  });

  it("isStreaming=false のときカーソルアニメーションが表示されないこと（TC-020b）", () => {
    // Given
    const message = {
      id: "4",
      role: "assistant" as const,
      content: "完了しました",
      createdAt: "2026-03-03T10:00:02Z",
    };

    // When
    render(<MessageBubble message={message} isStreaming={false} />);

    // Then
    const cursor = document.querySelector(".animate-pulse");
    expect(cursor).not.toBeInTheDocument();
  });
});
```

---

### 3.5 MessageInput コンポーネントテスト（フロントエンド）

**テストファイル**: `src/components/chat/__tests__/MessageInput.test.tsx`

#### TC-021: テキスト入力後 Enter キーで onSend が呼ばれる

```tsx
describe("MessageInput", () => {
  it("Enter キーでメッセージが送信されること（TC-021）", async () => {
    // Given
    const mockOnSend = jest.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();

    render(<MessageInput onSend={mockOnSend} />);
    const textarea = screen.getByRole("textbox", { name: "メッセージ入力欄" });

    // When
    await user.type(textarea, "タスクを作成して");
    await user.keyboard("{Enter}");

    // Then
    expect(mockOnSend).toHaveBeenCalledWith("タスクを作成して");
  });
```

#### TC-022: Shift+Enter は改行（送信しない）

```tsx
  it("Shift+Enter では送信されず改行されること（TC-022）", async () => {
    // Given
    const mockOnSend = jest.fn();
    const user = userEvent.setup();

    render(<MessageInput onSend={mockOnSend} />);
    const textarea = screen.getByRole("textbox", { name: "メッセージ入力欄" });

    // When
    await user.type(textarea, "1行目");
    await user.keyboard("{Shift>}{Enter}{/Shift}");
    await user.type(textarea, "2行目");

    // Then
    expect(mockOnSend).not.toHaveBeenCalled();
    expect(textarea).toHaveValue("1行目\n2行目");
  });
```

#### TC-023: disabled=true のとき送信ボタンが無効化される

```tsx
  it("disabled=true のとき送信ボタンが無効化されること（TC-023）", () => {
    // Given / When
    render(<MessageInput onSend={jest.fn()} disabled={true} />);

    // Then
    const sendButton = screen.getByRole("button", { name: "メッセージを送信" });
    expect(sendButton).toBeDisabled();
  });
```

#### TC-024: 空白のみのメッセージは送信されない

```tsx
  it("空白のみのメッセージは送信されないこと（TC-024）", async () => {
    // Given
    const mockOnSend = jest.fn();
    const user = userEvent.setup();

    render(<MessageInput onSend={mockOnSend} />);
    const textarea = screen.getByRole("textbox", { name: "メッセージ入力欄" });

    // When
    await user.type(textarea, "   ");
    await user.keyboard("{Enter}");

    // Then
    expect(mockOnSend).not.toHaveBeenCalled();
  });
});
```

---

### 3.6 useChat カスタムフックテスト（フロントエンド）

**テストファイル**: `src/hooks/__tests__/useChat.test.ts`

#### TC-025: sendMessage でユーザーメッセージがリストに追加される

```typescript
describe("useChat", () => {
  it("sendMessage 呼び出しでユーザーメッセージが追加されること（TC-025）", async () => {
    // Given
    const mockFetch = jest.fn().mockResolvedValue(
      new Response(
        'data: {"type": "message_end", "total_tokens": 100}\ndata: [DONE]\n',
        {
          status: 200,
          headers: { "Content-Type": "text/event-stream" },
        }
      )
    );
    global.fetch = mockFetch;

    const { result } = renderHook(() =>
      useChat({ conversationId: "test-conv-id" })
    );

    // When
    await act(async () => {
      await result.current.sendMessage("タスクを作成して");
    });

    // Then
    expect(result.current.messages).toHaveLength(2); // ユーザー + エージェント
    expect(result.current.messages[0].role).toBe("user");
    expect(result.current.messages[0].content).toBe("タスクを作成して");
  });
```

#### TC-026: SSE content_delta イベントでエージェントメッセージが更新される

```typescript
  it("SSE content_delta イベントでエージェントメッセージが逐次更新されること（TC-026）", async () => {
    // Given
    const sseStream = [
      'data: {"type": "message_start", "message_id": "msg_1"}\n\n',
      'data: {"type": "content_delta", "delta": "タスクを"}\n\n',
      'data: {"type": "content_delta", "delta": "作成しました。"}\n\n',
      'data: {"type": "message_end", "total_tokens": 50}\n\n',
      "data: [DONE]\n\n",
    ].join("");

    const mockFetch = jest.fn().mockResolvedValue(
      new Response(sseStream, {
        status: 200,
        headers: { "Content-Type": "text/event-stream" },
      })
    );
    global.fetch = mockFetch;

    const { result } = renderHook(() =>
      useChat({ conversationId: "test-conv-id" })
    );

    // When
    await act(async () => {
      await result.current.sendMessage("タスクを作成して");
    });

    // Then
    const assistantMessage = result.current.messages.find(
      (m) => m.role === "assistant"
    );
    expect(assistantMessage?.content).toBe("タスクを作成しました。");
  });
```

#### TC-027: API エラー時に onError コールバックが呼ばれる

```typescript
  it("API エラー発生時に onError コールバックが呼ばれること（TC-027）", async () => {
    // Given
    const mockFetch = jest.fn().mockResolvedValue(
      new Response(JSON.stringify({ error: { code: "SERVICE_UNAVAILABLE" } }), {
        status: 503,
        headers: { "Content-Type": "application/json" },
      })
    );
    global.fetch = mockFetch;

    const mockOnError = jest.fn();
    const { result } = renderHook(() =>
      useChat({ conversationId: "test-conv-id", onError: mockOnError })
    );

    // When
    await act(async () => {
      await result.current.sendMessage("タスクを作成して");
    });

    // Then
    expect(mockOnError).toHaveBeenCalled();
  });
});
```

---

## 4. テストフィクスチャ設計

### 4.1 バックエンドフィクスチャ（conftest.py）

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock
from app.infra.redmine.redmine_adapter import RedmineAdapter
from app.application.task.task_create_service import TaskCreateService


@pytest.fixture
def mock_redmine_adapter() -> AsyncMock:
    """RedmineAdapter のモックフィクスチャ。"""
    mock = AsyncMock(spec=RedmineAdapter)
    return mock


@pytest.fixture
def task_create_service(mock_redmine_adapter: AsyncMock) -> TaskCreateService:
    """TaskCreateService のフィクスチャ。RedmineAdapter をモック化する。"""
    return TaskCreateService(redmine_adapter=mock_redmine_adapter)


@pytest.fixture
def redmine_adapter() -> RedmineAdapter:
    """テスト用 RedmineAdapter（httpx-mock と組み合わせて使用）。"""
    return RedmineAdapter(
        base_url="http://localhost:8080",
        api_key="test-api-key",
    )


@pytest.fixture
def mock_task_create_service(monkeypatch) -> AsyncMock:
    """TaskCreateService のモックフィクスチャ（create_task_tool テスト用）。"""
    mock = AsyncMock(spec=TaskCreateService)
    monkeypatch.setattr(
        "app.agent.tools.create_task_tool.TaskCreateService",
        lambda *args, **kwargs: mock,
    )
    return mock
```

---

## 5. モック設計

### 5.1 バックエンドモック一覧

| モック対象 | モッククラス | 使用テスト |
|---|---|---|
| `RedmineAdapter` | `AsyncMock(spec=RedmineAdapter)` | TC-005〜011 |
| `httpx.AsyncClient` | `pytest-httpx` の `HTTPXMock` | TC-012〜017 |
| `TaskCreateService` | `AsyncMock(spec=TaskCreateService)` | TC-001〜004 |
| `get_settings()` | `unittest.mock.patch` | TC-001〜004 |

### 5.2 フロントエンドモック一覧

| モック対象 | モック方法 | 使用テスト |
|---|---|---|
| `fetch` API | `jest.fn()` | TC-025〜027 |
| `crypto.randomUUID()` | `jest.spyOn()` | TC-025〜027 |

---

## 6. カバレッジ目標

| 対象 | 目標カバレッジ | 計測方法 |
|---|---|---|
| バックエンド全体 | 80% 以上 | `pytest --cov=app --cov-report=term-missing` |
| `TaskCreateService` | 90% 以上 | 上記レポートで確認 |
| `RedmineAdapter` | 85% 以上 | 上記レポートで確認 |
| フロントエンド全体 | 80% 以上 | `jest --coverage` |
| `MessageBubble` | 90% 以上 | 上記レポートで確認 |
| `useChat` | 85% 以上 | 上記レポートで確認 |

---

## 7. テスト実行方法

### 7.1 バックエンドテスト

```bash
# 全テスト実行（カバレッジ付き）
cd backend
pytest tests/unit/ --cov=app --cov-report=term-missing --cov-fail-under=80 -v

# 特定テストファイルのみ実行
pytest tests/unit/test_task_create_service.py -v

# TDD の Red フェーズ確認（実装前にテストが失敗することを確認）
pytest tests/unit/test_create_task_tool.py::test_create_task_tool_with_title_only_returns_success_message -v
```

### 7.2 フロントエンドテスト

```bash
# 全テスト実行（カバレッジ付き）
cd frontend
npm test -- --coverage --watchAll=false

# 特定テストファイルのみ実行
npm test -- --testPathPattern="MessageBubble" --watchAll=false

# TDD の Red フェーズ確認
npm test -- --testNamePattern="TC-018" --watchAll=false
```

### 7.3 CI での自動実行（将来的な設定）

```yaml
# .github/workflows/test.yml（将来実装予定）
name: Tests
on: [push, pull_request]
jobs:
  backend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements-dev.txt
      - run: pytest tests/unit/ --cov=app --cov-fail-under=80

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "18"
      - run: npm ci
      - run: npm test -- --coverage --watchAll=false
```

---

## 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-001_FEAT-001 | 本テスト設計書に基づく Red → Green → Refactor サイクルでの実装。テストコードと実行結果を IMP-001 に含める |
| IMP-002_FEAT-001 | フロントエンドのテストコードと実行結果を IMP-002 に含める |
| IMP-005 | TDD 中に発見した不具合を IMP-005_tdd-defect-list.md に記録する |
