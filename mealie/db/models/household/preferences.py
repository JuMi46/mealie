from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.ext.associationproxy import AssociationProxy, association_proxy
from sqlalchemy.orm import Mapped, mapped_column

from .._model_base import BaseMixins, SqlAlchemyBase
from .._model_utils.auto_init import auto_init
from .._model_utils.guid import GUID

if TYPE_CHECKING:
    from ..recipe.ingredient import IngredientFoodModel, IngredientUnitModel
    from ..recipe.recipe import RecipeModel
    from .household import Household


PRIMARY_VOLUME_UNITS = "primary_volume"
SECONDARY_VOLUME_UNITS = "secondary_volume"
PRIMARY_MASS_UNITS = "primary_mass"
SECONDARY_MASS_UNITS = "secondary_mass"


household_preferences_units = sa.Table(
    "household_preferences_units",
    SqlAlchemyBase.metadata,
    sa.Column("household_preferences_id", GUID, sa.ForeignKey("household_preferences.id"), primary_key=True),
    sa.Column("unit_id", GUID, sa.ForeignKey("ingredient_units.id"), primary_key=True),
    sa.Column("unit_preference_type", sa.String(length=32), primary_key=True),
    sa.CheckConstraint(
        "unit_preference_type IN ('primary_volume', 'secondary_volume', 'primary_mass', 'secondary_mass')",
        name="ck_household_preferences_units_preference_type",
    ),
)


class HouseholdPreferencesModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "household_preferences"
    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)

    household_id: Mapped[GUID | None] = mapped_column(GUID, sa.ForeignKey("households.id"), nullable=False, index=True)
    household: Mapped[Optional["Household"]] = orm.relationship("Household", back_populates="preferences")
    group_id: AssociationProxy[GUID] = association_proxy("household", "group_id")

    private_household: Mapped[bool | None] = mapped_column(sa.Boolean, default=True)
    show_announcements: Mapped[bool] = mapped_column(sa.Boolean, default=True)

    lock_recipe_edits_from_other_households: Mapped[bool | None] = mapped_column(sa.Boolean, default=True)
    first_day_of_week: Mapped[int | None] = mapped_column(sa.Integer, default=0)

    # Recipe Defaults
    recipe_public: Mapped[bool | None] = mapped_column(sa.Boolean, default=True)
    recipe_show_nutrition: Mapped[bool | None] = mapped_column(sa.Boolean, default=False)
    recipe_show_assets: Mapped[bool | None] = mapped_column(sa.Boolean, default=False)
    recipe_landscape_view: Mapped[bool | None] = mapped_column(sa.Boolean, default=False)
    recipe_disable_comments: Mapped[bool | None] = mapped_column(sa.Boolean, default=False)

    # Household unit display preferences
    primary_volume_units: Mapped[list["IngredientUnitModel"]] = orm.relationship(
        "IngredientUnitModel",
        secondary=household_preferences_units,
        primaryjoin=lambda: sa.and_(
            HouseholdPreferencesModel.id == household_preferences_units.c.household_preferences_id,
            household_preferences_units.c.unit_preference_type == PRIMARY_VOLUME_UNITS,
        ),
        viewonly=True,
        overlaps="secondary_volume_units,primary_mass_units,secondary_mass_units",
    )
    secondary_volume_units: Mapped[list["IngredientUnitModel"]] = orm.relationship(
        "IngredientUnitModel",
        secondary=household_preferences_units,
        primaryjoin=lambda: sa.and_(
            HouseholdPreferencesModel.id == household_preferences_units.c.household_preferences_id,
            household_preferences_units.c.unit_preference_type == SECONDARY_VOLUME_UNITS,
        ),
        viewonly=True,
        overlaps="primary_volume_units,primary_mass_units,secondary_mass_units",
    )
    primary_mass_units: Mapped[list["IngredientUnitModel"]] = orm.relationship(
        "IngredientUnitModel",
        secondary=household_preferences_units,
        primaryjoin=lambda: sa.and_(
            HouseholdPreferencesModel.id == household_preferences_units.c.household_preferences_id,
            household_preferences_units.c.unit_preference_type == PRIMARY_MASS_UNITS,
        ),
        viewonly=True,
        overlaps="primary_volume_units,secondary_volume_units,secondary_mass_units",
    )
    secondary_mass_units: Mapped[list["IngredientUnitModel"]] = orm.relationship(
        "IngredientUnitModel",
        secondary=household_preferences_units,
        primaryjoin=lambda: sa.and_(
            HouseholdPreferencesModel.id == household_preferences_units.c.household_preferences_id,
            household_preferences_units.c.unit_preference_type == SECONDARY_MASS_UNITS,
        ),
        viewonly=True,
        overlaps="primary_volume_units,secondary_volume_units,primary_mass_units",
    )
    food_substitutions: Mapped[list["HouseholdFoodSubstitutionModel"]] = orm.relationship(
        "HouseholdFoodSubstitutionModel",
        back_populates="household_preferences",
        cascade="all, delete, delete-orphan",
    )
    volume_display_mode: Mapped[str] = mapped_column(sa.String, nullable=False, default="primary_only")
    mass_display_mode: Mapped[str] = mapped_column(sa.String, nullable=False, default="primary_only")
    temperature_display_template: Mapped[str] = mapped_column(sa.String, nullable=False, default="℃ / ℉")

    # Deprecated
    recipe_disable_amount: Mapped[bool | None] = mapped_column(sa.Boolean, default=True)

    @auto_init()
    def __init__(self, **_) -> None:
        pass

    def _sync_unit_preferences(
        self,
        session: orm.Session,
        pref_type: str,
        raw_list: list,
    ) -> None:
        """Delete and re-insert join-table rows for one unit preference category."""
        unit_ids: list[str] = []
        for item in raw_list:
            if isinstance(item, dict):
                uid = item.get("id")
            elif hasattr(item, "id"):
                uid = str(item.id)
            else:
                uid = str(item) if item else None
            if uid:
                unit_ids.append(uid)

        session.execute(
            household_preferences_units.delete().where(
                sa.and_(
                    household_preferences_units.c.household_preferences_id == self.id,
                    household_preferences_units.c.unit_preference_type == pref_type,
                )
            )
        )
        if unit_ids:
            session.execute(
                household_preferences_units.insert(),
                [
                    {
                        "household_preferences_id": str(self.id),
                        "unit_id": uid,
                        "unit_preference_type": pref_type,
                    }
                    for uid in unit_ids
                ],
            )

    def _sync_food_substitutions(self, session: orm.Session, raw_list: list) -> None:
        from ..recipe.ingredient import IngredientFoodModel
        from ..recipe.recipe import RecipeModel

        rows: list[dict[str, object]] = []
        seen_source_food_ids: set[str] = set()

        for item in raw_list:
            if isinstance(item, dict):
                source_food_id = item.get("source_food_id")
                substitute_food_id = item.get("substitute_food_id")
                substitute_recipe_id = item.get("substitute_recipe_id")
                ratio = item.get("ratio", 1)
            else:
                source_food_id = getattr(item, "source_food_id", None)
                substitute_food_id = getattr(item, "substitute_food_id", None)
                substitute_recipe_id = getattr(item, "substitute_recipe_id", None)
                ratio = getattr(item, "ratio", 1)

            source_food_id = str(source_food_id) if source_food_id else None
            substitute_food_id = str(substitute_food_id) if substitute_food_id else None
            substitute_recipe_id = str(substitute_recipe_id) if substitute_recipe_id else None

            if not source_food_id or source_food_id in seen_source_food_ids:
                continue

            target_count = int(bool(substitute_food_id)) + int(bool(substitute_recipe_id))
            if target_count != 1:
                continue

            ratio = float(ratio) if ratio is not None else 1
            if ratio <= 0:
                continue

            seen_source_food_ids.add(source_food_id)
            rows.append(
                {
                    "household_preferences_id": str(self.id),
                    "source_food_id": source_food_id,
                    "substitute_food_id": substitute_food_id,
                    "substitute_recipe_id": substitute_recipe_id,
                    "ratio": ratio,
                }
            )

        if rows:
            source_food_ids = {row["source_food_id"] for row in rows}
            substitute_food_ids = {row["substitute_food_id"] for row in rows if row["substitute_food_id"]}
            all_food_ids = source_food_ids | substitute_food_ids
            valid_food_ids = {
                str(food_id)
                for food_id in session.execute(
                    sa.select(IngredientFoodModel.id).where(
                        IngredientFoodModel.group_id == self.group_id,
                        IngredientFoodModel.id.in_(all_food_ids),
                    )
                ).scalars()
            }

            if all_food_ids - valid_food_ids:
                raise ValueError("One or more food substitutions reference an invalid food")

            substitute_recipe_ids = {row["substitute_recipe_id"] for row in rows if row["substitute_recipe_id"]}
            if substitute_recipe_ids:
                valid_recipe_ids = {
                    str(recipe_id)
                    for recipe_id in session.execute(
                        sa.select(RecipeModel.id).where(
                            RecipeModel.group_id == self.group_id,
                            RecipeModel.id.in_(substitute_recipe_ids),
                        )
                    ).scalars()
                }

                if substitute_recipe_ids - valid_recipe_ids:
                    raise ValueError("One or more food substitutions reference an invalid recipe")

        session.execute(
            HouseholdFoodSubstitutionModel.__table__.delete().where(
                HouseholdFoodSubstitutionModel.household_preferences_id == self.id
            )
        )

        if rows:
            session.execute(HouseholdFoodSubstitutionModel.__table__.insert(), rows)

    def update(self, session: orm.Session, **kwargs) -> None:
        """Override to manually manage unit preference associations (viewonly relationships)."""
        _UNIT_PREF_MAP = {
            "primary_volume_units": PRIMARY_VOLUME_UNITS,
            "secondary_volume_units": SECONDARY_VOLUME_UNITS,
            "primary_mass_units": PRIMARY_MASS_UNITS,
            "secondary_mass_units": SECONDARY_MASS_UNITS,
        }

        # Separate managed relationship fields from the rest
        unit_prefs: dict[str, list] = {}
        food_substitutions: list = []
        has_food_substitutions = False
        other_kwargs: dict = {}
        for key, val in kwargs.items():
            if key in _UNIT_PREF_MAP:
                unit_prefs[key] = val if val is not None else []
            elif key == "food_substitutions":
                has_food_substitutions = True
                food_substitutions = val if val is not None else []
            else:
                other_kwargs[key] = val

        # Let auto_init handle all non-unit fields (viewonly rels are skipped automatically)
        self.__init__(session=session, **other_kwargs)

        # Handle empty-list clearing (BaseMixins.update does this, but we own the loop now)
        for key, val in other_kwargs.items():
            if hasattr(self, key) and val == []:
                setattr(self, key, val)

        # Manually sync unit preference join rows
        for field_name, pref_type in _UNIT_PREF_MAP.items():
            if field_name in unit_prefs:
                self._sync_unit_preferences(session, pref_type, unit_prefs[field_name])

        if has_food_substitutions:
            self._sync_food_substitutions(session, food_substitutions)


class HouseholdFoodSubstitutionModel(SqlAlchemyBase, BaseMixins):
    __tablename__ = "household_food_substitutions"
    __table_args__ = (
        sa.UniqueConstraint(
            "household_preferences_id",
            "source_food_id",
            name="uq_household_food_substitutions_pref_source",
        ),
        sa.CheckConstraint(
            "((substitute_food_id IS NOT NULL) AND (substitute_recipe_id IS NULL)) OR "
            "((substitute_food_id IS NULL) AND (substitute_recipe_id IS NOT NULL))",
            name="ck_household_food_substitutions_single_target",
        ),
        sa.CheckConstraint("ratio > 0", name="ck_household_food_substitutions_ratio_positive"),
    )

    id: Mapped[GUID] = mapped_column(GUID, primary_key=True, default=GUID.generate)
    household_preferences_id: Mapped[GUID] = mapped_column(
        GUID,
        sa.ForeignKey("household_preferences.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_food_id: Mapped[GUID] = mapped_column(GUID, sa.ForeignKey("ingredient_foods.id"), nullable=False, index=True)
    substitute_food_id: Mapped[GUID | None] = mapped_column(
        GUID,
        sa.ForeignKey("ingredient_foods.id"),
        nullable=True,
        index=True,
    )
    substitute_recipe_id: Mapped[GUID | None] = mapped_column(
        GUID,
        sa.ForeignKey("recipes.id"),
        nullable=True,
        index=True,
    )
    ratio: Mapped[float] = mapped_column(sa.Float, nullable=False, default=1)

    household_preferences: Mapped["HouseholdPreferencesModel"] = orm.relationship(
        "HouseholdPreferencesModel",
        back_populates="food_substitutions",
    )
    source_food: Mapped["IngredientFoodModel"] = orm.relationship(
        "IngredientFoodModel",
        foreign_keys=[source_food_id],
    )
    substitute_food: Mapped[Optional["IngredientFoodModel"]] = orm.relationship(
        "IngredientFoodModel",
        foreign_keys=[substitute_food_id],
    )
    substitute_recipe: Mapped[Optional["RecipeModel"]] = orm.relationship(
        "RecipeModel",
        foreign_keys=[substitute_recipe_id],
    )

    @auto_init()
    def __init__(self, **_) -> None:
        pass
