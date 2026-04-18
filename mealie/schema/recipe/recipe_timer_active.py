import datetime

from pydantic import UUID4, ConfigDict

from mealie.schema._mealie import MealieModel


class RecipeTimerActiveCreate(MealieModel):
    complete_time: datetime.datetime
    text: str | None = None


class RecipeTimerActiveSave(RecipeTimerActiveCreate):
    group_id: UUID4
    household_id: UUID4
    user_id: UUID4
    recipe_id: UUID4 | None = None
    recipe_timer_id: UUID4 | None = None


class RecipeTimerActive(RecipeTimerActiveSave):
    id: UUID4
    running: bool
    seconds_remaining: int
    model_config = ConfigDict(from_attributes=True)
