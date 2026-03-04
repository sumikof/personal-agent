"""Initial schema for FEAT-001: Redmine task creation.

Revision ID: 0001
Revises:
Create Date: 2026-03-04
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """テーブルを作成する。"""
    # conversations テーブル
    op.create_table(
        "conversations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
            comment="会話ID（UUID v4）",
        ),
        sa.Column("title", sa.String(200), nullable=True, comment="会話タイトル（フェーズ1ではNULL）"),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="作成日時",
        ),
        sa.Column(
            "updated_at",
            postgresql.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("NOW()"),
            comment="更新日時",
        ),
        sa.Column(
            "deleted_at",
            postgresql.TIMESTAMPTZ(),
            nullable=True,
            comment="論理削除日時（NULL=有効）",
        ),
        comment="ユーザーとエージェントの対話セッション",
    )
    op.create_index(
        "idx_conversations_updated_at",
        "conversations",
        [sa.text("updated_at DESC")],
    )
    op.create_index(
        "idx_conversations_deleted_at",
        "conversations",
        ["deleted_at"],
    )

    # messages テーブル
    op.create_table(
        "messages",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
            comment="会話ID（外部キー）",
        ),
        sa.Column("role", sa.String(20), nullable=False, comment="メッセージロール（user/assistant/tool/system）"),
        sa.Column("content", sa.Text(), nullable=True, comment="メッセージ本文"),
        sa.Column("tool_calls", postgresql.JSONB(), nullable=True, comment="ツール呼び出し情報（JSON）"),
        sa.Column("token_count", sa.Integer(), nullable=True, comment="トークン数（コスト管理用）"),
        sa.Column(
            "created_at",
            postgresql.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "role IN ('user', 'assistant', 'tool', 'system')",
            name="ck_messages_role",
        ),
        comment="会話内のメッセージ（ユーザー入力・エージェント応答）",
    )
    op.create_index("idx_messages_conversation_id", "messages", ["conversation_id"])
    op.create_index(
        "idx_messages_conversation_created",
        "messages",
        ["conversation_id", "created_at"],
    )

    # agent_executions テーブル
    op.create_table(
        "agent_executions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "conversation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "trigger_message_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("messages.id", ondelete="SET NULL"),
            nullable=True,
            comment="エージェント実行を起動したユーザーメッセージID",
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="running",
            comment="実行状態（running/completed/failed/cancelled）",
        ),
        sa.Column(
            "checkpoint_data",
            postgresql.JSONB(),
            nullable=True,
            comment="LangGraphグラフ状態スナップショット（JSONB）",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "total_input_tokens",
            sa.Integer(),
            nullable=True,
            comment="Claude API入力トークン数合計",
        ),
        sa.Column(
            "total_output_tokens",
            sa.Integer(),
            nullable=True,
            comment="Claude API出力トークン数合計",
        ),
        sa.Column(
            "started_at",
            postgresql.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("completed_at", postgresql.TIMESTAMPTZ(), nullable=True),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'cancelled')",
            name="ck_agent_executions_status",
        ),
        comment="LangGraphエージェントの実行インスタンス管理",
    )
    op.create_index(
        "idx_agent_executions_conversation_id",
        "agent_executions",
        ["conversation_id"],
    )
    op.create_index("idx_agent_executions_status", "agent_executions", ["status"])

    # agent_tool_calls テーブル
    op.create_table(
        "agent_tool_calls",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "agent_execution_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_executions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tool_call_id",
            sa.String(100),
            nullable=False,
            comment="Claude APIが発行するツール呼び出しID（toulu_xxx形式）",
        ),
        sa.Column(
            "tool_name",
            sa.String(100),
            nullable=False,
            comment="ツール名（create_task/search_tasks等）",
        ),
        sa.Column(
            "input_params",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
            comment="ツール入力パラメータ（JSON）",
        ),
        sa.Column("output_result", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="success",
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "redmine_issue_id",
            sa.Integer(),
            nullable=True,
            comment="操作したRedmineチケットID（タスク操作ツールのみ）",
        ),
        sa.Column(
            "duration_ms",
            sa.Integer(),
            nullable=True,
            comment="ツール実行処理時間（ミリ秒）",
        ),
        sa.Column(
            "called_at",
            postgresql.TIMESTAMPTZ(),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.CheckConstraint(
            "status IN ('success', 'error')",
            name="ck_agent_tool_calls_status",
        ),
        comment="エージェントのツール呼び出し詳細ログ",
    )
    op.create_index(
        "idx_agent_tool_calls_execution_id",
        "agent_tool_calls",
        ["agent_execution_id"],
    )
    op.create_index(
        "idx_agent_tool_calls_tool_name",
        "agent_tool_calls",
        ["tool_name"],
    )
    op.create_index(
        "idx_agent_tool_calls_redmine_issue_id",
        "agent_tool_calls",
        ["redmine_issue_id"],
    )


def downgrade() -> None:
    """テーブルを削除する（ロールバック用）。"""
    op.drop_table("agent_tool_calls")
    op.drop_table("agent_executions")
    op.drop_table("messages")
    op.drop_table("conversations")
