import datetime

from pydantic import UUID4, ConfigDict

from mealie.schema._mealie import MealieModel


class RecipeTimerActiveCreate(MealieModel):
    complete_time: datetime.datetime
    text: str | None = None
    recipe_link: str | None = None


class RecipeTimerActiveUpdate(MealieModel):
    complete_time: datetime.datetime


class RecipeTimerActiveDelete(MealieModel):
    recipe_link: str | None = None


class RecipeTimerActiveSave(MealieModel):
    complete_time: datetime.datetime
    text: str | None = None
    group_id: UUID4
    household_id: UUID4
    user_id: UUID4
    recipe_id: UUID4 | None = None
    recipe_timer_id: UUID4 | None = None


class RecipeTimerActive(RecipeTimerActiveSave):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)
