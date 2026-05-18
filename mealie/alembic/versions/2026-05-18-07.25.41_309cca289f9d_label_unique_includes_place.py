"""'label unique includes place'

Revision ID: 309cca289f9d
Revises: f8a2b4c6d8e0
Create Date: 2026-05-18 07:25:41.776014

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "309cca289f9d"
down_revision: str | None = "f8a2b4c6d8e0"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {uc["name"] for uc in inspector.get_unique_constraints("multi_purpose_labels")}

    with op.batch_alter_table("multi_purpose_labels", schema=None) as batch_op:
        if "multi_purpose_labels_name_group_id_key" in existing:
            batch_op.drop_constraint("multi_purpose_labels_name_group_id_key", type_="unique")
        if "multi_purpose_labels_name_place_group_id_key" not in existing:
            batch_op.create_unique_constraint(
                "multi_purpose_labels_name_place_group_id_key",
                ["name", "place", "group_id"],
            )


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = {uc["name"] for uc in inspector.get_unique_constraints("multi_purpose_labels")}

    with op.batch_alter_table("multi_purpose_labels", schema=None) as batch_op:
        if "multi_purpose_labels_name_place_group_id_key" in existing:
            batch_op.drop_constraint("multi_purpose_labels_name_place_group_id_key", type_="unique")
        if "multi_purpose_labels_name_group_id_key" not in existing:
            batch_op.create_unique_constraint(
                "multi_purpose_labels_name_group_id_key",
                ["name", "group_id"],
            )
