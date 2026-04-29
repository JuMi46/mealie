"""Add household preferences for unit display

Revision ID: 9f3b2a6c1d4e
Revises: abf60f8d604f
Create Date: 2026-04-28 12:10:00.000000

"""

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "9f3b2a6c1d4e"
down_revision: str | None = "abf60f8d604f"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("primary_volume_units", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
        )
        batch_op.add_column(
            sa.Column("secondary_volume_units", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
        )
        batch_op.add_column(sa.Column("primary_mass_units", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
        batch_op.add_column(
            sa.Column("secondary_mass_units", sa.JSON(), nullable=False, server_default=sa.text("'[]'"))
        )
        batch_op.add_column(
            sa.Column("volume_display_mode", sa.String(), nullable=False, server_default="primary_only")
        )
        batch_op.add_column(sa.Column("mass_display_mode", sa.String(), nullable=False, server_default="primary_only"))

    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.alter_column("primary_volume_units", server_default=None)
        batch_op.alter_column("secondary_volume_units", server_default=None)
        batch_op.alter_column("primary_mass_units", server_default=None)
        batch_op.alter_column("secondary_mass_units", server_default=None)
        batch_op.alter_column("volume_display_mode", server_default=None)
        batch_op.alter_column("mass_display_mode", server_default=None)


def downgrade():
    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.drop_column("mass_display_mode")
        batch_op.drop_column("volume_display_mode")
        batch_op.drop_column("secondary_mass_units")
        batch_op.drop_column("primary_mass_units")
        batch_op.drop_column("secondary_volume_units")
        batch_op.drop_column("primary_volume_units")
