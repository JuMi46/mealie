from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from mealie.db.models.household.ingredient_food_label import HouseholdIngredientFoodLabel
from mealie.schema.recipe.recipe import Recipe
from mealie.schema.recipe.recipe_ingredient import RecipeIngredient
from mealie.schema.recipe.recipe_ingredient import CreateIngredientFood
from tests import utils
from tests.utils import api_routes
from tests.utils.factories import random_string
from tests.utils.fixture_schemas import TestUser


@pytest.fixture(scope="function")
def food(api_client: TestClient, unique_user: TestUser) -> Generator[dict, None, None]:
    data = CreateIngredientFood(
        name=random_string(10),
        description=random_string(10),
    ).model_dump(by_alias=True)

    response = api_client.post(api_routes.foods, json=data, headers=unique_user.token)

    assert response.status_code == 201

    yield response.json()

    response = api_client.delete(api_routes.foods_item_id(response.json()["id"]), headers=unique_user.token)


def test_create_food(api_client: TestClient, unique_user: TestUser):
    data = CreateIngredientFood(
        name=random_string(10),
        description=random_string(10),
    ).model_dump(by_alias=True)

    response = api_client.post(api_routes.foods, json=data, headers=unique_user.token)
    assert response.status_code == 201


def test_read_food(api_client: TestClient, food: dict, unique_user: TestUser):
    response = api_client.get(api_routes.foods_item_id(food["id"]), headers=unique_user.token)
    assert response.status_code == 200

    as_json = response.json()

    assert as_json["id"] == food["id"]
    assert as_json["name"] == food["name"]
    assert as_json["description"] == food["description"]


def test_update_food(api_client: TestClient, food: dict, unique_user: TestUser):
    update_data = {
        "id": food["id"],
        "name": random_string(10),
        "description": random_string(10),
    }
    response = api_client.put(
        api_routes.foods_item_id(food["id"]),
        json=update_data,
        headers=unique_user.token,
    )
    assert response.status_code == 200
    as_json = response.json()

    assert as_json["id"] == food["id"]
    assert as_json["name"] == update_data["name"]
    assert as_json["description"] == update_data["description"]


def test_delete_food(api_client: TestClient, food: dict, unique_user: TestUser):
    id = food["id"]

    response = api_client.delete(api_routes.foods_item_id(id), headers=unique_user.token)

    assert response.status_code == 200

    response = api_client.get(api_routes.foods_item_id(id), headers=unique_user.token)
    assert response.status_code == 404


def test_food_extras(
    api_client: TestClient,
    unique_user: TestUser,
):
    key_str_1 = random_string()
    val_str_1 = random_string()

    key_str_2 = random_string()
    val_str_2 = random_string()

    # create a food with extras
    new_food_data: dict = {"name": random_string()}
    new_food_data["extras"] = {key_str_1: val_str_1}

    response = api_client.post(api_routes.foods, json=new_food_data, headers=unique_user.token)
    food_as_json = utils.assert_deserialize(response, 201)

    # make sure the extra persists
    extras = food_as_json["extras"]
    assert key_str_1 in extras
    assert extras[key_str_1] == val_str_1

    # add more extras to the food
    food_as_json["extras"][key_str_2] = val_str_2

    response = api_client.put(
        api_routes.foods_item_id(food_as_json["id"]),
        json=food_as_json,
        headers=unique_user.token,
    )
    food_as_json = utils.assert_deserialize(response, 200)

    # make sure both the new extra and original extra persist
    extras = food_as_json["extras"]
    assert key_str_1 in extras
    assert key_str_2 in extras
    assert extras[key_str_1] == val_str_1
    assert extras[key_str_2] == val_str_2


def test_update_food_household_label_override(api_client: TestClient, unique_user: TestUser):
    database = unique_user.repos
    base_label = database.group_multi_purpose_labels.create({"name": random_string(10), "group_id": unique_user.group_id})
    override_label = database.group_multi_purpose_labels.create(
        {"name": random_string(10), "group_id": unique_user.group_id}
    )
    food = database.ingredient_foods.create(
        {"name": random_string(10), "group_id": unique_user.group_id, "label_id": base_label.id}
    )

    response = api_client.put(
        api_routes.foods_item_id(food.id),
        json={"name": food.name, "householdLabelId": str(override_label.id)},
        headers=unique_user.token,
    )
    as_json = utils.assert_deserialize(response, 200)
    assert as_json["householdLabelId"] == str(override_label.id)
    assert as_json["labelId"] == str(base_label.id)

    response = api_client.get(api_routes.foods_item_id(food.id), headers=unique_user.token)
    as_json = utils.assert_deserialize(response, 200)
    assert as_json["householdLabelId"] == str(override_label.id)


def test_recipe_get_one_uses_household_food_label_override(api_client: TestClient, unique_user: TestUser):
    database = unique_user.repos
    base_label = database.group_multi_purpose_labels.create({"name": random_string(10), "group_id": unique_user.group_id})
    override_label = database.group_multi_purpose_labels.create(
        {"name": random_string(10), "group_id": unique_user.group_id}
    )
    food = database.ingredient_foods.create(
        {"name": random_string(10), "group_id": unique_user.group_id, "label_id": base_label.id}
    )
    recipe = database.recipes.create(
        Recipe(
            user_id=unique_user.user_id,
            household_id=unique_user.household_id,
            group_id=unique_user.group_id,
            name=random_string(10),
            recipe_ingredient=[RecipeIngredient(quantity=1, food=food)],
        )
    )

    database.session.add(
        HouseholdIngredientFoodLabel(
            household_id=unique_user.household_id,
            food_id=food.id,
            label_id=override_label.id,
        )
    )
    database.session.commit()

    response = api_client.get(api_routes.recipes_slug(recipe.slug), headers=unique_user.token)
    as_json = utils.assert_deserialize(response, 200)
    ingredient_food = as_json["recipeIngredient"][0]["food"]
    assert ingredient_food["labelId"] == str(override_label.id)
    assert ingredient_food["householdLabelId"] == str(override_label.id)
