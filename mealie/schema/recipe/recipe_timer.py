from pydantic import UUID4, ConfigDict

from mealie.schema._mealie import MealieModel

from .recipe_timer_active import RecipeTimerActive


class RecipeTimer(MealieModel):
    id: UUID4
    duration: int
    text: str | None = None
    recipe_timer_active: list["RecipeTimerActive"] | None = []
    model_config = ConfigDict(from_attributes=True)
