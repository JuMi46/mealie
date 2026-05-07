from collections.abc import Collection

from pydantic import UUID4
from sqlalchemy import select

from mealie.db.models.household.household import Household
from mealie.db.models.household.preferences import HouseholdPreferencesModel
from mealie.db.models.recipe.ingredient import IngredientFoodModel
from mealie.schema.recipe.recipe_ingredient import IngredientFood

from .repository_generic import GroupRepositoryGeneric


class RepositoryFood(GroupRepositoryGeneric[IngredientFood, IngredientFoodModel]):
    def _get_food(self, id: UUID4) -> IngredientFoodModel:
        stmt = select(self.model).filter_by(**self._filter_builder(**{"id": id}))
        return self.session.execute(stmt).scalars().one()

    def merge(self, from_food: UUID4, to_food: UUID4) -> IngredientFood | None:
        from_model = self._get_food(from_food)
        to_model = self._get_food(to_food)

        to_model.ingredients += from_model.ingredients

        try:
            self.session.delete(from_model)
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

        return self.get_one(to_food)

    def get_household_name_overrides(
        self, household_id: UUID4, food_ids: Collection[UUID4] | None = None
    ) -> dict[str, str]:
        stmt = (
            select(HouseholdPreferencesModel.ingredient_food_name_overrides)
            .join(Household, Household.id == HouseholdPreferencesModel.household_id)
            .where(HouseholdPreferencesModel.household_id == household_id)
        )

        if self.group_id:
            stmt = stmt.where(Household.group_id == self.group_id)

        overrides = self.session.execute(stmt).scalar_one_or_none() or {}
        if not overrides:
            return {}

        if not food_ids:
            return overrides

        food_id_set = {str(food_id) for food_id in food_ids}
        return {food_id: name for food_id, name in overrides.items() if food_id in food_id_set}

    def set_household_name_override(self, food_id: UUID4, household_id: UUID4, name: str | None) -> None:
        stmt = (
            select(HouseholdPreferencesModel)
            .join(Household, Household.id == HouseholdPreferencesModel.household_id)
            .where(HouseholdPreferencesModel.household_id == household_id)
        )
        if self.group_id:
            stmt = stmt.where(Household.group_id == self.group_id)

        preferences = self.session.execute(stmt).scalar_one_or_none()
        if not preferences:
            return

        overrides = dict(preferences.ingredient_food_name_overrides or {})
        food_key = str(food_id)
        if name:
            overrides[food_key] = name
        else:
            overrides.pop(food_key, None)

        preferences.ingredient_food_name_overrides = overrides
        self.session.commit()

    def hydrate_household_name_overrides(self, foods: list[IngredientFood], household_id: UUID4, replace: bool) -> None:
        """Populate household override metadata and optionally replace display names.

        Set `replace=True` for responses that should show overridden ingredient names
        (e.g. recipe and shopping list payloads). Set `replace=False` when the original
        group-level food names must stay visible while still exposing the household
        override value (e.g. food data-management UI).
        """
        if not foods:
            return

        food_ids = [food.id for food in foods if food.id]
        if not food_ids:
            return

        overrides = self.get_household_name_overrides(household_id, food_ids)
        for food in foods:
            override = overrides.get(str(food.id))
            food.household_override_name = override
            if override and replace:
                food.name = override
                food.plural_name = override
