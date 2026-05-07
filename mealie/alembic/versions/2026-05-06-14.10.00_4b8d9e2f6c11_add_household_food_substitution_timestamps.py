"""Add household food substitution timestamps

Revision ID: 4b8d9e2f6c11
Revises: a7c3d9f4e1ab
Create Date: 2026-05-06 14:10:00.000000

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "4b8d9e2f6c11"
down_revision: str | None = "a7c3d9f4e1ab"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    with op.batch_alter_table("household_food_substitutions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("update_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_household_food_substitutions_created_at", ["created_at"], unique=False)


def downgrade():
    with op.batch_alter_table("household_food_substitutions", schema=None) as batch_op:
        batch_op.drop_index("ix_household_food_substitutions_created_at")
        batch_op.drop_column("update_at")
        batch_op.drop_column("created_at")
