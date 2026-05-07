<template>
  <div v-if="dialog">
    <BaseDialog
      v-if="shoppingListDialog && ready"
      v-model="dialog"
      :title="$t('recipe.add-to-list')"
      :icon="$globals.icons.cartCheck"
    >
      <v-container v-if="!filteredShoppingLists.length">
        <BasePageTitle>
          <template #title>
            {{ $t('shopping-list.no-shopping-lists-found') }}
          </template>
        </BasePageTitle>
      </v-container>
      <v-card-text>
        <v-card
          v-for="list in filteredShoppingLists"
          :key="list.id"
          hover
          class="my-2 left-border"
          @click="openShoppingListIngredientDialog(list)"
        >
          <v-card-title class="py-2">
            {{ list.name }}
          </v-card-title>
        </v-card>
      </v-card-text>
      <template #card-actions>
        <v-btn
          variant="text"
          color="grey"
          @click="dialog = false"
        >
          {{ $t("general.cancel") }}
        </v-btn>
        <div
          class="d-flex justify-end"
          style="width: 100%;"
        >
          <v-checkbox
            v-model="preferences.viewAllLists"
            hide-details
            :label="$t('general.show-all')"
            class="my-auto mr-4"
            @click="setShowAllToggled()"
          />
        </div>
      </template>
    </BaseDialog>
    <BaseDialog
      v-if="shoppingListIngredientDialog"
      v-model="dialog"
      :title="selectedShoppingList?.name || $t('recipe.add-to-list')"
      :icon="$globals.icons.cartCheck"
      width="70%"
      :submit-text="$t('recipe.add-to-list')"
      can-submit
      @submit="addRecipesToList()"
    >
      <div style="max-height: 70vh;  overflow-y: auto">
        <v-card v-for="(listSection, recipeSectionIndex) in groupedIngredients" :key="recipeSectionIndex" elevation="0" height="fit-content" width="100%">
          <v-divider
            v-if="recipeSectionIndex > 0"
            class="mt-3"
          />
          <v-card-title v-if="listSection.section" class="justify-center text-h5" width="100%">
            {{ listSection.section }}
          </v-card-title>
          <div>
            <div v-for="(label, labelIndex) in listSection.labels" :key="recipeSectionIndex + label.label">
              <v-card-title v-if="label.label" class="ingredient-title mt-2 pb-0 text-h6">
                {{ label.label }}
              </v-card-title>
              <div
                :class="$vuetify.display.smAndDown ? '' : 'ingredient-grid'"
                :style="$vuetify.display.smAndDown ? '' : { gridTemplateRows: `repeat(${Math.ceil(label.ingredients.length / 2)}, min-content)` }"
              >
                <v-list-item
                  v-for="(ingredientData, ingredientIndex) in label.ingredients"
                  :key="recipeSectionIndex + label.label + ingredientIndex"
                  density="compact"
                  @click="groupedIngredients[recipeSectionIndex]
                    .labels[labelIndex]
                    .ingredients[ingredientIndex].checked
                    = !groupedIngredients[recipeSectionIndex]
                      .labels[labelIndex]
                      .ingredients[ingredientIndex].checked"
                >
                  <v-container class="pa-0 ma-0">
                    <v-row no-gutters>
                      <v-checkbox
                        hide-details
                        :model-value="ingredientData.checked"
                        class="pt-0 my-auto py-auto mr-2"
                        color="secondary"
                        density="compact"
                      />
                      <div key="ingredientData.ingredientSum.quantity" class="pa-auto my-auto">
                        <RecipeIngredientListItem
                          :ingredient="ingredientData.ingredientSum"
                          :scale="1"
                        />
                      </div>
                    </v-row>
                  </v-container>
                </v-list-item>
              </div>
            </div>
          </div>
        </v-card>
      </div>
    </BaseDialog>
  </div>
</template>

<script setup lang="ts">
import { toRefs } from "@vueuse/core";
import RecipeIngredientListItem from "./RecipeIngredientListItem.vue";
import { useUserApi } from "~/composables/api";
import { useHouseholdSelf } from "~/composables/use-households";
import { alert } from "~/composables/use-toast";
import { useShoppingListPreferences } from "~/composables/use-users/preferences";
import { convertToGram, convertToMilliliter } from "~/composables/recipes/use-recipe-ingredients";
import { applyHouseholdFoodSubstitution, getHouseholdFoodSubstitutions } from "~/composables/recipes/use-household-food-substitutions";
import { useUnitStore } from "~/composables/store";
import type { IngredientUnit, RecipeIngredient, ShoppingListAddRecipeParamsBulk, ShoppingListSummary } from "~/lib/api/types/household";
import type { IngredientFood, Recipe } from "~/lib/api/types/recipe";
import { reduceIngredients } from "~/composables/recipes/use-recipe";
import { UnitNames } from "~/composables/use-unit";

export interface RecipeWithScale extends Recipe {
  scale: number;
}

export interface ShoppingListRecipe {
  id: string;
  scale: number;
}

export interface ShoppingListGroupedIngredientItem {
  checked: boolean;
  ingredient: RecipeIngredient;
  recipe: ShoppingListRecipe;
}

export interface ShoppingListGroupedIngredient {
  checked: boolean;
  ingredientSum: RecipeIngredient;
  ingredientItems: ShoppingListGroupedIngredientItem[];
}

export interface ShoppingListGroupedIngredientLabel {
  label: string;
  labelSortOrder: number | null | undefined;
  ingredients: ShoppingListGroupedIngredient[];
}

export interface ShoppingListGroupedIngredientLabels {
  section: string;
  labels: ShoppingListGroupedIngredientLabel[];
}

interface Props {
  recipes?: RecipeWithScale[];
  shoppingLists?: ShoppingListSummary[];
}
const props = withDefaults(defineProps<Props>(), {
  recipes: undefined,
  shoppingLists: () => [],
});

const dialog = defineModel<boolean>({ default: false });

const i18n = useI18n();
const auth = useMealieAuth();
const { household } = useHouseholdSelf();
const api = useUserApi();
const { household } = useHouseholdSelf();
const preferences = useShoppingListPreferences();
const ready = ref(false);
const substitutions = computed(() => getHouseholdFoodSubstitutions(household.value));

// Capture values at initialization to avoid reactive updates
const currentHouseholdSlug = ref("");
const filteredShoppingLists = ref<ShoppingListSummary[]>([]);

const state = reactive({
  shoppingListDialog: false,
  shoppingListIngredientDialog: false,
  shoppingListShowAllToggled: false,
});

const { shoppingListDialog, shoppingListIngredientDialog, shoppingListShowAllToggled: _shoppingListShowAllToggled } = toRefs(state);

const selectedShoppingList = ref<ShoppingListSummary | null>(null);
const groupedIngredients = ref<ShoppingListGroupedIngredientLabels[]>([]);

watch([dialog, () => preferences.value.viewAllLists], () => {
  if (dialog.value) {
    currentHouseholdSlug.value = auth.user.value?.householdSlug || "";
    filteredShoppingLists.value = props.shoppingLists.filter(
      list => preferences.value.viewAllLists || list.userId === auth.user.value?.id,
    );

    const defaultShoppingListId = household.value?.preferences?.defaultShoppingListId ?? null;
    const defaultShoppingList = defaultShoppingListId
      ? props.shoppingLists.find(list => list.id === defaultShoppingListId)
      : null;

    if (defaultShoppingList && !state.shoppingListShowAllToggled) {
      selectedShoppingList.value = defaultShoppingList;
      openShoppingListIngredientDialog(selectedShoppingList.value);
    }
    else if (filteredShoppingLists.value.length === 1 && !state.shoppingListShowAllToggled) {
      selectedShoppingList.value = filteredShoppingLists.value[0];
      openShoppingListIngredientDialog(selectedShoppingList.value);
    }
    else {
      state.shoppingListDialog = true;
      ready.value = true;
    }
  }
  else if (!dialog.value) {
    initState();
  }
});

async function consolidateRecipesIntoGroups(recipes: RecipeWithScale[]) {
  groupedIngredients.value = [{ section: "", labels: [] }, { section: "On hand", labels: [] }];
  const recipeMap = new Map<string, ShoppingListRecipe>();
  const groupedIngredientMap = new Map<string, ShoppingListGroupedIngredient>();

  for (const recipe of recipes) {
    if (!recipe.slug) {
      continue;
    }

    if (recipeMap.has(recipe.slug)) {
      const existingRecipe = recipeMap.get(recipe.slug);
      if (existingRecipe) {
        existingRecipe.scale += recipe.scale;
      }
      continue;
    }

    const recipeData = { ...recipe };
    if (!(recipeData.id && recipeData.name && recipeData.recipeIngredient)) {
      const { data } = await api.recipes.getOne(recipe.slug);
      if (!data?.recipeIngredient?.length) {
        continue;
      }
      recipeData.id = data.id || "";
      recipeData.name = data.name || "";
      recipeData.recipeIngredient = data.recipeIngredient;
    }
    else if (!recipeData.recipeIngredient.length) {
      continue;
    }

    const recipeItem: ShoppingListRecipe = {
      id: recipeData.id,
      scale: recipeData.scale,
    };

    recipeMap.set(recipe.slug, recipeItem);

    recipeData.recipeIngredient.forEach((ing) => {
      if (ing.unit) {
        if (ing.unit.standardUnit === UnitNames.gram) {
          ing.quantity = Number(convertToGram(ing.quantity, ing.unit));
          ing.unit = unitStore.store.value.find(unit => unit.name === UnitNames.gram) as IngredientUnit;
        }
        else if (ing.unit.standardUnit === UnitNames.milliliter) {
          ing.quantity = Number(convertToMilliliter(ing.quantity, ing.unit));
          ing.unit = unitStore.store.value.find(unit => unit.name === UnitNames.milliliter) as IngredientUnit;
        }
      }
    });

    recipeData.recipeIngredient = reduceIngredients(recipeData.recipeIngredient);

    recipeData.recipeIngredient.forEach((ing) => {
      ing = applyHouseholdFoodSubstitution(ing, substitutions.value, unitStore.store.value) as RecipeIngredient;
      addToGroups(ing, recipeItem);
    });
  }

  function addToGroups(ing: RecipeIngredient, recipeItem: ShoppingListRecipe) {
    if (!ing.referencedRecipe?.slug) {
      const householdsWithFood = ing.food?.householdsWithIngredientFood || [];
      const checked = ing.food && ing.food.name ? !householdsWithFood.includes(currentHouseholdSlug.value) : true;
      const groupedIngredientMapKey = (ing.food && ing.food.name ? ing.food.name : ing.referenceId || "") + (ing.unit?.name || "");
      const match = ing.note?.match(/^or [^;]*/);
      ing.note = match ? match[0] : undefined;

      if (groupedIngredientMap.has(groupedIngredientMapKey)) {
        const mapItem = groupedIngredientMap.get(groupedIngredientMapKey);
        if (mapItem) {
          if (ing.note) {
            mapItem.ingredientSum.note = mapItem.ingredientSum.note ? `${mapItem.ingredientSum.note} | ${ing.note}` : ing.note;
          }
          mapItem.ingredientItems.push({
            checked,
            ingredient: ing,
            recipe: recipeItem,
          });
        }
      }
      else {
        groupedIngredientMap.set(groupedIngredientMapKey, {
          checked,
          ingredientSum: {
            ...ing,
            quantity: 0,
          },
          ingredientItems: [{
            checked,
            ingredient: ing,
            recipe: recipeItem,
          }],
        });
      }
    }
    else if (recipeMap.has(ing.referencedRecipe.slug)) {
      const existingRecipe = recipeMap.get(ing.referencedRecipe.slug);
      if (existingRecipe) {
        existingRecipe.scale += (ing.quantity || 1) / (ing.referencedRecipe.recipeServings || 1);
      }
    }
    else {
      const refRecipeItem: ShoppingListRecipe = {
        id: recipeItem.id,
        scale: (ing.quantity || 1) / (ing.referencedRecipe.recipeServings || 1),
      };

      recipeMap.set(ing.referencedRecipe.slug, refRecipeItem);

      ing.referencedRecipe.recipeIngredient?.forEach(refIng => addToGroups(refIng, refRecipeItem));
    }
  }
  const groupedIngredientLabelMap = new Map<string, ShoppingListGroupedIngredientLabel>();
  const groupedIngredientLabelOnHandMap = new Map<string, ShoppingListGroupedIngredientLabel>();

  groupedIngredientMap.forEach((ing) => {
    ing.ingredientItems.forEach((ingItem) => {
      if (ingItem.ingredient.quantity) {
        ing.ingredientSum.quantity = (ing.ingredientSum.quantity || 0) + (ingItem.ingredient.quantity * ingItem.recipe.scale);
      }
    });

    let label: string;
    let labelSortOrder: number;
    const labelObject = (ing.ingredientSum.food as IngredientFood)?.label;

    if (labelObject?.sortOrder) {
      label = labelObject.labelText || labelObject.name;
      labelSortOrder = labelObject.sortOrder;
    }
    else {
      label = "Mixed";
      labelSortOrder = 999;
    }

    if (ing.checked) {
      if (groupedIngredientLabelMap.has(label)) {
        groupedIngredientLabelMap.get(label)?.ingredients.push(ing);
      }
      else {
        groupedIngredientLabelMap.set(label, { label, labelSortOrder, ingredients: [ing] });
      }
    }
    else if (groupedIngredientLabelOnHandMap.has(label)) {
      groupedIngredientLabelOnHandMap.get(label)?.ingredients.push(ing);
    }
    else {
      groupedIngredientLabelOnHandMap.set(label, { label, labelSortOrder, ingredients: [ing] });
    }
  });

  moveToMixed(groupedIngredientLabelMap);
  moveToMixed(groupedIngredientLabelOnHandMap);

  groupedIngredients.value[0].labels = Array.from(groupedIngredientLabelMap.values()).sort((a, b) => {
    return (a.labelSortOrder || a.label) < (b.labelSortOrder || b.label) ? -1 : 1;
  });
  groupedIngredients.value[1].labels = Array.from(groupedIngredientLabelOnHandMap.values()).sort((a, b) => {
    return (a.labelSortOrder || a.label) < (b.labelSortOrder || b.label) ? -1 : 1;
  });

  function moveToMixed(map: Map<string, ShoppingListGroupedIngredientLabel>) {
    const keysToBeMixed: string[] = [];
    map.forEach((value, key) => {
      if (value.ingredients.length == 1) {
        keysToBeMixed.push(key);
      }
    });

    if (keysToBeMixed.length >= 2) {
      const mixed: ShoppingListGroupedIngredient[] = [];
      keysToBeMixed.forEach((key) => {
        const label = map.get(key);
        if (label?.ingredients[0]) {
          mixed.push(label.ingredients[0]);
          map.delete(key);
        }
      });
      const mixedKey = "mixed";
      if (map.has(mixedKey)) {
        const oldMap = map.get(mixedKey);
        if (oldMap) {
          oldMap.ingredients.push(...mixed);
        }
      }
      else {
        map.set(mixedKey, { label: "Mixed", labelSortOrder: 999, ingredients: mixed });
      }
    }
  }
}

function initState() {
  state.shoppingListDialog = false;
  state.shoppingListIngredientDialog = false;
  state.shoppingListShowAllToggled = false;
  selectedShoppingList.value = null;
  groupedIngredients.value = [];
}

initState();

async function openShoppingListIngredientDialog(list: ShoppingListSummary) {
  if (!props.recipes?.length) {
    return;
  }
  selectedShoppingList.value = list;
  console.log("shop", props.recipes);
  await consolidateRecipesIntoGroups(props.recipes);
  state.shoppingListDialog = false;
  state.shoppingListIngredientDialog = true;
}

function setShowAllToggled() {
  state.shoppingListShowAllToggled = true;
}

const unitStore = useUnitStore();

async function addRecipesToList() {
  if (!selectedShoppingList.value) {
    return;
  }

  const recipeData: ShoppingListAddRecipeParamsBulk[] = [];

  const recipeDataIndexes: { [key: string]: number } = {};
  groupedIngredients.value.forEach((section) => {
    section.labels.forEach((label) => {
      label.ingredients.forEach((ingredientData) => {
        if (ingredientData.checked) {
          ingredientData.ingredientItems.forEach((ing) => {
            if (ing.recipe.id in recipeDataIndexes) {
              recipeData[recipeDataIndexes[ing.recipe.id]].recipeIngredients?.push(ing.ingredient);
            }
            else {
              recipeDataIndexes[ing.recipe.id] = recipeData.length;
              recipeData.push({
                recipeId: ing.recipe.id,
                recipeIncrementQuantity: ing.recipe.scale,
                recipeIngredients: [ing.ingredient],
              });
            }
          });
        }
      });
    });
  });

  const { error } = await api.shopping.lists.addRecipes(selectedShoppingList.value.id, recipeData);
  // eslint-disable-next-line @typescript-eslint/no-unused-expressions
  error ? alert.error(i18n.t("recipe.failed-to-add-recipes-to-list")) : alert.success(i18n.t("recipe.successfully-added-to-list"));

  state.shoppingListDialog = false;
  state.shoppingListIngredientDialog = false;
  dialog.value = false;
}
</script>

<style scoped lang="css">
.ingredient-grid {
  display: grid;
  grid-auto-flow: column;
  grid-template-columns: 1fr 1fr;
  grid-gap: 0.5rem;
}
</style>
