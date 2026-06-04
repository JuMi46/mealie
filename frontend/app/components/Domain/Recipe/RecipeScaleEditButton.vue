<template>
  <div v-if="yieldDisplay">
    <div class="text-center d-flex align-center">
      <div>
        <v-menu
          v-model="menu"
          :disabled="!canEditScale"
          offset-y
          top
          nudge-top="6"
          :close-on-content-click="false"
        >
          <template #activator="{ props: activatorProps }">
            <v-tooltip
              v-if="canEditScale"
              size="small"
              location="top"
              color="secondary-darken-1"
            >
              <template #activator="{ props: tooltipProps }">
                <v-card
                  class="pa-1 px-2"
                  dark
                  color="secondary-darken-1"
                  size="small"
                  v-bind="{ ...activatorProps, ...tooltipProps }"
                  :style="{ cursor: canEditScale ? '' : 'default' }"
                >
                  <v-icon
                    v-if="canEditScale"
                    size="small"
                    class="mr-2"
                  >
                    {{ $globals.icons.edit }}
                  </v-icon>
                  <!-- eslint-disable-next-line vue/no-v-html -->
                  <span v-html="yieldDisplay" />
                </v-card>
              </template>
              <span> {{ $t("recipe.edit-scale") }} </span>
            </v-tooltip>
            <v-card
              v-else
              class="pa-1 px-2"
              dark
              color="secondary-darken-1"
              size="small"
              v-bind="activatorProps"
              :style="{ cursor: canEditScale ? '' : 'default' }"
            >
              <v-icon
                v-if="canEditScale"
                size="small"
                class="mr-2"
              >
                {{ $globals.icons.edit }}
              </v-icon>
              <!-- eslint-disable-next-line vue/no-v-html -->
              <span v-html="yieldDisplay" />
            </v-card>
          </template>
          <v-card min-width="300px">
            <v-card-title class="mb-0">
              {{ $t("recipe.servings") }}
            </v-card-title>
            <v-card-text class="mt-n5">
              <div class="mt-4 d-flex align-center">
                <v-number-input
                  :model-value="yieldQuantity"
                  :precision="null"
                  :min="0"
                  variant="underlined"
                  control-variant="hidden"
                  @update:model-value="recalculateScale($event || 0)"
                />
                <v-tooltip
                  location="end"
                  color="secondary-darken-1"
                >
                  <template #activator="{ props: resetTooltipProps }">
                    <v-btn
                      v-bind="resetTooltipProps"
                      icon
                      flat
                      class="mx-1"
                      size="small"
                      @click="scale = 1"
                    >
                      <v-icon>
                        {{ $globals.icons.undo }}
                      </v-icon>
                    </v-btn>
                  </template>
                  <span> {{ $t("recipe.reset-servings-count") }} </span>
                </v-tooltip>
              </div>
              <div class="mt-3">
                <v-select
                  v-model="selectedIngredientKey"
                  :items="ingredientScaleOptions"
                  item-title="label"
                  item-value="key"
                  density="compact"
                  variant="underlined"
                  hide-details
                  :label="$t('recipe.based-on-ingredient')"
                />

                <div v-if="selectedIngredientOption" class="mt-2">
                  <v-number-input
                    :model-value="ingredientQuantityInput"
                    :precision="null"
                    :min="0"
                    density="compact"
                    variant="underlined"
                    control-variant="hidden"
                    :label="$t('recipe.quantity')"
                    @update:model-value="updateIngredientQuantity"
                  />

                  <v-select
                    v-if="showCompatibleUnitSelect"
                    v-model="selectedUnitId"
                    :items="compatibleUnits"
                    item-title="name"
                    item-value="id"
                    density="compact"
                    variant="underlined"
                    hide-details
                    class="mt-2"
                    :label="$t('recipe.unit')"
                  />
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-menu>
      </div>
      <BaseButtonGroup
        v-if="canEditScale"
        class="pl-2"
        :large="false"
        :buttons="[
          {
            icon: $globals.icons.minus,
            text: $t('recipe.decrease-scale-label'),
            event: 'decrement',
            disabled: disableDecrement,
          },
          {
            icon: $globals.icons.createAlt,
            text: $t('recipe.increase-scale-label'),
            event: 'increment',
          },
        ]"
        @decrement="recalculateScale(yieldQuantity - 1)"
        @increment="recalculateScale(yieldQuantity + 1)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useIngredientTextParser } from "~/composables/recipes/use-recipe-ingredients";
import { useScaledAmount } from "~/composables/recipes/use-scaled-amount";
import { useUnitStore } from "~/composables/store";
import type { IngredientUnit, RecipeIngredient } from "~/lib/api/types/recipe";

interface Props {
  recipeServings?: number;
  editScale?: boolean;
  recipeIngredients?: RecipeIngredient[];
}
const props = withDefaults(defineProps<Props>(), {
  recipeServings: 0,
  editScale: false,
  recipeIngredients: () => [],
});

interface IngredientScaleOption {
  key: string;
  label: string;
  quantityPerServing: number | null;
  unit: RecipeIngredient["unit"];
}

const scale = defineModel<number>({ required: true });

const i18n = useI18n();
const { parseIngredientText } = useIngredientTextParser();
const { store: unitStore } = useUnitStore(i18n);
const menu = ref<boolean>(false);
const selectedIngredientKey = ref<string | null>(null);
const selectedUnitId = ref<string | null>(null);
const ingredientQuantityInput = ref<number | null>(null);
const canEditScale = computed(() => props.editScale && props.recipeServings > 0);

function unitConversionKey(unit: RecipeIngredient["unit"]): string {
  if (!unit) {
    return "none";
  }

  return unit.id || unit.name || "none";
}

function ingredientDisplayName(ingredient: RecipeIngredient): string {
  return ingredient.food?.name
    || ingredient.display
    || ingredient.originalText
    || ingredient.note
    || i18n.t("recipe.ingredient").toString();
}

function formatIngredientOptionLabel(ingredient: RecipeIngredient, quantityForOriginalRecipe: number | null): string {
  const labelIngredient: RecipeIngredient = {
    ...ingredient,
    quantity: quantityForOriginalRecipe,
  };

  const parsedText = parseIngredientText(labelIngredient, 1, false, false);
  const ingredientText = parsedText || ingredientDisplayName(ingredient);

  return ingredientText;
}

function walkIngredients(
  ingredients: RecipeIngredient[],
  multiplier: number,
  out: Array<{ ingredient: RecipeIngredient; effectiveQuantity: number | null }>,
) {
  for (const ingredient of ingredients) {
    if (ingredient.referencedRecipe?.recipeIngredient?.length) {
      const referencedServings = ingredient.referencedRecipe.recipeServings || 1;
      const referenceQuantity = ingredient.quantity || 1;
      const nestedMultiplier = multiplier * (referenceQuantity / referencedServings);
      walkIngredients(ingredient.referencedRecipe.recipeIngredient, nestedMultiplier, out);
      continue;
    }

    const quantity = typeof ingredient.quantity === "number"
      ? ingredient.quantity * multiplier
      : null;

    if (quantity) {
      out.push({ ingredient, effectiveQuantity: quantity });
    }
  }
}

const ingredientScaleOptions = computed<IngredientScaleOption[]>(() => {
  const servings = props.recipeServings;
  const flattened: Array<{ ingredient: RecipeIngredient; effectiveQuantity: number | null }> = [];
  walkIngredients(props.recipeIngredients || [], 1, flattened);

  const merged = new Map<string, IngredientScaleOption>();

  for (const row of flattened) {
    const ingredient = row.ingredient;
    const unitKey = unitConversionKey(ingredient.unit);
    const ingredientKey = ingredient.food?.id
      || ingredient.food?.name
      || ingredient.originalText
      || ingredient.note
      || ingredient.referenceId
      || ingredientDisplayName(ingredient);
    const key = `${ingredientKey}::${unitKey}`;

    const quantityPerServing = row.effectiveQuantity !== null && servings > 0
      ? row.effectiveQuantity / servings
      : null;
    const quantityForOriginalRecipe = quantityPerServing !== null && servings > 0
      ? quantityPerServing * servings
      : null;

    if (!merged.has(key)) {
      merged.set(key, {
        key,
        label: formatIngredientOptionLabel(ingredient, quantityForOriginalRecipe),
        quantityPerServing,
        unit: ingredient.unit,
      });
      continue;
    }

    const existing = merged.get(key);
    if (!existing) {
      continue;
    }

    if (existing.quantityPerServing !== null && quantityPerServing !== null) {
      existing.quantityPerServing += quantityPerServing;
      existing.label = formatIngredientOptionLabel(ingredient, existing.quantityPerServing * servings);
    }
  }

  return [...merged.values()].sort((a, b) => a.label.localeCompare(b.label));
});

const selectedIngredientOption = computed(() => {
  return ingredientScaleOptions.value.find(option => option.key === selectedIngredientKey.value) || null;
});

const compatibleUnits = computed<IngredientUnit[]>(() => {
  const standardUnit = selectedIngredientOption.value?.unit?.standardUnit;
  if (!standardUnit) {
    return [];
  }

  return unitStore.value.filter(unit => unit.standardUnit === standardUnit);
});

const showCompatibleUnitSelect = computed(() => {
  return !!selectedIngredientOption.value?.unit?.standardUnit;
});

function findMatchingUnitId(sourceUnit: RecipeIngredient["unit"]): string | null {
  if (!sourceUnit) {
    return null;
  }

  if (sourceUnit.id && compatibleUnits.value.some(unit => unit.id === sourceUnit.id)) {
    return sourceUnit.id;
  }

  const byName = compatibleUnits.value.find(unit => unit.name === sourceUnit.name);
  if (byName) {
    return byName.id;
  }

  return compatibleUnits.value[0]?.id || null;
}

function updateIngredientQuantity(value: number | string | null | undefined) {
  if (value === null || value === undefined || value === "") {
    ingredientQuantityInput.value = null;
    return;
  }

  const quantity = Number(value);
  ingredientQuantityInput.value = isNaN(quantity) ? null : quantity;
}

function calculateServingsFromIngredient() {
  const ingredient = selectedIngredientOption.value;
  const userQuantity = ingredientQuantityInput.value;
  let quantityPerServing = ingredient?.quantityPerServing;
  if (!ingredient
    || !userQuantity || userQuantity <= 0 || isNaN(userQuantity)
    || !quantityPerServing || quantityPerServing <= 0) {
    return;
  }

  if (ingredient.unit?.standardUnit) {
    const selectedUnit = compatibleUnits.value.find(unit => unit.id === selectedUnitId.value);
    if (!selectedUnit?.standardQuantity || !ingredient.unit.standardQuantity) {
      return;
    }

    quantityPerServing = quantityPerServing * (ingredient.unit.standardQuantity / selectedUnit.standardQuantity);
    if (!quantityPerServing || quantityPerServing <= 0) {
      return;
    }
  }

  recalculateScale(userQuantity / quantityPerServing);
}

watch(selectedIngredientOption, (option) => {
  ingredientQuantityInput.value = null;

  if (!option || !option.unit?.standardUnit) {
    selectedUnitId.value = null;
    return;
  }

  selectedUnitId.value = findMatchingUnitId(option.unit);
});

watch(compatibleUnits, () => {
  if (!selectedIngredientOption.value?.unit?.standardUnit) {
    return;
  }

  if (!selectedUnitId.value || !compatibleUnits.value.some(unit => unit.id === selectedUnitId.value)) {
    selectedUnitId.value = findMatchingUnitId(selectedIngredientOption.value.unit);
  }
});

watch([ingredientQuantityInput, selectedUnitId, selectedIngredientOption], () => {
  calculateServingsFromIngredient();
});

watch(menu, (isOpen) => {
  if (!isOpen) {
    selectedIngredientKey.value = null;
    selectedUnitId.value = null;
    ingredientQuantityInput.value = null;
  }
});

function recalculateScale(newYield: number) {
  if (isNaN(newYield) || newYield <= 0) {
    return;
  }

  if (props.recipeServings <= 0) {
    scale.value = 1;
  }
  else {
    scale.value = newYield / props.recipeServings;
  }
}

const recipeYieldAmount = computed(() => {
  return useScaledAmount(props.recipeServings, scale.value);
});
const yieldQuantity = computed(() => recipeYieldAmount.value.scaledAmount);
const yieldDisplay = computed(() => {
  return yieldQuantity.value
    ? i18n.t(
      "recipe.serves-amount", { amount: recipeYieldAmount.value.scaledAmountDisplay },
    ) as string
    : "";
});

const disableDecrement = computed(() => {
  return yieldQuantity.value <= 1;
});
</script>
