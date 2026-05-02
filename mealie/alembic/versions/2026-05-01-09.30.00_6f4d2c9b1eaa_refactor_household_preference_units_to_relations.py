"""Refactor household preference units to relational pointers

Revision ID: 6f4d2c9b1eaa
Revises: 9f3b2a6c1d4e
Create Date: 2026-05-01 09:30:00.000000

"""

import json

import sqlalchemy as sa
from alembic import op

import mealie.db.migration_types


# revision identifiers, used by Alembic.
revision = "6f4d2c9b1eaa"
down_revision: str | None = "9f3b2a6c1d4e"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

PRIMARY_VOLUME_UNITS = "primary_volume"
SECONDARY_VOLUME_UNITS = "secondary_volume"
PRIMARY_MASS_UNITS = "primary_mass"
SECONDARY_MASS_UNITS = "secondary_mass"


def _to_list(raw: object) -> list[str]:
    if raw is None:
        return []

    if isinstance(raw, list):
        return [str(v) for v in raw if v is not None]

    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError:
            return []

        if isinstance(loaded, list):
            return [str(v) for v in loaded if v is not None]

    return []


def upgrade():
    op.create_table(
        "household_preferences_units",
        sa.Column(
            "household_preferences_id",
            mealie.db.migration_types.GUID(),
            sa.ForeignKey("household_preferences.id"),
            nullable=False,
        ),
        sa.Column("unit_id", mealie.db.migration_types.GUID(), sa.ForeignKey("ingredient_units.id"), nullable=False),
        sa.Column("unit_preference_type", sa.String(length=32), nullable=False),
        sa.CheckConstraint(
            "unit_preference_type IN ('primary_volume', 'secondary_volume', 'primary_mass', 'secondary_mass')",
            name="ck_household_preferences_units_preference_type",
        ),
        sa.PrimaryKeyConstraint("household_preferences_id", "unit_id", "unit_preference_type"),
    )

    bind = op.get_bind()
    metadata = sa.MetaData()

    household_preferences = sa.Table("household_preferences", metadata, autoload_with=bind)
    households = sa.Table("households", metadata, autoload_with=bind)
    ingredient_units = sa.Table("ingredient_units", metadata, autoload_with=bind)
    preferences_units = sa.Table("household_preferences_units", metadata, autoload_with=bind)

    unit_rows = (
        bind.execute(sa.select(ingredient_units.c.id, ingredient_units.c.group_id, ingredient_units.c.name))
        .mappings()
        .all()
    )

    unit_id_map = {str(row["id"]): row["id"] for row in unit_rows}
    unit_name_map = {(str(row["group_id"]), row["name"]): row["id"] for row in unit_rows if row["name"]}

    pref_rows = (
        bind.execute(
            sa.select(
                household_preferences.c.id,
                household_preferences.c.primary_volume_units,
                household_preferences.c.secondary_volume_units,
                household_preferences.c.primary_mass_units,
                household_preferences.c.secondary_mass_units,
                households.c.group_id,
            ).select_from(
                household_preferences.join(households, household_preferences.c.household_id == households.c.id)
            )
        )
        .mappings()
        .all()
    )

    mapping = [
        ("primary_volume_units", PRIMARY_VOLUME_UNITS),
        ("secondary_volume_units", SECONDARY_VOLUME_UNITS),
        ("primary_mass_units", PRIMARY_MASS_UNITS),
        ("secondary_mass_units", SECONDARY_MASS_UNITS),
    ]

    rows: list[dict[str, object]] = []

    for pref in pref_rows:
        group_id = str(pref["group_id"])

        for field_name, preference_type in mapping:
            values = _to_list(pref[field_name])
            seen: set[str] = set()

            for value in values:
                unit_id = unit_id_map.get(value) or unit_name_map.get((group_id, value))
                if not unit_id:
                    continue

                unit_id_str = str(unit_id)
                if unit_id_str in seen:
                    continue

                seen.add(unit_id_str)
                rows.append(
                    {
                        "household_preferences_id": pref["id"],
                        "unit_id": unit_id,
                        "unit_preference_type": preference_type,
                    }
                )

    if rows:
        op.bulk_insert(preferences_units, rows)

    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.drop_column("primary_volume_units")
        batch_op.drop_column("secondary_volume_units")
        batch_op.drop_column("primary_mass_units")
        batch_op.drop_column("secondary_mass_units")


def downgrade():
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

    bind = op.get_bind()
    metadata = sa.MetaData()

    household_preferences = sa.Table("household_preferences", metadata, autoload_with=bind)
    preferences_units = sa.Table("household_preferences_units", metadata, autoload_with=bind)

    pref_ids = bind.execute(sa.select(household_preferences.c.id)).scalars().all()
    updates = {
        pref_id: {
            "primary_volume_units": [],
            "secondary_volume_units": [],
            "primary_mass_units": [],
            "secondary_mass_units": [],
        }
        for pref_id in pref_ids
    }

    for pref_id, unit_id, preference_type in bind.execute(
        sa.select(
            preferences_units.c.household_preferences_id,
            preferences_units.c.unit_id,
            preferences_units.c.unit_preference_type,
        )
    ):
        if preference_type == PRIMARY_VOLUME_UNITS:
            updates[pref_id]["primary_volume_units"].append(str(unit_id))
        elif preference_type == SECONDARY_VOLUME_UNITS:
            updates[pref_id]["secondary_volume_units"].append(str(unit_id))
        elif preference_type == PRIMARY_MASS_UNITS:
            updates[pref_id]["primary_mass_units"].append(str(unit_id))
        elif preference_type == SECONDARY_MASS_UNITS:
            updates[pref_id]["secondary_mass_units"].append(str(unit_id))

    for pref_id, values in updates.items():
        bind.execute(household_preferences.update().where(household_preferences.c.id == pref_id).values(**values))

    with op.batch_alter_table("household_preferences", schema=None) as batch_op:
        batch_op.alter_column("primary_volume_units", server_default=None)
        batch_op.alter_column("secondary_volume_units", server_default=None)
        batch_op.alter_column("primary_mass_units", server_default=None)
        batch_op.alter_column("secondary_mass_units", server_default=None)

    op.drop_table("household_preferences_units")
