"""add recipe yield unit

Revision ID: f8a2b4c6d8e0
Revises: d1f7a9c2b4e6
Create Date: 2026-05-16 10:30:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "f8a2b4c6d8e0"
down_revision: str | None = "d1f7a9c2b4e6"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    with op.batch_alter_table("recipes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("recipe_yield_unit_id", mealie.db.migration_types.GUID(), nullable=True))
        batch_op.create_index(batch_op.f("ix_recipes_recipe_yield_unit_id"), ["recipe_yield_unit_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_recipes_recipe_yield_unit",
            "ingredient_units",
            ["recipe_yield_unit_id"],
            ["id"],
            ondelete="SET NULL",
        )


def downgrade():
    with op.batch_alter_table("recipes", schema=None) as batch_op:
        batch_op.drop_constraint("fk_recipes_recipe_yield_unit", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_recipes_recipe_yield_unit_id"))
        batch_op.drop_column("recipe_yield_unit_id")
