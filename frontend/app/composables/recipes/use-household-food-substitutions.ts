import type { HouseholdInDB, ReadHouseholdFoodSubstitution } from "~/lib/api/types/household";

type IngredientUnitLike = {
  id?: string | null;
  name?: string;
  pluralName?: string | null;
  abbreviation?: string;
  pluralAbbreviation?: string | null;
  standardQuantity?: number | null;
  standardUnit?: string | null;
};

type RecipeLike = {
  recipeYieldUnit?: IngredientUnitLike | null;
  recipeYield?: string | null;
};

type FoodLike = {
  id?: string | null;
};

type RecipeIngredientLike = {
  quantity?: number | null;
  food?: FoodLike | null;
  unit?: IngredientUnitLike | null;
  referencedRecipe?: RecipeLike | null;
};

export function getHouseholdFoodSubstitutions(
  household: HouseholdInDB | null | undefined,
): ReadHouseholdFoodSubstitution[] {
  const substitutions = household?.preferences?.foodSubstitutions;
  if (!Array.isArray(substitutions)) {
    return [];
  }

  return substitutions;
}

export function applyHouseholdFoodSubstitution<T extends RecipeIngredientLike>(
  ingredient: T,
  substitutions: ReadHouseholdFoodSubstitution[],
): T {
  if (!ingredient.food?.id || !substitutions.length) {
    return ingredient;
  }

  const substitution = substitutions.find(sub => sub.sourceFoodId === ingredient.food?.id);
  if (!substitution) {
    return ingredient;
  }
  const ratio = substitution.ratio && substitution.ratio > 0 ? substitution.ratio : 1;
  const substitutedIngredient = JSON.parse(JSON.stringify(ingredient)) as T;

  if (typeof substitutedIngredient.quantity === "number") {
    substitutedIngredient.quantity *= ratio;
  }
  else if (substitution.substituteRecipeId) {
    // Preserve legacy "no quantity means 1" behavior for referenced recipes.
    substitutedIngredient.quantity = ratio;
  }

  if (substitution.substituteFood) {
    substitutedIngredient.food = substitution.substituteFood;
    substitutedIngredient.referencedRecipe = null;
    return substitutedIngredient;
  }

  if (substitution.substituteRecipe) {
    const substituteYieldUnit = substitution.substituteRecipe.recipeYieldUnit;
    const originalUnit = substitutedIngredient.unit;

    if (
      typeof substitutedIngredient.quantity === "number"
      && originalUnit?.standardQuantity
      && originalUnit.standardUnit
      && substituteYieldUnit?.standardQuantity
      && substituteYieldUnit.standardUnit === originalUnit.standardUnit
    ) {
      substitutedIngredient.quantity = substitutedIngredient.quantity
        * originalUnit.standardQuantity
        / substituteYieldUnit.standardQuantity;
      substitutedIngredient.unit = substituteYieldUnit;
    }
    else {
      substitutedIngredient.unit = null;
    }

    substitutedIngredient.food = null;
    substitutedIngredient.referencedRecipe = substitution.substituteRecipe;
  }

  return substitutedIngredient;
}
