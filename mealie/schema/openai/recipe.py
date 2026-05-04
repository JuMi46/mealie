from pydantic import Field

from ._base import OpenAIBase


class OpenAIRecipeTimer(OpenAIBase):
    duration: int = Field(..., description="Timer duration in seconds.")
    text: str | None = Field(None, description="Short human-readable timer label.")


class OpenAIRecipeIngredientReference(OpenAIBase):
    reference_id: str | None = Field(
        None,
        description=(
            "Reference ID of an ingredient used in this instruction. "
            "Must match a referenceId from the ingredients list."
        ),
    )


class OpenAIRecipeIngredientWithQuantity(OpenAIBase):
    reference_id: str | None = Field(
        None,
        description="Reference ID of the ingredient being used. Must match a referenceId from the ingredients list.",
    )
    quantity: float | None = Field(None, description="Quantity of the ingredient used in this step.")
    quantity_in_ml: float | None = Field(None, description="Quantity converted to milliliters, if applicable.")
    unit_name: str | None = Field(None, description="Name of the unit used (e.g., 'cup', 'g', 'ml').")
    comment: str | None = Field(None, description="Additional comment about the usage of this ingredient in this step.")


class OpenAIRecipeIngredient(OpenAIBase):
    title: str | None = Field(
        None,
        description="Ingredient section title (e.g., 'Dry Ingredients'). Only set on the first item in each section.",
    )

    text: str = Field(
        ...,
        description="The complete ingredient text, e.g., '1 cup of flour' or '2 cups of onions, chopped'.",
    )

    reference_id: str | None = Field(
        None,
        description="Reference ID provided in the input for this ingredient. Return this value exactly unchanged.",
    )

    quantity: float | None = Field(None, description="Parsed numeric quantity from the ingredient text.")
    unit_name: str | None = Field(
        None, description="Unit name parsed from the ingredient text (e.g., 'cup', 'g', 'tbsp')."
    )
    food_name: str | None = Field(
        None, description="Food name parsed from the ingredient text (e.g., 'flour', 'butter', 'onion')."
    )
    note: str | None = Field(
        None,
        description="Additional preparation note from the ingredient text (e.g., 'chopped', 'at room temperature').",
    )
    quantity_in_ml: float | None = Field(
        None,
        description="The ingredient quantity converted to milliliters.",
    )


class OpenAIRecipeInstruction(OpenAIBase):
    title: str | None = Field(
        None,
        description="Instruction section title. Only set on the first step in each section.",
    )

    text: str = Field(
        ...,
        description=(
            "One instruction step. Do not include numeric prefixes like '1.' or 'Step 1', "
            "but do include word-based prefixes like 'First' or 'Second'."
        ),
    )

    id: str | None = Field(
        None,
        description="ID provided in the input for this instruction step. Return this value exactly unchanged.",
    )

    preparation_instruction_id: str | None = Field(
        None,
        description=(
            "ID of another instruction step that must be prepared before this one"
            "(e.g., a sauce referenced later). Must match an id from the instructions list."
        ),
    )

    ingredient_references: list[OpenAIRecipeIngredientReference] = Field(
        default_factory=list,
        description="Ingredient references used in this instruction step.",
    )

    ingredients_with_quantity: list[OpenAIRecipeIngredientWithQuantity] = Field(
        default_factory=list,
        description="Ingredients used in this specific step with their precise quantities.",
    )

    timers: list[OpenAIRecipeTimer] = Field(
        default_factory=list,
        description="Timers mentioned in this instruction step.",
    )


class OpenAIRecipeNotes(OpenAIBase):
    title: str | None = Field(
        None,
        description="Note title. Ignore generic titles like 'Note' or 'Info' and leave blank.",
    )

    text: str = Field(
        ...,
        description="The note content, such as tips, variations, or preparation advice.",
    )


class OpenAIRecipe(OpenAIBase):
    name: str = Field(
        ...,
        description="Recipe name or title. Make your best guess if not obvious.",
    )

    description: str | None = Field(
        None,
        description="A brief description of the recipe in a few words or sentences.",
    )

    recipe_yield: str | None = Field(
        None,
        description="Recipe yield, e.g., '12 cookies' or '4 servings'.",
    )

    total_time: str | None = Field(
        None,
        description="Total time as text (e.g., '1 hour 30 minutes'). Use if only one time is available.",
    )

    prep_time: str | None = Field(
        None,
        description="Prep time as text, e.g., '30 minutes'. Do not duplicate total_time.",
    )

    perform_time: str | None = Field(
        None,
        description="Cook/perform time as text, e.g., '1 hour'. Do not duplicate total_time.",
    )

    primary_unit_system: str | None = Field(
        None,
        description="Primary unit system used in the recipe, such as metric, US customary, or imperial.",
    )

    ingredients: list[OpenAIRecipeIngredient] = Field(
        default_factory=list,
        description="List of ingredients in order.",
    )

    instructions: list[OpenAIRecipeInstruction] = Field(
        default_factory=list,
        description="List of instruction steps in order.",
    )

    notes: list[OpenAIRecipeNotes] = Field(
        default_factory=list,
        description="List of notes, tips, or variations.",
    )
