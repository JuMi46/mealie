"""Add default shopping list preference to household preferences

Revision ID: 3a7f5d2c9e11
Revises: f2a1c4e9b7d0
Create Date: 2026-05-06 23:40:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "3a7f5d2c9e11"
down_revision: str | None = "f2a1c4e9b7d0"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.add_column(sa.Column("default_shopping_list_id", mealie.db.migration_types.GUID(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_household_preferences_default_shopping_list_id"), ["default_shopping_list_id"], unique=False
        )
        batch_op.create_foreign_key(
            "fk_household_preferences_default_shopping_list",
            "shopping_lists",
            ["default_shopping_list_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.drop_constraint("fk_household_preferences_default_shopping_list", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_household_preferences_default_shopping_list_id"))
        batch_op.drop_column("default_shopping_list_id")
