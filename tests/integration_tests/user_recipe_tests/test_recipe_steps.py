import json
import random

from fastapi.testclient import TestClient

from mealie.schema.openai.recipe import (
    OpenAIRecipeInstructionTimerResult,
    OpenAIRecipeInstructionTimerStep,
    OpenAIRecipeTimer,
)
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_step import IngredientReferences
from mealie.schema.recipe.recipe_timer import RecipeTimer
from mealie.services.openai import OpenAIService
from tests.utils import api_routes, jsonify
from tests.utils.factories import random_int
from tests.utils.fixture_schemas import TestUser


def test_associate_ingredient_with_step(api_client: TestClient, unique_user: TestUser, random_recipe: Recipe):
    recipe: Recipe = random_recipe

    # Associate an ingredient with a step
    steps = {}  # key=step_id, value=ingredient_id

    for idx, step in enumerate(recipe.recipe_instructions or []):
        ingredients = random.choices(recipe.recipe_ingredient, k=2)

        step.ingredient_references = [
            IngredientReferences(reference_id=ingredient.reference_id) for ingredient in ingredients
        ]

        steps[idx] = [str(ingredient.reference_id) for ingredient in ingredients]

    response = api_client.put(
        api_routes.recipes_slug(recipe.slug),
        json=jsonify(recipe.model_dump()),
        headers=unique_user.token,
    )

    assert response.status_code == 200

    # Get Recipe and check that the ingredient is associated with the step

    response = api_client.get(api_routes.recipes_slug(recipe.slug), headers=unique_user.token)
    assert response.status_code == 200

    data: dict = json.loads(response.text)

    for idx, stp in enumerate(data.get("recipeInstructions") or []):
        all_refs = [ref["referenceId"] for ref in stp.get("ingredientReferences")]

        assert len(all_refs) == 2

        assert all(ref in steps[idx] for ref in all_refs)


def test_timers_crud(api_client: TestClient, unique_user: TestUser, random_recipe: Recipe):
    recipe = random_recipe
    assert recipe.recipe_instructions

    step_idx = random.randint(0, len(recipe.recipe_instructions) - 1)
    recipe.recipe_instructions[step_idx].timers = [
        RecipeTimer(duration=random_int(), text="") for _ in range(random_int(2, 5))
    ]

    response = api_client.put(
        api_routes.recipes_slug(recipe.slug),
        json=jsonify(recipe.model_dump()),
        headers=unique_user.token,
    )
    assert response.status_code == 200
    # Check that timers were updated (compare durations since ids will be generated)
    response_timers = response.json()["recipeInstructions"][step_idx]["timers"]
    expected_timers = recipe.recipe_instructions[step_idx].timers
    assert len(response_timers) == len(expected_timers)
    for response_timer, expected_timer in zip(response_timers, expected_timers, strict=False):
        assert response_timer["duration"] == expected_timer.duration
        assert response_timer["text"] == expected_timer.text


def test_parse_instruction_timers_for_recipe_without_save(
    api_client: TestClient,
    unique_user: TestUser,
    random_recipe: Recipe,
):
    recipe = random_recipe

    response_before = api_client.get(api_routes.recipes_slug(recipe.slug), headers=unique_user.token)
    assert response_before.status_code == 200
    before_data = response_before.json()

    assert before_data["recipeInstructions"]
    step_index = 0
    before_timer_count = len(before_data["recipeInstructions"][step_index]["timers"])

    response_parse = api_client.post(
        f"/api/recipes/{recipe.slug}/parse-instruction-timers",
        json={"steps": [{"index": step_index, "text": "Simmer for 5 minutes and rest for 1 hour."}]},
        headers=unique_user.token,
    )

    assert response_parse.status_code == 200
    parsed_data = response_parse.json()
    assert parsed_data["steps"]
    assert parsed_data["steps"][0]["index"] == step_index
    parsed_durations = [timer["duration"] for timer in parsed_data["steps"][0]["timers"]]
    assert 300 in parsed_durations
    assert 3600 in parsed_durations

    response_after = api_client.get(api_routes.recipes_slug(recipe.slug), headers=unique_user.token)
    assert response_after.status_code == 200
    after_data = response_after.json()
    after_timer_count = len(after_data["recipeInstructions"][step_index]["timers"])

    # Endpoint parses from provided text only and does not persist recipe timers.
    assert after_timer_count == before_timer_count


def test_parse_instructions_with_ai_for_recipe_without_save(
    api_client: TestClient,
    unique_user: TestUser,
    random_recipe: Recipe,
    monkeypatch,
):
    recipe = random_recipe

    async def mock_get_response(
        _self, _prompt, _message, *_args, **_kwargs
    ) -> OpenAIRecipeInstructionTimerResult | None:
        return OpenAIRecipeInstructionTimerResult(
            instructions=[
                OpenAIRecipeInstructionTimerStep(
                    id=None,
                    text="Bake at 180 C / 356 F for 5 minutes.",
                    timers=[OpenAIRecipeTimer(duration=300, text="Bake")],
                )
            ]
        )

    monkeypatch.setattr(OpenAIService, "get_response", mock_get_response)

    response_before = api_client.get(api_routes.recipes_slug(recipe.slug), headers=unique_user.token)
    assert response_before.status_code == 200
    before_data = response_before.json()

    assert before_data["recipeInstructions"]
    before_step = before_data["recipeInstructions"][0]
    before_timer_count = len(before_step["timers"])
    before_text = before_step["text"]

    response_parse = api_client.post(
        api_routes.recipes_slug_parse_instructions_with_ai(recipe.slug),
        json={
            "primaryUnitSystem": before_data.get("primaryUnitSystem"),
            "orgURL": before_data.get("orgURL"),
            "instructions": [
                {
                    "id": before_step.get("id"),
                    "text": "Bake at 350 degrees for 5 minutes.",
                    "timers": [],
                }
            ],
        },
        headers=unique_user.token,
    )

    assert response_parse.status_code == 200
    parsed_data = response_parse.json()
    assert parsed_data["instructions"]
    assert parsed_data["instructions"][0]["text"] == "Bake at 180 C / 356 F for 5 minutes."
    assert parsed_data["instructions"][0]["timers"][0]["duration"] == 300
    assert parsed_data["instructions"][0]["timers"][0]["text"] == "Bake"

    response_after = api_client.get(api_routes.recipes_slug(recipe.slug), headers=unique_user.token)
    assert response_after.status_code == 200
    after_data = response_after.json()
    after_step = after_data["recipeInstructions"][0]

    # Endpoint does not persist instruction text or timers.
    assert len(after_step["timers"]) == before_timer_count
    assert after_step["text"] == before_text
