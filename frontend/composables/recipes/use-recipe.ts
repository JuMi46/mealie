import { useUserApi } from "~/composables/api";
import type { Recipe, RecipeIngredient } from "~/lib/api/types/recipe";

export const useRecipe = function (slug: string, eager = true) {
  const api = useUserApi();
  const loading = ref(false);

  const recipe = ref<Recipe | null>(null);

  async function fetchRecipe() {
    loading.value = true;
    const { data } = await api.recipes.getOne(slug);
    loading.value = false;
    if (data) {
      recipe.value = data;
    }
  }

  async function deleteRecipe() {
    loading.value = true;
    const { data } = await api.recipes.deleteOne(slug);
    loading.value = false;
    return data;
  }

  async function updateRecipe(recipe: Recipe) {
    loading.value = true;
    const { data } = await api.recipes.updateOne(slug, recipe);
    loading.value = false;
    return data;
  }

  onMounted(() => {
    if (eager) {
      fetchRecipe();
    }
  });

  return {
    recipe,
    loading,
    fetchRecipe,
    deleteRecipe,
    updateRecipe,
  };
};

export function reduceIngredients(ingredients: RecipeIngredient[]) {
  const indexes: { [key: string]: number } = {};
  const refIndexes: { [key: string]: number } = {};

  return ingredients.reduce((res, ingredient) => {
    const id = ingredient.food?.id;
    if (id) {
      if (indexes[id] == undefined) {
        indexes[id] = res.length;
        res.push(JSON.parse(JSON.stringify(ingredient)) as RecipeIngredient);
      }
      else {
        const index = indexes[id];
        if (ingredient.unit?.name === res[index].unit?.name && res[index].quantity && !isNaN(res[index].quantity)) {
          res[index].quantity += ingredient.quantity || 0;
        }
        else if (ingredient.unit?.milliliter && res[index].unit?.milliliter
          && ingredient.quantity && !isNaN(ingredient.quantity) && res[index].quantity && !isNaN(res[index].quantity)) {
          res[index].quantity += ingredient.quantity * ingredient.unit.milliliter / res[index].unit.milliliter;
        }
      }
    }
    else if (ingredient.referencedRecipe?.id) {
      const refId = ingredient.referencedRecipe?.id;
      if (refIndexes[refId] == undefined) {
        refIndexes[refId] = res.length;
        res.push(JSON.parse(JSON.stringify(ingredient)) as RecipeIngredient);
      }
      else {
        const index = refIndexes[refId];
        if (res[index].quantity && !isNaN(res[index].quantity)) {
          res[index].quantity += ingredient.quantity || 0;
        }
      }
    }
    else {
      res.push(JSON.parse(JSON.stringify(ingredient)) as RecipeIngredient);
    }
    return res;
  }, [] as RecipeIngredient[]);
}
