from functools import cached_property

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4

from mealie.db.models.household.ingredient_food_label import HouseholdIngredientFoodLabel
from mealie.routes._base.base_controllers import BaseUserController
from mealie.routes._base.controller import controller
from mealie.routes._base.mixins import HttpRepo
from mealie.routes._base.routers import MealieCrudRoute
from mealie.schema import mapper
from mealie.schema.recipe.recipe_ingredient import (
    CreateIngredientFood,
    IngredientFood,
    IngredientFoodPagination,
    MergeFood,
    SaveIngredientFood,
)
from mealie.schema.response.pagination import PaginationQuery
from mealie.schema.response.responses import SuccessResponse
from mealie.services.household_services.ingredient_food_labels import get_household_food_label_map

router = APIRouter(prefix="/foods", tags=["Recipes: Foods"], route_class=MealieCrudRoute)


@controller(router)
class IngredientFoodsController(BaseUserController):
    @cached_property
    def repo(self):
        return self.repos.ingredient_foods

    @cached_property
    def mixins(self):
        return HttpRepo[SaveIngredientFood, IngredientFood, CreateIngredientFood](
            self.repo,
            self.logger,
            self.registered_exceptions,
        )

    def _apply_household_label_override(self, foods: list[IngredientFood]) -> list[IngredientFood]:
        label_map = get_household_food_label_map(
            self.session,
            self.household_id,
            [food.id for food in foods],
        )
        for food in foods:
            override_label = label_map.get(food.id)
            food.household_label_id = override_label.id if override_label else None
        return foods

    def _set_household_label_override(self, food_id: UUID4, household_label_id: UUID4 | None) -> None:
        if self.household_id is None:
            return

        stmt = sa.select(HouseholdIngredientFoodLabel).where(
            HouseholdIngredientFoodLabel.household_id == self.household_id,
            HouseholdIngredientFoodLabel.food_id == food_id,
        )
        existing = self.session.execute(stmt).scalars().one_or_none()
        if household_label_id is None:
            if existing:
                self.session.delete(existing)
                self.session.commit()
            return

        if existing:
            existing.label_id = household_label_id
        else:
            self.session.add(
                HouseholdIngredientFoodLabel(
                    household_id=self.household_id,
                    food_id=food_id,
                    label_id=household_label_id,
                )
            )
        self.session.commit()

    def _validate_household_label_override(self, household_label_id: UUID4 | None) -> None:
        if household_label_id is None:
            return

        label = self.repos.group_multi_purpose_labels.get_one(household_label_id)
        if label is None:
            raise HTTPException(status_code=400, detail="invalid household label override")

    @router.get("", response_model=IngredientFoodPagination)
    def get_all(self, q: PaginationQuery = Depends(PaginationQuery), search: str | None = None):
        response = self.repo.page_all(
            pagination=q,
            override=IngredientFood,
            search=search,
        )
        response.items = self._apply_household_label_override(response.items)

        response.set_pagination_guides(router.url_path_for("get_all"), q.model_dump())
        return response

    @router.post("", response_model=IngredientFood, status_code=201)
    def create_one(self, data: CreateIngredientFood):
        self.checks.can_organize()
        should_set_override = "household_label_id" in data.model_fields_set
        if should_set_override:
            self._validate_household_label_override(data.household_label_id)
        save_data = mapper.cast(data, SaveIngredientFood, group_id=self.group_id)
        food = self.mixins.create_one(save_data)
        if should_set_override:
            self._set_household_label_override(food.id, data.household_label_id)
        return self._apply_household_label_override([food])[0]

    @router.put("/merge", response_model=SuccessResponse)
    def merge_one(self, data: MergeFood):
        self.checks.can_organize()
        try:
            self.repo.merge(data.from_food, data.to_food)
            return SuccessResponse.respond("Successfully merged foods")
        except Exception as e:
            self.logger.error(e)
            raise HTTPException(500, "Failed to merge foods") from e

    @router.get("/{item_id}", response_model=IngredientFood)
    def get_one(self, item_id: UUID4):
        food = self.mixins.get_one(item_id)
        return self._apply_household_label_override([food])[0]

    @router.put("/{item_id}", response_model=IngredientFood)
    def update_one(self, item_id: UUID4, data: CreateIngredientFood):
        self.checks.can_organize()
        should_set_override = "household_label_id" in data.model_fields_set
        if should_set_override:
            self._validate_household_label_override(data.household_label_id)
        data = mapper.cast(data, SaveIngredientFood, group_id=self.group_id)
        food = self.mixins.update_one(data, item_id)
        if should_set_override:
            self._set_household_label_override(food.id, data.household_label_id)
        return self._apply_household_label_override([food])[0]

    @router.delete("/{item_id}", response_model=IngredientFood)
    def delete_one(self, item_id: UUID4):
        self.checks.can_organize()
        return self.mixins.delete_one(item_id)
