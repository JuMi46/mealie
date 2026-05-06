"""Add household temperature display template preference

Revision ID: f2a1c4e9b7d0
Revises: c8b3ed6e8fc4
Create Date: 2026-05-06 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "f2a1c4e9b7d0"
down_revision: str | None = "c8b3ed6e8fc4"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("temperature_display_template", sa.String(), nullable=False, server_default="℃ / ℉")
        )

    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.alter_column("temperature_display_template", server_default=None)


def downgrade():
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.drop_column("temperature_display_template")
