"""add name_jp to ingredient foods

Revision ID: a1f4c2d9e8b3
Revises: a19c6d2e4f0b
Create Date: 2026-05-27 12:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1f4c2d9e8b3"
down_revision: str | None = "a19c6d2e4f0b"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    with op.batch_alter_table("ingredient_foods") as batch_op:
        batch_op.add_column(sa.Column("name_jp", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("name_jp_kanji", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("ingredient_foods") as batch_op:
        batch_op.drop_column("name_jp")
        batch_op.drop_column("name_jp_kanji")
