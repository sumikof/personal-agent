# DSD-008_FEAT-005 単体テスト設計書（チャットUI）

| 項目 | 値 |
|---|---|
| ドキュメントID | DSD-008_FEAT-005 |
| バージョン | 1.0 |
| 作成日 | 2026-03-03 |
| 機能ID | FEAT-005 |
| 機能名 | チャットUI（chat-ui） |
| 入力元 | DSD-001_FEAT-005, DSD-002_FEAT-005, DSD-003_FEAT-005 |
| ステータス | 初版 |

---

## 目次

1. テスト設計方針
2. テスト対象コンポーネント
3. モック方針
4. バックエンドテストケース
5. フロントエンドテストケース
6. SSEストリーミングテストケース
7. テスト実行環境
8. カバレッジ目標
9. 後続フェーズへの影響

---

## 1. テスト設計方針

### 1.1 TDD方針

本設計書はTDD（テスト駆動開発）の起点となる。DSD-001〜003の設計に基づいて先にテストを記述し（Red）、テストが通る実装を行い（Green）、コードを整理する（Refactor）のサイクルで開発する。

| フェーズ | 説明 |
|---|---|
| Red | 本設計書のテストケースをコードに落とし込む。すべて失敗することを確認する |
| Green | テストが通る最小限の実装を行う |
| Refactor | コードの品質・可読性を改善する。テストは引き続きパスすること |

### 1.2 テストレベル

本設計書が対象とするのは単体テスト（UT）のみ。結合テストはIT-001_FEAT-005で定義する。

| テストレベル | 対象 | 本書の対象 |
|---|---|---|
| 単体テスト（UT） | クラス・関数単位のテスト | ○（本書） |
| 結合テスト（IT） | API〜DB・フロントエンド〜バックエンド連携 | × （IT-001_FEAT-005） |
| システムテスト（ST） | E2Eシナリオ | × （ST-001） |

### 1.3 テストフレームワーク

| 領域 | フレームワーク | 補助ライブラリ |
|---|---|---|
| バックエンド（Python） | pytest + pytest-asyncio | pytest-mock, httpx（AsyncClient）, faker |
| フロントエンド（TypeScript） | Vitest + Testing Library | @testing-library/react, @testing-library/user-event, msw（Mock Service Worker） |

---

## 2. テスト対象コンポーネント

### 2.1 バックエンドテスト対象

| テスト対象 | クラス/モジュール | テストファイル |
|---|---|---|
| 会話サービス | `ConversationService` | `tests/chat/test_conversation_service.py` |
| 会話リポジトリ | `ConversationRepository` | `tests/chat/test_conversation_repository.py` |
| メッセージリポジトリ | `MessageRepository` | `tests/chat/test_message_repository.py` |
| LangGraphワークフロー | `AgentWorkflow` | `tests/agent/test_agent_workflow.py` |
| ツールレジストリ | `ToolRegistry` | `tests/agent/test_tool_registry.py` |
| SSEイベント生成 | `event_generator` | `tests/chat/test_sse_streaming.py` |
| APIルーター | `ConversationRouter` | `tests/chat/test_conversation_router.py` |

### 2.2 フロントエンドテスト対象

| テスト対象 | コンポーネント/フック | テストファイル |
|---|---|---|
| チャットウィンドウ | `ChatWindow` | `src/components/chat/__tests__/ChatWindow.test.tsx` |
| メッセージバブル | `MessageBubble` | `src/components/chat/__tests__/MessageBubble.test.tsx` |
| メッセージ入力 | `MessageInput` | `src/components/chat/__tests__/MessageInput.test.tsx` |
| ToolCallカード | `ToolCallCard` | `src/components/chat/__tests__/ToolCallCard.test.tsx` |
| 会話管理フック | `useConversation` | `src/hooks/__tests__/useConversation.test.ts` |
| SSEイベントハンドラ | `handleSSEEvent` | `src/lib/__tests__/sse.test.ts` |

---

## 3. モック方針

### 3.1 バックエンドモック

| モック対象 | モック方法 | 理由 |
|---|---|---|
| `ClaudeAPIClient` | `pytest-mock`で`create_message_stream`をモック | 外部API依存・コスト発生・レスポンス時間の非決定性 |
| `RedmineMCPClient` | `pytest-mock`で各メソッドをモック | 外部Redmineサーバ依存 |
| `AsyncSession`（DB） | `pytest-asyncio`+インメモリSQLite または `sqlalchemy` モック | テスト時のDB依存排除 |
| `asyncio.sleep` | `pytest-mock` | リトライ時のwaitをスキップ |

**ClaudeAPIClientのモック実装例:**

```python
# tests/conftest.py
import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_claude_client():
    """Claude APIクライアントのモック"""
    client = MagicMock()

    async def mock_stream(*args, **kwargs):
        """テキストチャンクとツール呼び出しをシミュレート"""
        events = [
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "タスクを"}},
            {"type": "content_block_delta", "delta": {"type": "text_delta", "text": "作成します"}},
            {"type": "message_stop"},
        ]
        for event in events:
            yield event

    client.create_message_stream = AsyncMock(return_value=mock_stream())
    return client

@pytest.fixture
def mock_redmine_client():
    """Redmine MCPクライアントのモック"""
    client = MagicMock()
    client.create_issue = AsyncMock(return_value={
        "id": 123,
        "title": "テストタスク",
        "status": {"id": 1, "name": "New"},
        "url": "http://localhost:8080/issues/123"
    })
    client.get_issues = AsyncMock(return_value={
        "issues": [
            {"id": 1, "subject": "設計書作成", "status": {"name": "In Progress"}}
        ],
        "total_count": 1
    })
    return client
```

### 3.2 フロントエンドモック

| モック対象 | モック方法 | 理由 |
|---|---|---|
| `fetch` API | Mock Service Worker（msw） | バックエンドAPI依存排除 |
| SSEストリーム | `ReadableStream`をモック | ストリーミング動作の再現 |
| `useConversation`フック | `vi.mock` | 上位コンポーネントのテスト用 |

**MSWハンドラ設定例:**

```typescript
// src/mocks/handlers.ts
import { http, HttpResponse } from 'msw';

export const handlers = [
  // 会話作成
  http.post('/api/v1/conversations', () => {
    return HttpResponse.json({
      data: {
        id: 'test-conversation-id',
        title: null,
        created_at: '2026-03-03T10:00:00Z',
        updated_at: '2026-03-03T10:00:00Z',
      }
    }, { status: 201 });
  }),

  // メッセージ送信（SSEモック）
  http.post('/api/v1/conversations/:id/messages', () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        const events = [
          'data: {"type":"message_start","message_id":"msg-001"}\n\n',
          'data: {"type":"chunk","content":"テスト応答"}\n\n',
          'data: {"type":"done","message_id":"msg-001"}\n\n',
          'data: [DONE]\n\n',
        ];
        events.forEach(event => {
          controller.enqueue(encoder.encode(event));
        });
        controller.close();
      }
    });
    return new Response(stream, {
      headers: { 'Content-Type': 'text/event-stream' }
    });
  }),
];
```

---

## 4. バックエンドテストケース

### 4.1 ConversationServiceテスト

#### TC-BE-001: 会話新規作成（正常系）

```
Given: DBが正常に動作している
When: ConversationService.create_conversation(title=None) を呼び出す
Then:
  - Conversation オブジェクトが返される
  - conversation.id が UUID v4 形式である
  - conversation.title が None である
  - conversation.created_at が現在時刻付近（±1秒）である
  - DBに1件のconversationレコードが挿入されている
```

```python
@pytest.mark.asyncio
async def test_create_conversation_without_title(
    conversation_service: ConversationService,
    db_session: AsyncSession
):
    # Given: DBが正常に動作している（fixtureで確保済み）

    # When
    result = await conversation_service.create_conversation(title=None)

    # Then
    assert result.id is not None
    assert str(result.id) != ""
    assert result.title is None
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    assert abs((result.created_at - now).total_seconds()) < 5
    # DBの確認
    db_record = await db_session.get(ConversationORM, result.id)
    assert db_record is not None
    assert db_record.deleted_at is None
```

#### TC-BE-002: 会話新規作成（タイトルあり）

```
Given: DBが正常に動作している
When: ConversationService.create_conversation(title="テスト会話") を呼び出す
Then:
  - conversation.title が "テスト会話" である
```

#### TC-BE-003: 存在しない会話の取得（異常系）

```
Given: 指定したIDの会話が存在しない
When: ConversationService.get_conversation("non-existent-id") を呼び出す
Then: NotFoundException が raise される
```

```python
@pytest.mark.asyncio
async def test_get_conversation_not_found(
    conversation_service: ConversationService
):
    # Given: 存在しないUUID
    fake_id = "00000000-0000-0000-0000-000000000000"

    # When / Then
    with pytest.raises(NotFoundException) as exc_info:
        await conversation_service.get_conversation(fake_id)
    assert exc_info.value.status_code == 404
```

#### TC-BE-004: 論理削除済み会話の取得（異常系）

```
Given: 指定したIDの会話が論理削除済み（deleted_at != NULL）
When: ConversationService.get_conversation(conversation_id) を呼び出す
Then: NotFoundException が raise される
```

#### TC-BE-005: メッセージ送信→エージェント応答（正常系・ツールなし）

```
Given:
  - 有効な会話が存在する
  - ClaudeAPIClientが "こんにちは！" とストリーミング応答するようにモック済み
  - Redmine MCPClientが不要（ツール呼び出しなし）
When: ConversationService.send_message_stream(conversation_id, "はじめまして") を呼び出す
Then:
  - SSEEventのAsyncIteratorが返される
  - イベントの順序: message_start → chunk × N → done
  - chunkイベントのcontentを結合すると "こんにちは！" になる
  - DBにユーザーメッセージ（role="user"）が保存されている
  - DBにエージェントメッセージ（role="assistant", content="こんにちは！"）が保存されている
```

```python
@pytest.mark.asyncio
async def test_send_message_stream_no_tool_call(
    conversation_service: ConversationService,
    mock_claude_client: MagicMock,
    db_session: AsyncSession
):
    # Given
    conversation = await conversation_service.create_conversation()

    # When
    events = []
    async for event in conversation_service.send_message_stream(
        conversation.id, "はじめまして"
    ):
        events.append(event)

    # Then
    event_types = [e["type"] for e in events]
    assert "message_start" in event_types
    assert "chunk" in event_types
    assert "done" in event_types

    # chunkのcontentを結合
    content = "".join(e["content"] for e in events if e["type"] == "chunk")
    assert content == "こんにちは！"

    # DBの確認
    messages = await db_session.execute(
        select(MessageORM).where(MessageORM.conversation_id == conversation.id)
        .order_by(MessageORM.created_at)
    )
    messages = messages.scalars().all()
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "はじめまして"
    assert messages[1].role == "assistant"
    assert messages[1].content == "こんにちは！"
```

#### TC-BE-006: メッセージ送信→ツール呼び出しあり（正常系）

```
Given:
  - 有効な会話が存在する
  - ClaudeAPIClientがtool_use（create_issue）を含むレスポンスをモック
  - RedmineMCPClientがissue作成成功をモック（{"id": 123, "title": "テスト"}）
When: ConversationService.send_message_stream(conversation_id, "タスクを作成して") を呼び出す
Then:
  - SSEEventにtool_callイベントが含まれる（tool="create_issue"）
  - SSEEventにtool_resultイベントが含まれる（result.id=123）
  - DBのagent_tool_callsに1件のレコードが保存されている
  - tool_name="create_issue", status="success"
```

```python
@pytest.mark.asyncio
async def test_send_message_stream_with_tool_call(
    conversation_service: ConversationService,
    mock_claude_client_with_tool: MagicMock,
    mock_redmine_client: MagicMock,
    db_session: AsyncSession
):
    # Given
    conversation = await conversation_service.create_conversation()

    # When
    events = []
    async for event in conversation_service.send_message_stream(
        conversation.id, "タスクを作成して"
    ):
        events.append(event)

    # Then: ツール呼び出しイベントの確認
    tool_call_events = [e for e in events if e["type"] == "tool_call"]
    assert len(tool_call_events) >= 1
    assert tool_call_events[0]["tool"] == "create_issue"

    tool_result_events = [e for e in events if e["type"] == "tool_result"]
    assert len(tool_result_events) >= 1
    assert tool_result_events[0]["result"]["id"] == 123

    # DBのagent_tool_callsの確認
    messages = await db_session.execute(
        select(MessageORM).where(
            MessageORM.conversation_id == conversation.id,
            MessageORM.role == "assistant"
        )
    )
    assistant_msg = messages.scalars().first()
    assert assistant_msg is not None

    tool_calls = await db_session.execute(
        select(AgentToolCallORM).where(
            AgentToolCallORM.message_id == assistant_msg.id
        )
    )
    tool_call_records = tool_calls.scalars().all()
    assert len(tool_call_records) == 1
    assert tool_call_records[0].tool_name == "create_issue"
    assert tool_call_records[0].status == "success"
```

#### TC-BE-007: Claude API接続失敗（異常系）

```
Given:
  - 有効な会話が存在する
  - ClaudeAPIClientがAPIConnectionErrorを raise するようにモック
When: ConversationService.send_message_stream(conversation_id, "テスト") を呼び出す
Then:
  - SSEEventのAsyncIteratorからerrorイベントが yield される
  - error["type"] == "error"
  - error["error"] に "AIとの通信" を含むメッセージが入っている
  - 例外は呼び出し元に伝播しない（イベントとして返す）
```

```python
@pytest.mark.asyncio
async def test_send_message_claude_api_error(
    conversation_service: ConversationService,
    mock_claude_client_error: MagicMock,
    db_session: AsyncSession
):
    # Given
    conversation = await conversation_service.create_conversation()

    # When
    events = []
    async for event in conversation_service.send_message_stream(
        conversation.id, "テスト"
    ):
        events.append(event)

    # Then
    error_events = [e for e in events if e["type"] == "error"]
    assert len(error_events) >= 1
    assert "AI" in error_events[0]["error"] or "通信" in error_events[0]["error"]
```

#### TC-BE-008: 会話削除（正常系）

```
Given: 有効な会話が存在する
When: ConversationService.delete_conversation(conversation_id) を呼び出す
Then:
  - DBのconversationsレコードのdeleted_atが設定される
  - その後get_conversation(conversation_id)でNotFoundExceptionが発生する
```

### 4.2 AgentWorkflowテスト

#### TC-BE-009: LangGraphワークフロー初期化（正常系）

```
Given: ToolRegistryとClaudeAPIClientが設定済み
When: AgentWorkflow() を初期化する
Then:
  - グラフが正常にコンパイルされる（例外なし）
  - 3つのノード（llm_node, tool_executor_node）が定義されている
```

#### TC-BE-010: tool_router_nodeのルーティング（ツールあり）

```
Given: AgentStateのtool_callsに1件のツール呼び出しが設定されている
When: tool_router_node(state) を呼び出す
Then: "tool_executor_node" が返される
```

```python
def test_tool_router_with_tool_calls(agent_workflow: AgentWorkflow):
    # Given
    state = AgentState(
        messages=[],
        tool_calls=[{"id": "call_001", "name": "create_issue", "input": {}}],
        intermediate_steps=[],
        conversation_id="test-id",
        streaming_events=[]
    )

    # When
    result = agent_workflow.tool_router_node(state)

    # Then
    assert result == "tool_executor_node"
```

#### TC-BE-011: tool_router_nodeのルーティング（ツールなし）

```
Given: AgentStateのtool_callsがNone
When: tool_router_node(state) を呼び出す
Then: "__end__" が返される
```

### 4.3 ToolRegistryテスト

#### TC-BE-012: ツール登録と取得（正常系）

```
Given: ToolRegistry が初期化済み
When:
  1. mock_tool を register() で登録する
  2. get_by_name(mock_tool.name) で取得する
Then:
  - 登録したmock_toolが返される
```

#### TC-BE-013: 未登録ツールのディスパッチ（異常系）

```
Given: ToolRegistryに "unknown_tool" が登録されていない
When: dispatch("unknown_tool", {}) を呼び出す
Then: ValueError が raise される
```

```python
@pytest.mark.asyncio
async def test_dispatch_unknown_tool(tool_registry: ToolRegistry):
    # Given: unknown_tool は未登録

    # When / Then
    with pytest.raises(ValueError, match="ツール 'unknown_tool' が登録されていません"):
        await tool_registry.dispatch("unknown_tool", {})
```

### 4.4 SSEストリーミングテスト

#### TC-BE-014: SSEイベントジェネレータ（正常系）

```
Given: ConversationServiceのsend_message_streamが正常なSSEイベントを yield する
When: event_generator(conversation_id, content, service) を非同期で消費する
Then:
  - 各イベントが "data: {JSON}\n\n" 形式で生成される
  - 最後に "data: [DONE]\n\n" が生成される
```

```python
@pytest.mark.asyncio
async def test_event_generator_format(
    mock_conversation_service: MagicMock
):
    # Given
    mock_conversation_service.send_message_stream = AsyncMock(
        return_value=aiter([
            {"type": "chunk", "content": "テスト"},
            {"type": "done", "message_id": "msg-001"},
        ])
    )

    # When
    lines = []
    async for line in event_generator("conv-id", "テスト入力", mock_conversation_service):
        lines.append(line)

    # Then
    assert lines[0].startswith("data: ")
    assert '"type": "chunk"' in lines[0]
    assert lines[-1] == "data: [DONE]\n\n"
```

#### TC-BE-015: SSEチャンク分割受信（メッセージ分割テスト）

```
Given: ClaudeAPIが "タ" "ス" "ク" と1文字ずつストリーミングするようにモック
When: send_message_stream を消費する
Then:
  - 3つの chunk イベントが生成される
  - 各chunkのcontentを結合すると "タスク" になる
```

---

## 5. フロントエンドテストケース

### 5.1 MessageInputテスト

#### TC-FE-001: メッセージ送信（正常系）

```
Given: MessageInputコンポーネントが onSend コールバックとともにレンダリングされている
When: 入力欄に "テストメッセージ" を入力し、送信ボタンをクリックする
Then:
  - onSend が "テストメッセージ" の引数で1回呼ばれる
  - 入力欄がクリアされる
```

```typescript
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MessageInput } from '../MessageInput';

test('送信ボタンクリックでonSendが呼ばれる', async () => {
  // Given
  const onSend = vi.fn();
  render(<MessageInput onSend={onSend} disabled={false} />);
  const input = screen.getByRole('textbox');
  const button = screen.getByRole('button', { name: '送信' });

  // When
  await userEvent.type(input, 'テストメッセージ');
  await userEvent.click(button);

  // Then
  expect(onSend).toHaveBeenCalledWith('テストメッセージ');
  expect(onSend).toHaveBeenCalledTimes(1);
  expect(input).toHaveValue('');
});
```

#### TC-FE-002: Enterキーで送信

```
Given: MessageInputが disabled=false でレンダリングされている
When: 入力欄に "テスト" を入力し、Enterキーを押す
Then: onSend が "テスト" で呼ばれる
```

#### TC-FE-003: Shift+Enterで改行（送信しない）

```
Given: MessageInputが disabled=false でレンダリングされている
When: 入力欄に "テスト" を入力し、Shift+Enterを押す
Then:
  - onSend は呼ばれない
  - 入力欄内で改行が発生する
```

#### TC-FE-004: disabled時は送信不可

```
Given: MessageInputが disabled=true でレンダリングされている
When: 送信ボタンをクリックする
Then:
  - onSend が呼ばれない
  - 送信ボタンが disabled 状態である
  - 入力欄が disabled 状態である
```

```typescript
test('disabled=trueのとき送信できない', async () => {
  // Given
  const onSend = vi.fn();
  render(<MessageInput onSend={onSend} disabled={true} />);
  const button = screen.getByRole('button', { name: '送信' });

  // When
  await userEvent.click(button);

  // Then
  expect(onSend).not.toHaveBeenCalled();
  expect(button).toBeDisabled();
});
```

#### TC-FE-005: 空白のみのメッセージは送信しない

```
Given: MessageInputが disabled=false でレンダリングされている
When: 入力欄に "   "（スペースのみ）を入力し、送信ボタンをクリックする
Then: onSend が呼ばれない
```

### 5.2 MessageBubbleテスト

#### TC-FE-006: ユーザーメッセージの表示（正常系）

```
Given: roleが "user"、contentが "テスト" のMessage
When: MessageBubble をレンダリングする
Then:
  - "テスト" テキストが表示されている
  - バブルが右寄せ（justify-end）である
  - 背景色クラス "bg-blue-500" が適用されている
```

#### TC-FE-007: エージェントメッセージのMarkdownレンダリング（正常系）

```
Given: roleが "assistant"、contentが "**太字テスト**" のMessage
When: MessageBubble をレンダリングする
Then:
  - "太字テスト" が<strong>タグ（または相当するスタイル）でレンダリングされている
```

#### TC-FE-008: ストリーミング中のカーソル表示

```
Given: isStreaming=true のStreamingMessage
When: MessageBubble をレンダリングする
Then:
  - ストリーミングカーソル（▋またはアニメーション要素）が表示されている
```

#### TC-FE-009: ツール呼び出しカードの表示

```
Given: tool_callsを持つエージェントMessage
When: MessageBubble をレンダリングする
Then:
  - ToolCallCardコンポーネントが表示されている
```

### 5.3 useConversationフックテスト

#### TC-FE-010: 初回マウント時に会話作成APIが呼ばれる（正常系）

```
Given: MSWで POST /api/v1/conversations が 201 を返すように設定
When: useConversation フックを使用するコンポーネントをマウントする
Then:
  - conversation が null でなくなる
  - conversation.id が設定されている
```

```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useConversation } from '../useConversation';
import { server } from '../../mocks/server';

test('初回マウント時に会話が作成される', async () => {
  // Given: MSWのデフォルトハンドラで会話作成APIがモック済み

  // When
  const { result } = renderHook(() => useConversation());

  // Then
  await waitFor(() => {
    expect(result.current.conversation).not.toBeNull();
  });
  expect(result.current.conversation?.id).toBe('test-conversation-id');
});
```

#### TC-FE-011: メッセージ送信後のUI更新（楽観的更新）

```
Given:
  - 会話が初期化済み
  - MSWでSSEストリームが設定済み（chunk="テスト応答", done）
When: sendMessage("テスト") を呼び出す
Then:
  - sendMessage呼び出し後すぐに isStreaming が true になる
  - messages にユーザーメッセージが追加される（楽観的更新）
  - streamingMessage が更新され、content="テスト応答" になる
  - done受信後に isStreaming が false になる
  - messages にエージェントメッセージが追加される
```

#### TC-FE-012: SSE通信エラー（異常系）

```
Given:
  - 会話が初期化済み
  - MSWでメッセージ送信APIが 503 を返すように設定
When: sendMessage("テスト") を呼び出す
Then:
  - error が null でなくなる
  - isStreaming が false に戻る
```

---

## 6. SSEイベントハンドラテストケース

### 6.1 handleSSEEvent関数テスト

#### TC-SSE-001: chunkイベントのハンドリング

```
Given: {"type": "chunk", "content": "テスト"} のSSEイベント
When: handleSSEEvent(event, handlers) を呼び出す
Then: handlers.onChunk が "テスト" の引数で呼ばれる
```

```typescript
import { handleSSEEvent } from '../../lib/sse';

test('chunkイベントでonChunkが呼ばれる', () => {
  // Given
  const handlers = {
    onChunk: vi.fn(),
    onToolCall: vi.fn(),
    onDone: vi.fn(),
    onError: vi.fn(),
  };
  const event = { type: 'chunk' as const, content: 'テスト' };

  // When
  handleSSEEvent(event, handlers);

  // Then
  expect(handlers.onChunk).toHaveBeenCalledWith('テスト');
  expect(handlers.onToolCall).not.toHaveBeenCalled();
});
```

#### TC-SSE-002: tool_callイベントのハンドリング

```
Given: {"type": "tool_call", "tool": "create_issue", "input": {"title": "テスト"}} のSSEイベント
When: handleSSEEvent(event, handlers) を呼び出す
Then: handlers.onToolCall が {tool: "create_issue", input: {...}, result: null} の引数で呼ばれる
```

#### TC-SSE-003: doneイベントのハンドリング

```
Given: {"type": "done", "message_id": "msg-001"} のSSEイベント
When: handleSSEEvent(event, handlers) を呼び出す
Then: handlers.onDone が "msg-001" の引数で呼ばれる
```

#### TC-SSE-004: errorイベントのハンドリング

```
Given: {"type": "error", "error": "APIエラー"} のSSEイベント
When: handleSSEEvent(event, handlers) を呼び出す
Then: handlers.onError が "APIエラー" の引数で呼ばれる
```

#### TC-SSE-005: 不明なイベントタイプのハンドリング（異常系）

```
Given: {"type": "unknown_type"} のSSEイベント
When: handleSSEEvent(event, handlers) を呼び出す
Then: ハンドラは一切呼ばれない（エラーも throw しない）
```

---

## 7. テスト実行環境

### 7.1 バックエンドテスト環境

```
# pytest設定（pytest.ini または pyproject.toml）
[pytest]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

**テスト用DB設定:**

```python
# tests/conftest.py
@pytest.fixture(scope="function")
async def db_session():
    """テスト用インメモリSQLite（asyncio対応）"""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

**テスト実行コマンド:**
```bash
# 単体テスト実行
pytest tests/ -v --cov=app --cov-report=term-missing

# FEAT-005のみ実行
pytest tests/chat/ tests/agent/ -v
```

### 7.2 フロントエンドテスト環境

**vitest設定:**

```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/mocks/setup.ts'],
    coverage: {
      reporter: ['text', 'lcov'],
      include: ['src/**/*.{ts,tsx}'],
      exclude: ['src/**/*.test.{ts,tsx}', 'src/mocks/**'],
    },
  },
});
```

**テスト実行コマンド:**
```bash
# 単体テスト実行
npm run test

# カバレッジ計測
npm run test -- --coverage
```

---

## 8. カバレッジ目標

| 対象 | カバレッジ目標 | 優先対象 |
|---|---|---|
| バックエンド（Python） | 行カバレッジ 80%以上 | ConversationService, AgentWorkflow, ToolRegistry |
| フロントエンド（TypeScript） | 行カバレッジ 70%以上 | useConversation, handleSSEEvent, MessageInput |

**カバレッジ除外対象:**
- `app/main.py`（エントリーポイント）
- `app/config.py`（設定読み込みのみ）
- `alembic/`配下（マイグレーションスクリプト）
- `src/mocks/`配下（テスト用モック）

---

## 9. 後続フェーズへの影響

| 影響先 | 内容 |
|---|---|
| IMP-001_FEAT-005 | 本設計書のバックエンドテストケース（TC-BE-001〜015）をpytestで実装する |
| IMP-002_FEAT-005 | 本設計書のフロントエンドテストケース（TC-FE-001〜012）をVitestで実装する |
| IMP-005 | TDDサイクルで発見したバグはIMP-005（TDD不具合管理票）に記録する |
| IT-001_FEAT-005 | 本単体テストで確認した境界値・エッジケースを結合テストにも引き継ぐ |
