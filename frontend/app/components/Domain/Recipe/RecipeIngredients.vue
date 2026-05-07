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
      <v-checkbox
        v-if="!isCookMode && sortedIngredientsByPlace"
        v-model="sortIngredientsByPlace"
        class="my-auto ml-auto"
        color="secondary"
        :label="$t('recipe.sort-by-label-place')"
      />
      <template v-if="!isCookMode && sortIngredientsByPlace">
        <div
          v-for="(place, placeName) in sortedIngredientsByPlace"
          :key="'place' + placeName"
        >
          <h2
            v-if="place.length > 0"
            class="mt-2"
          >
            {{ placeName }}
          </h2>
          <v-list>
            <template
              v-for="(ingredient, ingredientIndex) in place"
              :key="'ingredient' + ingredientIndex"
            >
              <v-list-item
                v-if="!ingredient.referencedRecipe || (ingredient.referencedRecipe?.recipeInstructions?.length || 0 > 0)"
                density="compact"
                class="pa-0"
              >
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
                >
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
      </template>

      <template v-else>
        <v-list>
          <template
            v-for="(ingredient, index) in groupedIngredients"
            :key="'ingredient' + index"
          >
            <v-list-item
              v-if="!ingredient.referencedRecipe || (ingredient.referencedRecipe?.recipeInstructions?.length || 0 > 0)"
              density="compact"
              class="pa-0"
              @click.stop="toggleChecked(index)"
            >
              <template #prepend>
                <v-checkbox
                  v-model="checked[index]"
                  hide-details
                  class="pt-0 my-auto py-auto"
                  color="secondary"
                  density="comfortable"
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
                      v-model="checked[index]"
                      hide-details
                      class="pt-0 my-auto py-auto"
                      color="secondary"
                      density="comfortable"
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
              >
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
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import RecipeIngredientListItem from "./RecipeIngredientListItem.vue";
import { applyHouseholdFoodSubstitution, getHouseholdFoodSubstitutions, useIngredientTextParser } from "~/composables/recipes";
import type { IngredientFood, RecipeIngredient } from "~/lib/api/types/recipe";
import { reduceIngredients } from "~/composables/recipes/use-recipe";
import { useUnitStore } from "~/composables/store";

const { household } = useHouseholdSelf();
const unitStore = useUnitStore();
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

const checked = ref(props.value.map(() => false));
const sortIngredientsByPlace = ref(true); // TODO: Save default value as a household setting

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

function toggleChecked(index: number) {
  // TODO Find a better way to do this - $set is not available, and
  // direct array modifications are not propagated for some reason
  checked.value.splice(index, 1, !checked.value[index]);
}

const sortedIngredientsByPlace = computed(() => {
  const ingredientsByPlace: { fridge: RecipeIngredient[]; freezer: RecipeIngredient[]; pantry: RecipeIngredient[] } = { fridge: [], freezer: [], pantry: [] };
  groupedIngredients.value.forEach((ingredient) => {
    let place = (ingredient.food as IngredientFood)?.label?.place;
    if (ingredient.referencedRecipe?.recipeIngredient) {
      const refFood = ingredient.referencedRecipe?.recipeIngredient[0].food as IngredientFood;
      place = refFood?.label?.place;
    }

    if (place) {
      ingredientsByPlace[place].push(ingredient);
    }
    else {
      ingredientsByPlace.pantry.push(ingredient);
    }
  });
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
  return ingredientsByPlace;
});

const groupedIngredients = computed(() => {
  const reducedIngredients = reduceIngredients(props.value);
  reducedIngredients.forEach((ingredient, index) => {
    reducedIngredients[index] = applyHouseholdFoodSubstitution(
      ingredient,
      substitutions.value,
      unitStore.store.value,
    ) as RecipeIngredient;
  });
  return reducedIngredients;
});
</script>

<style>
.dense-markdown p {
  margin: auto !important;
}
</style>
