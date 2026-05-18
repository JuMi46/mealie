<template>
  <div v-if="value && value.length > 0">
    <div
      v-if="!isCookMode"
      class="d-flex justify-start"
    >
      <h2 class="mt-1 text-h5 font-weight-medium opacity-80">
        {{ $t("recipe.ingredients") }}
      </h2>
      <AppButtonCopy
        btn-class="ml-auto"
        :copy-text="ingredientCopyText"
      />
    </div>
    <div>
      <div class="ingredient-sort-controls">
        <v-icon
          size="18"
          class="ingredient-sort-icon"
        >
          {{ $globals.icons.sortDescending }}
        </v-icon>
        <div
          v-if="!isCookMode"
          class="ingredient-sort-toggles"
        >
          <v-checkbox
            v-model="sortIngredientsByLabel"
            class="ingredient-sort-checkbox"
            color="secondary"
            density="compact"
            hide-details
            :label="$t('recipe.sort-by-label')"
          />
          <v-checkbox
            v-model="sortIngredientsBySection"
            class="ingredient-sort-checkbox"
            color="secondary"
            density="compact"
            hide-details
            :label="$t('recipe.sort-by-section')"
          />
        </div>
      </div>

      <div
        v-for="[sectionName, ingredientsByPlace] in ingredients"
        :key="'section' + sectionName"
      >
        <h3
          v-if="sectionName"
          class="mt-2"
        >
          {{ sectionName }}
        </h3>
        <v-divider v-if="sectionName" thickness="3" class="my-2" />
        <div
          v-for="[placeName, place] in ingredientsByPlace"
          :key="'place' + placeName"
        >
          <h3
            v-if="placeName && sortIngredientsByLabel"
            class="mt-2"
          >
            {{ placeName }}
          </h3>
          <v-divider v-if="placeName && sortIngredientsByLabel" thickness="2" gradient class="my-2" />

          <v-list>
            <template
              v-for="(ingredient, ingredientIndex) in place"
              :key="ingredient.referenceId || ('ingredient' + ingredientIndex)"
            >
              <v-list-item
                v-if="!ingredient.referencedRecipe || (ingredient.referencedRecipe?.recipeInstructions?.length || 0 > 0)"
                density="compact"
                class="pa-0"
              >
                <template #prepend>
                  <v-checkbox
                    v-if="showIngredientCheckboxesInRecipe"
                    :model-value="isIngredientChecked(sectionName, placeName, ingredient, ingredientIndex)"
                    hide-details
                    class="pt-0 my-auto py-auto"
                    color="secondary"
                    density="comfortable"
                    @update:model-value="setIngredientChecked(sectionName, placeName, ingredient, ingredientIndex, !!$event)"
                  />
                </template>
                <v-list-item-title>
                  <RecipeIngredientListItem
                    :ingredient="ingredient"
                    :scale="scale"
                  />
                </v-list-item-title>
              </v-list-item>

              <v-list-group
                v-else
                density="compact"
                class="pa-0"
              >
                <template #activator="{ props: groupProps }">
                  <v-list-item
                    v-bind="groupProps"
                    density="compact"
                    class="pa-0"
                  >
                    <template #prepend>
                      <v-checkbox
                        v-if="showIngredientCheckboxesInRecipe"
                        :model-value="isGroupedIngredientChecked(sectionName, placeName, ingredient, ingredientIndex)"
                        hide-details
                        class="pt-0 my-auto py-auto"
                        color="secondary"
                        density="comfortable"
                        @update:model-value="setGroupedIngredientChecked(sectionName, placeName, ingredient, ingredientIndex, !!$event)"
                      />
                    </template>
                    <v-list-item-title>
                      <RecipeIngredientListItem
                        :ingredient="ingredient"
                        :scale="scale"
                      />
                    </v-list-item-title>
                  </v-list-item>
                </template>
                <v-list-item
                  v-for="(refIngredient, refIngredientIndex) in ingredient.referencedRecipe?.recipeIngredient"
                  :key="'refIngredient' + refIngredientIndex"
                  density="compact"
                  class="pa-0"
                  style="padding-left: 10px;"
                >
                  <template #prepend>
                    <v-checkbox
                      v-if="showIngredientCheckboxesInRecipe"
                      :model-value="isReferencedIngredientChecked(sectionName, placeName, ingredientIndex, refIngredient, refIngredientIndex)"
                      hide-details
                      class="pt-0 my-auto py-auto"
                      color="secondary"
                      density="comfortable"
                      @update:model-value="setReferencedIngredientChecked(sectionName, placeName, ingredient, ingredientIndex, refIngredient, refIngredientIndex, !!$event)"
                    />
                  </template>
                  <v-list-item-title>
                    <RecipeIngredientListItem
                      :ingredient="refIngredient"
                      :scale="(ingredient.quantity || 1) * scale / (ingredient.referencedRecipe.recipeServings || 1)"
                    />
                  </v-list-item-title>
                </v-list-item>
              </v-list-group>
            </template>
          </v-list>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import RecipeIngredientListItem from "./RecipeIngredientListItem.vue";
import { applyHouseholdFoodSubstitution, getHouseholdFoodSubstitutions, useIngredientTextParser } from "~/composables/recipes";
import { useUserRecipeIngredientPreferences } from "~/composables/use-users/preferences";
import type { IngredientFood, RecipeIngredient } from "~/lib/api/types/recipe";
import { reduceIngredients } from "~/composables/recipes/use-recipe";

const { household } = useHouseholdSelf();
const substitutions = computed(() => getHouseholdFoodSubstitutions(household.value));

interface Props {
  value?: RecipeIngredient[];
  scale?: number;
  isCookMode?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  value: () => [],
  scale: 1,
  isCookMode: false,
});

const { parseIngredientText } = useIngredientTextParser();

const checkedByReferenceId = ref<Record<string, boolean>>({});
const ingredientPreferences = useUserRecipeIngredientPreferences();
const sortIngredientsByLabel = computed({
  get: () => ingredientPreferences.value.sortByLabel,
  set: value => (ingredientPreferences.value.sortByLabel = value),
});
const sortIngredientsBySection = computed({
  get: () => ingredientPreferences.value.sortBySection,
  set: value => (ingredientPreferences.value.sortBySection = value),
});
const showIngredientCheckboxesInRecipe = computed(() => ingredientPreferences.value.showIngredientCheckboxesInRecipe);

const ingredientCopyText = computed(() => {
  const components: string[] = [];
  props.value.forEach((ingredient) => {
    if (ingredient.title) {
      if (components.length) {
        components.push("");
      }

      components.push(`[${ingredient.title}]`);
    }

    components.push(parseIngredientText(ingredient, props.scale, false));
  });

  return components.join("\n");
});

function getIngredientCheckboxKey(sectionName: string, placeName: string, ingredient: RecipeIngredient, ingredientIndex: number): string {
  return ingredient.referenceId || `${sectionName}:${placeName}:${ingredientIndex}`;
}

function isIngredientChecked(sectionName: string, placeName: string, ingredient: RecipeIngredient, ingredientIndex: number): boolean {
  const key = getIngredientCheckboxKey(sectionName, placeName, ingredient, ingredientIndex);
  return !!checkedByReferenceId.value[key];
}

function setIngredientChecked(
  sectionName: string,
  placeName: string,
  ingredient: RecipeIngredient,
  ingredientIndex: number,
  value: boolean,
) {
  const key = getIngredientCheckboxKey(sectionName, placeName, ingredient, ingredientIndex);
  checkedByReferenceId.value[key] = value;
}

function getReferencedIngredientCheckboxKey(
  sectionName: string,
  placeName: string,
  ingredientIndex: number,
  refIngredient: RecipeIngredient,
  refIngredientIndex: number,
): string {
  return refIngredient.referenceId || `${sectionName}:${placeName}:${ingredientIndex}:ref:${refIngredientIndex}`;
}

function isReferencedIngredientChecked(
  sectionName: string,
  placeName: string,
  ingredientIndex: number,
  refIngredient: RecipeIngredient,
  refIngredientIndex: number,
): boolean {
  const key = getReferencedIngredientCheckboxKey(sectionName, placeName, ingredientIndex, refIngredient, refIngredientIndex);
  return !!checkedByReferenceId.value[key];
}

function areAllReferencedIngredientsChecked(
  sectionName: string,
  placeName: string,
  ingredient: RecipeIngredient,
  ingredientIndex: number,
): boolean {
  const referencedIngredients = ingredient.referencedRecipe?.recipeIngredient;
  if (!referencedIngredients || referencedIngredients.length === 0) {
    return false;
  }

  return referencedIngredients.every((refIngredient, refIngredientIndex) => isReferencedIngredientChecked(
    sectionName,
    placeName,
    ingredientIndex,
    refIngredient,
    refIngredientIndex,
  ));
}

function isGroupedIngredientChecked(
  sectionName: string,
  placeName: string,
  ingredient: RecipeIngredient,
  ingredientIndex: number,
): boolean {
  if (ingredient.referencedRecipe?.recipeIngredient?.length) {
    return areAllReferencedIngredientsChecked(sectionName, placeName, ingredient, ingredientIndex);
  }

  return isIngredientChecked(sectionName, placeName, ingredient, ingredientIndex);
}

function setGroupedIngredientChecked(
  sectionName: string,
  placeName: string,
  ingredient: RecipeIngredient,
  ingredientIndex: number,
  value: boolean,
) {
  setIngredientChecked(sectionName, placeName, ingredient, ingredientIndex, value);

  const referencedIngredients = ingredient.referencedRecipe?.recipeIngredient;
  if (!referencedIngredients || referencedIngredients.length === 0) {
    return;
  }

  referencedIngredients.forEach((refIngredient, refIngredientIndex) => {
    const key = getReferencedIngredientCheckboxKey(sectionName, placeName, ingredientIndex, refIngredient, refIngredientIndex);
    checkedByReferenceId.value[key] = value;
  });
}

function setReferencedIngredientChecked(
  sectionName: string,
  placeName: string,
  ingredient: RecipeIngredient,
  ingredientIndex: number,
  refIngredient: RecipeIngredient,
  refIngredientIndex: number,
  value: boolean,
) {
  const key = getReferencedIngredientCheckboxKey(sectionName, placeName, ingredientIndex, refIngredient, refIngredientIndex);
  checkedByReferenceId.value[key] = value;

  const parentValue = areAllReferencedIngredientsChecked(sectionName, placeName, ingredient, ingredientIndex);
  setIngredientChecked(sectionName, placeName, ingredient, ingredientIndex, parentValue);
}

function sortSectionIngredientsByPlace(ingredientsByPlace: Map<string, RecipeIngredient[]>) {
  for (const place in ingredientsByPlace) {
    ingredientsByPlace[place].sort((a: RecipeIngredient, b: RecipeIngredient) => {
      let aSortOrder = 100;
      let bSortOrder = 100;

      let aFood = a.food as IngredientFood;
      if (a.referencedRecipe?.recipeIngredient) {
        const refIng = a.referencedRecipe?.recipeIngredient[0];
        if (refIng) {
          aFood = refIng.food as IngredientFood;
        }
      }
      if (aFood?.label?.position) {
        aSortOrder = aFood.label.position;
      }

      let bFood = b.food as IngredientFood;
      if (b.referencedRecipe?.recipeIngredient) {
        const refIng = b.referencedRecipe?.recipeIngredient[0];
        if (refIng) {
          bFood = refIng.food as IngredientFood;
        }
      }
      if (bFood?.label?.position) {
        bSortOrder = bFood.label.position;
      }
      return aSortOrder - bSortOrder;
    });
  }
}

function transformToIngredientsByPlace(ingredients: RecipeIngredient[]): Map<string, RecipeIngredient[]> {
  const ingredientsByPlace = new Map<string, RecipeIngredient[]>([
    ["fridge", []],
    ["freezer", []],
    ["pantry", []],
    ["all", []],
  ]);

  ingredients = reduceIngredients(ingredients);
  ingredients.forEach((ingredient) => {
    let place: string | null | undefined = "all";
    if (sortIngredientsByLabel.value) {
      place = (ingredient.food as IngredientFood)?.label?.place;
      if (ingredient.referencedRecipe?.recipeIngredient) {
        const refFood = ingredient.referencedRecipe?.recipeIngredient[0].food as IngredientFood;
        place = refFood?.label?.place;
      }
      if (!place) {
        place = "pantry";
      }
    }

    ingredientsByPlace.get(place)?.push(ingredient);
  });

  for (const [place, placeIngredients] of ingredientsByPlace.entries()) {
    if (placeIngredients.length === 0) {
      ingredientsByPlace.delete(place);
    }
  }

  if (sortIngredientsByLabel.value) {
    sortSectionIngredientsByPlace(ingredientsByPlace);
  }
  return ingredientsByPlace;
}

const substitutedIngredients = computed(() => {
  return props.value.map(ingredient => applyHouseholdFoodSubstitution(
    ingredient,
    substitutions.value,
  ) as RecipeIngredient);
});

const ingredients = computed(() => {
  const ingredientsBySection = new Map<string, Map<string, RecipeIngredient[]>>();

  let ingredientTitle = "";
  let ingredientsInSection: RecipeIngredient[] = [];

  substitutedIngredients.value.forEach((ingredient, index) => {
    if (index === 0) {
      ingredientTitle = sortIngredientsBySection.value ? ingredient.title || "" : "";
    }
    else if (ingredient.title && sortIngredientsBySection.value) {
      ingredientsBySection.set(ingredientTitle, transformToIngredientsByPlace(ingredientsInSection));
      ingredientTitle = ingredient.title || "";
      ingredientsInSection = [];
    }

    ingredientsInSection.push(ingredient);
  });

  if (ingredientsInSection.length > 0) {
    ingredientsBySection.set(ingredientTitle, transformToIngredientsByPlace(ingredientsInSection));
  }

  return ingredientsBySection;
});
</script>

<style scoped>
.dense-markdown p {
  margin: auto !important;
}

.ingredient-sort-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 2rem;
}

.ingredient-sort-icon {
  opacity: 0.8;
}

.ingredient-sort-toggles {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.ingredient-sort-checkbox {
  margin: 0;
}

.ingredient-sort-checkbox :deep(.v-selection-control) {
  min-height: 1.75rem;
}

.ingredient-sort-checkbox :deep(.v-label) {
  opacity: 0.9;
}
</style>
