from uuid import UUID, uuid4

from pydantic import UUID4, ConfigDict, Field

from mealie.schema._mealie import MealieModel


class IngredientReferences(MealieModel):
    """
    A list of ingredient references.
    """

    reference_id: UUID4 | None = None
    model_config = ConfigDict(from_attributes=True)


class RecipeStep(MealieModel):
    id: UUID | None = Field(default_factory=uuid4)
    title: str | None = ""
    """The section title"""
    summary: str | None = ""
    """The header/summary of this single instruction (e.g. "Step 1")"""
    text: str
    """The actual instruction text"""

    timers: list[int] = []
    """List of timers for this step, in seconds"""
    ingredient_references: list[IngredientReferences] = []
    model_config = ConfigDict(from_attributes=True)
