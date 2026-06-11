"""Add category position and recommended side dishes

Revision ID: 8c1d2e4f9a3b
Revises: 5fff42642462
Create Date: 2026-06-08 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types

# revision identifiers, used by Alembic.
revision = "8c1d2e4f9a3b"
down_revision: str | None = "5fff42642462"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.add_column(sa.Column("position", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("position_recipe", sa.Integer(), nullable=False, server_default="0"))
        batch_op.create_index(batch_op.f("ix_categories_position"), ["position"], unique=False)
        batch_op.create_index(batch_op.f("ix_categories_position_recipe"), ["position_recipe"], unique=False)

    op.create_table(
        "recipes_to_recommended_side_dishes",
        sa.Column("recipe_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("recommended_recipe_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.ForeignKeyConstraint(["recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recommended_recipe_id"], ["recipes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("recipe_id", "recommended_recipe_id", name="recipe_id_recommended_recipe_id_key"),
    )
    with op.batch_alter_table("recipes_to_recommended_side_dishes", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_recipes_to_recommended_side_dishes_recipe_id"), ["recipe_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_recipes_to_recommended_side_dishes_recommended_recipe_id"),
            ["recommended_recipe_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("recipes_to_recommended_side_dishes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_recipes_to_recommended_side_dishes_recommended_recipe_id"))
        batch_op.drop_index(batch_op.f("ix_recipes_to_recommended_side_dishes_recipe_id"))

    op.drop_table("recipes_to_recommended_side_dishes")

    with op.batch_alter_table("categories", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_categories_position"))
        batch_op.drop_index(batch_op.f("ix_categories_position_recipe"))
        batch_op.drop_column("position")
        batch_op.drop_column("position_recipe")
