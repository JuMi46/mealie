import datetime

from pydantic import UUID4, ConfigDict

from mealie.schema._mealie import MealieModel


class CreateRecipeInstructionTimerActive(MealieModel):
    complete_time: datetime.datetime
    text: str | None = None
    recipe_id: UUID4 | None = None
    recipe_instruction_timer_id: UUID4 | None = None


class SaveRecipeInstructionTimerActive(CreateRecipeInstructionTimerActive):
    group_id: UUID4
    household_id: UUID4
    user_id: UUID4


class ReadRecipeInstructionTimerActive(SaveRecipeInstructionTimerActive):
    id: UUID4
    running: bool
    seconds_remaining: int
    model_config = ConfigDict(from_attributes=True)
