from functools import cached_property

import orjson
import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import UUID4

from mealie.db.models.household.ingredient_food_label import HouseholdIngredientFoodLabel
from mealie.routes._base.base_controllers import BaseUserController
from mealie.routes._base.controller import controller
from mealie.routes._base.mixins import HttpRepo
from mealie.routes._base.routers import MealieCrudRoute
from mealie.schema import mapper
from mealie.schema.openai.general import OpenAIFoodTranslations
from mealie.schema.recipe.recipe_ingredient import (
    CreateIngredientFood,
    IngredientFood,
    IngredientFoodPagination,
    MergeFood,
    SaveIngredientFood,
    UpdateIngredientFood,
)
from mealie.schema.response.pagination import PaginationQuery
from mealie.schema.response.responses import ErrorResponse, SuccessResponse
from mealie.services.household_services.ingredient_food_labels import get_household_food_label_map
from mealie.services.openai.openai import OpenAICallContext, OpenAIService

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
                    session=self.session,
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

    @router.post("/translate-jp", response_model=SuccessResponse)
    async def translate_foods_jp(self):
        self.checks.can_organize()

        ai_settings = self.group.ai_provider_settings
        if not ai_settings or not ai_settings.ai_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.respond(message="AI is not enabled for this group"),
            )

        openai_service = OpenAIService(self.repos)
        provider = openai_service.default_provider
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=ErrorResponse.respond(message="No default AI provider configured"),
            )

        foods = self.repo.get_all(override=IngredientFood)
        target_foods = [food for food in foods if food.name and not (food.name_jp or "").strip()]

        if not target_foods:
            return SuccessResponse.respond("No foods required translation")

        source_food_names = list(dict.fromkeys(food.name.strip() for food in target_foods if food.name))
        prompt = openai_service.get_prompt("foods.translate-jp")

        try:
            response = await openai_service.get_response(
                prompt,
                orjson.dumps(source_food_names).decode("utf-8"),
                response_schema=OpenAIFoodTranslations,
                provider=provider,
                context=OpenAICallContext(
                    endpoint="/api/foods/translate-jp",
                    user_id=str(self.user.id),
                    household_id=str(self.user.household_id),
                    group_id=str(self.user.group_id),
                ),
            )
        except Exception as ex:
            self.logger.exception(ex)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=ErrorResponse.respond(message="Failed to translate foods with AI"),
            ) from ex

        if not response:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=ErrorResponse.respond(message="AI provider returned an empty response"),
            )

        translated_by_en = {
            item.en.strip().lower(): item for item in response.translations if item.en and item.jp and item.en.strip()
        }

        updates_by_id: dict[UUID4, dict[str, str]] = {}
        for food in target_foods:
            key = food.name.strip().lower()
            translated = translated_by_en.get(key)
            if not translated:
                continue

            jp = (translated.jp or "").strip()
            if not jp:
                continue

            updates_by_id[food.id] = {
                "name_jp": jp,
                "name_jp_kanji": (translated.jpKanji or "").strip(),
            }

        translated_count = 0
        if updates_by_id:
            model = self.repo.model
            stmt = sa.select(model).where(
                model.id.in_(list(updates_by_id.keys())),
                model.group_id == self.group_id,
            )
            db_foods = self.session.execute(stmt).scalars().all()

            for db_food in db_foods:
                update = updates_by_id.get(db_food.id)
                if not update:
                    continue
                db_food.name_jp = update["name_jp"]
                db_food.name_jp_kanji = update["name_jp_kanji"]
                translated_count += 1

            self.session.commit()

        return SuccessResponse.respond(f"Translated {translated_count} foods")

    @router.get("/{item_id}", response_model=IngredientFood)
    def get_one(self, item_id: UUID4):
        food = self.mixins.get_one(item_id)
        return self._apply_household_label_override([food])[0]

    @router.patch("/{item_id}", response_model=IngredientFood)
    def patch_one(self, item_id: UUID4, data: UpdateIngredientFood):
        self.checks.can_organize()

        should_set_override = "household_label_id" in data.model_fields_set
        if should_set_override:
            self._validate_household_label_override(data.household_label_id)

        patch_data = data.model_dump(exclude_unset=True, exclude_defaults=True)
        patch_data.pop("household_label_id", None)

        if patch_data:
            existing_food = self.mixins.get_one(item_id)
            merged_data = existing_food.model_dump()
            merged_data.update(patch_data)
            save_data = SaveIngredientFood.model_validate({**merged_data, "group_id": self.group_id})
            food = self.mixins.update_one(save_data, item_id)
        else:
            food = self.mixins.get_one(item_id)

        if should_set_override:
            self._set_household_label_override(item_id, data.household_label_id)

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
