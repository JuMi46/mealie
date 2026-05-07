"""Add household food name overrides preference

Revision ID: e4c9b8a7d6f5
Revises: f2a1c4e9b7d0
Create Date: 2026-05-07 02:00:00.000000

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "e4c9b8a7d6f5"
down_revision: str | None = "f2a1c4e9b7d0"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "ingredient_food_name_overrides",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'"),
            )
        )

    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.alter_column("ingredient_food_name_overrides", server_default=None)


def downgrade():
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.drop_column("ingredient_food_name_overrides")
