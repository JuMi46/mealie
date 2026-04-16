from pydantic import UUID4, ConfigDict

from mealie.schema._mealie import MealieModel


class RecipeInstructionTimer(MealieModel):
    id: UUID4
    duration: int
    text: str | None = None
    model_config = ConfigDict(from_attributes=True)
