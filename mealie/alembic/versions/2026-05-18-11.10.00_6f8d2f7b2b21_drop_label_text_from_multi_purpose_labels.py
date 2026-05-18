"""drop label_text from multi purpose labels

Revision ID: 6f8d2f7b2b21
Revises: 309cca289f9d
Create Date: 2026-05-18 11:10:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6f8d2f7b2b21"
down_revision: str | None = "309cca289f9d"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("multi_purpose_labels")}

    if "label_text" in columns:
        with op.batch_alter_table("multi_purpose_labels", schema=None) as batch_op:
            batch_op.drop_column("label_text")


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("multi_purpose_labels")}

    if "label_text" not in columns:
        with op.batch_alter_table("multi_purpose_labels", schema=None) as batch_op:
            batch_op.add_column(sa.Column("label_text", sa.String(), nullable=True))
