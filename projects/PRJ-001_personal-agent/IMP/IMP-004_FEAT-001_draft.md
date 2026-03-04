# IMP-004 DB マイグレーション下書き（FEAT-001）

| 項目 | 値 |
|---|---|
| 対象機能 | FEAT-001 Redmineタスク作成（redmine-task-create） |
| プロジェクトID | PRJ-001 |
| 作成日 | 2026-03-04 |

> このファイルは並行作業用の下書き。全 FEAT 完了後に IMP-004_db-migration.md へ統合する。

---

## マイグレーションファイル一覧（この機能分）

| 順序（仮） | ファイル名 | 内容 | 依存テーブル |
|---|---|---|---|
| 1 | `backend/alembic/versions/0001_initial_schema.py` | `conversations` テーブル新規作成 | なし（ルートテーブル） |
| 2 | `backend/alembic/versions/0001_initial_schema.py` | `messages` テーブル新規作成 | `conversations`（FK） |
| 3 | `backend/alembic/versions/0001_initial_schema.py` | `agent_executions` テーブル新規作成 | `conversations`（FK）、`messages`（FK） |
| 4 | `backend/alembic/versions/0001_initial_schema.py` | `agent_tool_calls` テーブル新規作成 | `agent_executions`（FK） |

> 注記: 4テーブルはすべて同一マイグレーションファイル `0001_initial_schema.py` に含まれる。
> 実行順序は upgrade() 関数内で制御される（conversations → messages → agent_executions → agent_tool_calls）。

## テーブル詳細

### conversations テーブル

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(200) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMPTZ NULL
);
```

インデックス:
- `idx_conversations_updated_at` (updated_at DESC)
- `idx_conversations_deleted_at` (deleted_at)

### messages テーブル

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'tool', 'system')),
    content TEXT NULL,
    tool_calls JSONB NULL,
    token_count INTEGER NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

インデックス:
- `idx_messages_conversation_id` (conversation_id)
- `idx_messages_conversation_created` (conversation_id, created_at)

### agent_executions テーブル

```sql
CREATE TABLE agent_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    trigger_message_id UUID NULL REFERENCES messages(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'running'
        CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    checkpoint_data JSONB NULL,
    error_message TEXT NULL,
    total_input_tokens INTEGER NULL,
    total_output_tokens INTEGER NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ NULL
);
```

インデックス:
- `idx_agent_executions_conversation_id` (conversation_id)
- `idx_agent_executions_status` (status)

### agent_tool_calls テーブル

```sql
CREATE TABLE agent_tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_execution_id UUID NOT NULL REFERENCES agent_executions(id) ON DELETE CASCADE,
    tool_call_id VARCHAR(100) NOT NULL,
    tool_name VARCHAR(100) NOT NULL,
    input_params JSONB NOT NULL DEFAULT '{}',
    output_result TEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'success'
        CHECK (status IN ('success', 'error')),
    error_message TEXT NULL,
    redmine_issue_id INTEGER NULL,
    duration_ms INTEGER NULL,
    called_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

インデックス:
- `idx_agent_tool_calls_execution_id` (agent_execution_id)
- `idx_agent_tool_calls_tool_name` (tool_name)
- `idx_agent_tool_calls_redmine_issue_id` (redmine_issue_id)

## マイグレーション実行コマンド

```bash
cd backend
alembic upgrade head
```

## ロールバックスクリプト概要

```bash
cd backend
alembic downgrade base
```

downgrade() では agent_tool_calls → agent_executions → messages → conversations の順に DROP TABLE を実行する。

## テーブル依存関係の申し送り

FEAT-001 の 4テーブルはシステムの基盤テーブルであり、他の FEAT のマイグレーションが依存する可能性がある。

- 「conversations テーブルは他のすべての FEAT のマイグレーションより先に実行される必要がある」
- FEAT-002〜FEAT-006 のマイグレーションが conversations・messages テーブルを参照する場合は、FEAT-001 の 0001_initial_schema.py を先に実行すること

## 統合時の注意事項

全 FEAT の draft が出揃った後、IMP-004_db-migration.md に統合する際は以下を考慮すること:

1. FEAT-001 の `0001_initial_schema.py` が必ず最初に実行されること
2. 他 FEAT のマイグレーションは `down_revision = "0001"` を指定して依存関係を明示すること
3. テーブル間の外部キー制約の実行順序を確認すること
