from typing import Literal

from pydantic import UUID4, ConfigDict, Field, model_validator
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.interfaces import LoaderOption

from mealie.db.models.household.household import Household
from mealie.db.models.household.preferences import HouseholdFoodSubstitutionModel, HouseholdPreferencesModel
from mealie.db.models.recipe.recipe import RecipeModel
from mealie.schema._mealie import MealieModel
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_ingredient import IngredientFood, IngredientUnit


class HouseholdFoodSubstitutionBase(MealieModel):
    source_food_id: UUID4
    substitute_food_id: UUID4 | None = None
    substitute_recipe_id: UUID4 | None = None
    ratio: float = Field(default=1, gt=0)

    @model_validator(mode="after")
    def validate_target(self):
        target_count = int(bool(self.substitute_food_id)) + int(bool(self.substitute_recipe_id))
        if target_count != 1:
            raise ValueError("Exactly one substitute target must be set")

        return self


class UpdateHouseholdFoodSubstitution(HouseholdFoodSubstitutionBase):
    id: UUID4 | None = None


class ReadHouseholdFoodSubstitution(HouseholdFoodSubstitutionBase):
    id: UUID4
    source_food: IngredientFood
    substitute_food: IngredientFood | None = None
    substitute_recipe: Recipe | None = None

    model_config = ConfigDict(from_attributes=True)


class HouseholdPreferencesBase(MealieModel):
    private_household: bool = True
    show_announcements: bool = True

    lock_recipe_edits_from_other_households: bool = True
    first_day_of_week: int = 0

    # Recipe Defaults
    recipe_public: bool = True
    recipe_show_nutrition: bool = False
    recipe_show_assets: bool = False
    recipe_landscape_view: bool = False
    recipe_disable_comments: bool = False

    volume_display_mode: Literal["primary_only", "secondary_only", "both"] = "primary_only"
    mass_display_mode: Literal["primary_only", "secondary_only", "both"] = "primary_only"
    temperature_display_template: str = "℃ / ℉"


class UpdateHouseholdPreferences(HouseholdPreferencesBase):
    primary_volume_units: list[str] = Field(default_factory=list)
    secondary_volume_units: list[str] = Field(default_factory=list)
    primary_mass_units: list[str] = Field(default_factory=list)
    secondary_mass_units: list[str] = Field(default_factory=list)
    food_substitutions: list[UpdateHouseholdFoodSubstitution] = Field(default_factory=list)


class CreateHouseholdPreferences(UpdateHouseholdPreferences): ...


class SaveHouseholdPreferences(UpdateHouseholdPreferences):
    household_id: UUID4


class ReadHouseholdPreferences(HouseholdPreferencesBase):
    primary_volume_units: list[IngredientUnit] = Field(default_factory=list)
    secondary_volume_units: list[IngredientUnit] = Field(default_factory=list)
    primary_mass_units: list[IngredientUnit] = Field(default_factory=list)
    secondary_mass_units: list[IngredientUnit] = Field(default_factory=list)
    food_substitutions: list[ReadHouseholdFoodSubstitution] = Field(default_factory=list)

    id: UUID4
    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def loader_options(cls) -> list[LoaderOption]:
        return [
            joinedload(HouseholdPreferencesModel.household).load_only(Household.group_id),
            joinedload(HouseholdPreferencesModel.primary_volume_units),
            joinedload(HouseholdPreferencesModel.secondary_volume_units),
            joinedload(HouseholdPreferencesModel.primary_mass_units),
            joinedload(HouseholdPreferencesModel.secondary_mass_units),
            joinedload(HouseholdPreferencesModel.food_substitutions).joinedload(
                HouseholdFoodSubstitutionModel.source_food
            ),
            joinedload(HouseholdPreferencesModel.food_substitutions).joinedload(
                HouseholdFoodSubstitutionModel.substitute_food
            ),
            joinedload(HouseholdPreferencesModel.food_substitutions)
            .joinedload(HouseholdFoodSubstitutionModel.substitute_recipe)
            .load_only(RecipeModel.id, RecipeModel.slug, RecipeModel.name),
        ]
