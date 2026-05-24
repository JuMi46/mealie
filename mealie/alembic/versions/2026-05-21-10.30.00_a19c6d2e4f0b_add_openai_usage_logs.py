"""add openai usage logs

Revision ID: a19c6d2e4f0b
Revises: 2187537c52b8
Create Date: 2026-05-21 10:30:00.000000

"""

import sqlalchemy as sa

from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "a19c6d2e4f0b"
down_revision: str | None = "2187537c52b8"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    op.create_table(
        "openai_usage_logs",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("timestamp", mealie.db.migration_types.NaiveDateTime(), nullable=False),
        sa.Column("endpoint", sa.String(), nullable=False),
        sa.Column("operation", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("provider", sa.String(), nullable=True),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("had_attachments", sa.Boolean(), nullable=False),
        sa.Column("error_class", sa.String(), nullable=True),
        sa.Column("error_message", sa.String(), nullable=True),
        sa.Column("group_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("household_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("user_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("created_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.Column("update_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"]),
        sa.ForeignKeyConstraint(["household_id"], ["households.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("openai_usage_logs", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_openai_usage_logs_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_openai_usage_logs_timestamp"), ["timestamp"], unique=False)
        batch_op.create_index(batch_op.f("ix_openai_usage_logs_endpoint"), ["endpoint"], unique=False)
        batch_op.create_index(batch_op.f("ix_openai_usage_logs_status"), ["status"], unique=False)
        batch_op.create_index(batch_op.f("ix_openai_usage_logs_model"), ["model"], unique=False)
        batch_op.create_index(batch_op.f("ix_openai_usage_logs_group_id"), ["group_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_openai_usage_logs_household_id"), ["household_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_openai_usage_logs_user_id"), ["user_id"], unique=False)


def downgrade():
    with op.batch_alter_table("openai_usage_logs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_openai_usage_logs_user_id"))
        batch_op.drop_index(batch_op.f("ix_openai_usage_logs_household_id"))
        batch_op.drop_index(batch_op.f("ix_openai_usage_logs_group_id"))
        batch_op.drop_index(batch_op.f("ix_openai_usage_logs_model"))
        batch_op.drop_index(batch_op.f("ix_openai_usage_logs_status"))
        batch_op.drop_index(batch_op.f("ix_openai_usage_logs_endpoint"))
        batch_op.drop_index(batch_op.f("ix_openai_usage_logs_timestamp"))
        batch_op.drop_index(batch_op.f("ix_openai_usage_logs_created_at"))

    op.drop_table("openai_usage_logs")
