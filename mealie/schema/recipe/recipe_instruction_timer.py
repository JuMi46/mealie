from pydantic import UUID4, ConfigDict

from mealie.schema._mealie import MealieModel

from .recipe_instruction_timer_active import ReadRecipeInstructionTimerActive


class RecipeInstructionTimer(MealieModel):
    id: UUID4
    duration: int
    text: str | None = None
    recipe_instuction_timer_active: list["ReadRecipeInstructionTimerActive"] | None = []
    model_config = ConfigDict(from_attributes=True)
