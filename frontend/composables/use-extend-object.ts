import type { MultiPurposeLabelSummary } from "~/lib/api/types/labels";
import type { CreateIngredientFood, CreateIngredientUnit, IngredientFood, IngredientUnit, Recipe, RecipeIngredient, RecipeTool } from "~/lib/api/types/recipe";

export function extendFood(food: IngredientFood | CreateIngredientFood | null | undefined) {
  if (food?.description?.startsWith("{")) {
    const descriptionObject = JSON.parse(food.description);
    food.density = descriptionObject.density;
    food.tip = descriptionObject.tip;
  }
}

export function extendLabel(label: MultiPurposeLabelSummary | null | undefined) {
  if (label?.name.startsWith("{")) {
    const labelObject = JSON.parse(label.name);
    label.sortOrder = labelObject.sortOrder;
    label.labelText = labelObject.name;
    label.place = labelObject.place;
  }
}

export function extendUnit(unit: IngredientUnit | CreateIngredientUnit | null | undefined) {
  if (unit?.description?.startsWith("{")) {
    const descriptionObject = JSON.parse(unit.description);
    unit.gram = descriptionObject.gram;
    unit.milliliter = descriptionObject.milliliter;
    unit.metric = descriptionObject.metric;
    unit.imperial = descriptionObject.imperial;
    unit.range = descriptionObject.range;
  }
};

export function extendTool(tool: RecipeTool | null | undefined) {
  if (tool?.name?.startsWith("{")) {
    const toolObject = JSON.parse(tool.name);
    tool.sortOrder = toolObject.sortOrder;
    tool.toolName = toolObject.name;
    tool.labelText = toolObject.label;
    tool.weight = toolObject.weight;
    tool.servingCategory = toolObject.servingCategory;
  }
}

export function extendRecipe(recipe: Recipe) {
  if (recipe.recipeIngredient && recipe.recipeIngredient.length > 0) {
    recipe.recipeIngredient.forEach((ingredient) => {
      extendObjects(ingredient);
    });
  }

  if (recipe.tools) {
    for (const tool of recipe.tools) {
      extendTool(tool);
    }
  }

  function extendObjects(ingredient: RecipeIngredient) {
    if (!ingredient.referencedRecipe) {
      extendFood(ingredient.food);

      extendLabel((ingredient.food as IngredientFood)?.label);

      extendUnit(ingredient.unit);
    }
    else if (ingredient.referencedRecipe.recipeIngredient && ingredient.referencedRecipe.recipeIngredient.length > 0) {
      for (const refIngredient of ingredient.referencedRecipe.recipeIngredient) {
        extendObjects(refIngredient);
      }
    }
  }
}

export function compareLabel(a: MultiPurposeLabelSummary | null, b: MultiPurposeLabelSummary | null) {
  if (!a || !b) return 1;
  return (a.sortOrder || a.name) < (b.sortOrder || b.name) ? -1 : 1;
}

export function parseLabelName(label: MultiPurposeLabelSummary | null | undefined, withPlace: boolean = false) {
  if (!label) {
    const { t } = useI18n();
    return t("shopping-list.no-label");
  }
  return label.labelText ? `${label.labelText}${withPlace && label.place ? `: ${label.place}` : ""}` : label.name;
}

export function parseToolName(tool: RecipeTool) {
  return tool.toolName ? tool.toolName : tool.name;
}
