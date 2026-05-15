"""add household food label overrides

Revision ID: d1f7a9c2b4e6
Revises: 3a7f5d2c9e11
Create Date: 2026-05-07 03:05:00.000000

"""

import sqlalchemy as sa

import mealie.db.migration_types
from alembic import op

# revision identifiers, used by Alembic.
revision = "d1f7a9c2b4e6"
down_revision: str | None = "3a7f5d2c9e11"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    op.create_table(
        "households_to_ingredient_food_labels",
        sa.Column("id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("household_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("food_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("label_id", mealie.db.migration_types.GUID(), nullable=False),
        sa.Column("created_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.Column("update_at", mealie.db.migration_types.NaiveDateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["food_id"],
            ["ingredient_foods.id"],
        ),
        sa.ForeignKeyConstraint(
            ["household_id"],
            ["households.id"],
        ),
        sa.ForeignKeyConstraint(
            ["label_id"],
            ["multi_purpose_labels.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("household_id", "food_id", name="household_id_food_id_label_key"),
    )
    with op.batch_alter_table("households_to_ingredient_food_labels", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_households_to_ingredient_food_labels_food_id"), ["food_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_households_to_ingredient_food_labels_household_id"), ["household_id"], unique=False
        )
        batch_op.create_index(
            batch_op.f("ix_households_to_ingredient_food_labels_label_id"), ["label_id"], unique=False
        )


def downgrade():
    with op.batch_alter_table("households_to_ingredient_food_labels", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_households_to_ingredient_food_labels_label_id"))
        batch_op.drop_index(batch_op.f("ix_households_to_ingredient_food_labels_household_id"))
        batch_op.drop_index(batch_op.f("ix_households_to_ingredient_food_labels_food_id"))

    op.drop_table("households_to_ingredient_food_labels")
