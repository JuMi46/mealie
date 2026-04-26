import json
import random

from fastapi.testclient import TestClient

from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_step import IngredientReferences
from mealie.schema.recipe.recipe_timer import RecipeTimer
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
