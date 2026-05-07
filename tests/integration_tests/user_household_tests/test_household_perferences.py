from fastapi.testclient import TestClient

from mealie.schema.household.household_preferences import UpdateHouseholdPreferences
from mealie.schema.recipe.recipe_ingredient import SaveIngredientFood
from tests.utils import api_routes
from tests.utils.assertion_helpers import assert_ignore_keys
from tests.utils.factories import random_bool, random_string
from tests.utils.fixture_schemas import TestUser


def test_get_preferences(api_client: TestClient, unique_user: TestUser) -> None:
    response = api_client.get(api_routes.households_preferences, headers=unique_user.token)
    assert response.status_code == 200

    preferences = response.json()

    assert preferences["recipePublic"] in {True, False}
    assert preferences["recipeShowNutrition"] in {True, False}


def test_preferences_in_household(api_client: TestClient, unique_user: TestUser) -> None:
    response = api_client.get(api_routes.households_self, headers=unique_user.token)

    assert response.status_code == 200

    household = response.json()

    assert household["preferences"] is not None

    # Spot Check
    assert household["preferences"]["recipePublic"] in {True, False}
    assert household["preferences"]["recipeShowNutrition"] in {True, False}


def test_update_preferences_no_permission(api_client: TestClient, user_tuple: list[TestUser]) -> None:
    unique_user, other_user = user_tuple

    user = other_user.repos.users.get_one(unique_user.user_id)
    assert user
    user.can_manage_household = False
    other_user.repos.users.update(user.id, user)

    new_data = UpdateHouseholdPreferences(recipe_public=random_bool(), recipe_show_nutrition=random_bool())
    response = api_client.put(api_routes.households_preferences, json=new_data.model_dump(), headers=unique_user.token)
    assert response.status_code == 403


def test_update_preferences(api_client: TestClient, user_tuple: list[TestUser]) -> None:
    unique_user, other_user = user_tuple

    user = other_user.repos.users.get_one(unique_user.user_id)
    assert user
    user.can_manage_household = True
    other_user.repos.users.update(user.id, user)

    new_data = UpdateHouseholdPreferences(recipe_public=random_bool(), recipe_show_nutrition=random_bool())
    response = api_client.put(api_routes.households_preferences, json=new_data.model_dump(), headers=unique_user.token)
    assert response.status_code == 200

    preferences = response.json()
    assert preferences is not None
    assert preferences["recipePublic"] == new_data.recipe_public
    assert preferences["recipeShowNutrition"] == new_data.recipe_show_nutrition
    assert_ignore_keys(new_data.model_dump(by_alias=True), preferences, ["id", "householdId"])


def test_food_substitutions_crud(api_client: TestClient, unique_user: TestUser) -> None:
    database = unique_user.repos

    # Ensure the user can manage the household
    user = database.users.get_one(unique_user.user_id)
    assert user
    user.can_manage_household = True
    database.users.update(user.id, user)

    # Create two foods in the group
    source_food = database.ingredient_foods.create(
        SaveIngredientFood(name=random_string(10), group_id=unique_user.group_id)
    )
    substitute_food = database.ingredient_foods.create(
        SaveIngredientFood(name=random_string(10), group_id=unique_user.group_id)
    )

    # Set a food substitution
    prefs_response = api_client.get(api_routes.households_preferences, headers=unique_user.token)
    assert prefs_response.status_code == 200
    existing_prefs = prefs_response.json()

    new_prefs = dict(existing_prefs)
    new_prefs["foodSubstitutions"] = [
        {
            "sourceFoodId": str(source_food.id),
            "substituteFoodId": str(substitute_food.id),
            "substituteRecipeId": None,
            "ratio": 0.5,
        }
    ]

    response = api_client.put(api_routes.households_preferences, json=new_prefs, headers=unique_user.token)
    assert response.status_code == 200

    saved_prefs = response.json()
    assert len(saved_prefs["foodSubstitutions"]) == 1
    sub = saved_prefs["foodSubstitutions"][0]
    assert sub["sourceFoodId"] == str(source_food.id)
    assert sub["substituteFood"]["id"] == str(substitute_food.id)
    assert sub["ratio"] == 0.5

    # Clear substitutions
    new_prefs["foodSubstitutions"] = []
    response = api_client.put(api_routes.households_preferences, json=new_prefs, headers=unique_user.token)
    assert response.status_code == 200
    assert response.json()["foodSubstitutions"] == []
