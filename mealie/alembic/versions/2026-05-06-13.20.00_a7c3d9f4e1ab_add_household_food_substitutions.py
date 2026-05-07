"""Add household food substitutions

Revision ID: a7c3d9f4e1ab
Revises: f2a1c4e9b7d0
Create Date: 2026-05-06 13:20:00.000000

"""

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types


# revision identifiers, used by Alembic.
revision = "a7c3d9f4e1ab"
down_revision: str | None = "f2a1c4e9b7d0"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    op.create_table(
        "household_food_substitutions",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("household_preferences_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("source_food_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("substitute_food_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("substitute_recipe_id", mealie.db.migration_types.GUID(), nullable=True),
        sa.Column("ratio", sa.Float(), nullable=False, server_default="1"),
        sa.CheckConstraint(
            "((substitute_food_id IS NOT NULL) AND (substitute_recipe_id IS NULL)) OR "
            "((substitute_food_id IS NULL) AND (substitute_recipe_id IS NOT NULL))",
            name="ck_household_food_substitutions_single_target",
        ),
        sa.CheckConstraint("ratio > 0", name="ck_household_food_substitutions_ratio_positive"),
        sa.ForeignKeyConstraint(
            ["household_preferences_id"],
            ["household_preferences.id"],
            name="fk_household_food_substitutions_household_preferences_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_food_id"],
            ["ingredient_foods.id"],
            name="fk_household_food_substitutions_source_food_id",
        ),
        sa.ForeignKeyConstraint(
            ["substitute_food_id"],
            ["ingredient_foods.id"],
            name="fk_household_food_substitutions_substitute_food_id",
        ),
        sa.ForeignKeyConstraint(
            ["substitute_recipe_id"],
            ["recipes.id"],
            name="fk_household_food_substitutions_substitute_recipe_id",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "household_preferences_id",
            "source_food_id",
            name="uq_household_food_substitutions_pref_source",
        ),
    )

    with op.batch_alter_table("household_food_substitutions", schema=None) as batch_op:
        batch_op.create_index(
            "ix_household_food_substitutions_household_preferences_id",
            ["household_preferences_id"],
            unique=False,
        )
        batch_op.create_index("ix_household_food_substitutions_source_food_id", ["source_food_id"], unique=False)
        batch_op.create_index(
            "ix_household_food_substitutions_substitute_food_id",
            ["substitute_food_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_household_food_substitutions_substitute_recipe_id",
            ["substitute_recipe_id"],
            unique=False,
        )
        batch_op.alter_column("ratio", server_default=None)


def downgrade():
    with op.batch_alter_table("household_food_substitutions", schema=None) as batch_op:
        batch_op.drop_index("ix_household_food_substitutions_substitute_recipe_id")
        batch_op.drop_index("ix_household_food_substitutions_substitute_food_id")
        batch_op.drop_index("ix_household_food_substitutions_source_food_id")
        batch_op.drop_index("ix_household_food_substitutions_household_preferences_id")

    op.drop_table("household_food_substitutions")
