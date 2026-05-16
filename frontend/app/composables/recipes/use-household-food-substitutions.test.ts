import { describe, expect, test } from "vitest";

import {
  applyHouseholdFoodSubstitution,
  getHouseholdFoodSubstitutions,
} from "./use-household-food-substitutions";
import type { HouseholdInDB, ReadHouseholdFoodSubstitution } from "~/lib/api/types/household";
import type { RecipeIngredient } from "~/lib/api/types/recipe";

function createIngredient(overrides: Partial<RecipeIngredient> = {}): RecipeIngredient {
  return {
    quantity: 4,
    note: "original note",
    food: {
      id: "source-food-id",
      name: "Source Food",
    },
    referencedRecipe: null,
    ...overrides,
  } as RecipeIngredient;
}

function createFoodSubstitution(
  overrides: Partial<ReadHouseholdFoodSubstitution> = {},
): ReadHouseholdFoodSubstitution {
  return {
    id: "substitution-id",
    sourceFoodId: "source-food-id",
    ratio: 0.5,
    sourceFood: {
      id: "source-food-id",
      name: "Source Food",
    },
    substituteFood: {
      id: "substitute-food-id",
      name: "Substitute Food",
    },
    substituteRecipe: null,
    substituteRecipeId: null,
    substituteFoodId: "substitute-food-id",
    ...overrides,
  } as ReadHouseholdFoodSubstitution;
}

describe("use-household-food-substitutions", () => {
  test("extracts substitutions from household preferences", () => {
    const substitutions = [createFoodSubstitution()];
    const household = {
      preferences: {
        foodSubstitutions: substitutions,
      },
    } as HouseholdInDB;

    expect(getHouseholdFoodSubstitutions(household)).toEqual(substitutions);
    expect(getHouseholdFoodSubstitutions(null)).toEqual([]);
  });

  test("replaces the ingredient food and scales quantity", () => {
    const ingredient = createIngredient();
    const substitution = createFoodSubstitution();

    const result = applyHouseholdFoodSubstitution(ingredient, [substitution]);

    expect(result).not.toBe(ingredient);
    expect(result.food?.id).toBe("substitute-food-id");
    expect(result.referencedRecipe).toBeNull();
    expect(result.quantity).toBe(2);
    expect(ingredient.food?.id).toBe("source-food-id");
    expect(ingredient.quantity).toBe(4);
  });

  test("replaces the ingredient with a referenced recipe target", () => {
    const ingredient = createIngredient({
      quantity: null,
      unit: {
        id: "quart-id",
        name: "quart",
      },
    });
    const substitution = createFoodSubstitution({
      ratio: 3,
      substituteFood: null,
      substituteFoodId: null,
      substituteRecipeId: "recipe-id",
      substituteRecipe: {
        id: "recipe-id",
        name: "Substitute Recipe",
        slug: "substitute-recipe",
      },
    });

    const result = applyHouseholdFoodSubstitution(ingredient, [substitution]);

    expect(result.food).toBeNull();
    expect(result.unit).toBeNull();
    expect(result.referencedRecipe?.id).toBe("recipe-id");
    expect(result.quantity).toBe(3);
  });

  test("converts the original unit into the substitute recipe yield unit", () => {
    const ingredient = createIngredient({
      quantity: 1,
      unit: {
        id: "quart-id",
        name: "quart",
        standardQuantity: 946.4,
        standardUnit: "milliliter",
      },
    });
    const substitution = createFoodSubstitution({
      ratio: 1,
      substituteFood: null,
      substituteFoodId: null,
      substituteRecipeId: "recipe-id",
      substituteRecipe: {
        id: "recipe-id",
        name: "vegetable broth",
        slug: "vegetable-broth",
        recipeYield: "cup",
      },
    });

    const result = applyHouseholdFoodSubstitution(ingredient, [substitution]);

    expect(result.referencedRecipe?.id).toBe("recipe-id");
    expect(result.unit?.id).toBe("cup-id");
    expect(result.quantity).toBeCloseTo(4, 1);
  });
});
