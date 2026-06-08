<template>
  <template v-if="showCalculator">
    <div class="d-flex gap-2 px-2">
      <v-text-field
        v-model.number="volumeQty"
        type="number"
        variant="underlined"
        density="comfortable"
        :label="$t('data-pages.foods.volume-quantity')"
        :min="0.0001"
        step="any"
        style="flex: 1"
      />
      <v-autocomplete
        v-model="volumeUnit"
        return-object
        :items="volumeUnits"
        :custom-filter="normalizeFilter"
        item-title="name"
        :label="$t('data-pages.foods.volume-unit')"
        variant="solo-filled"
        flat
        density="comfortable"
        style="flex: 2"
      />
    </div>
    <div class="d-flex gap-2 px-2">
      <v-text-field
        v-model.number="massQty"
        type="number"
        variant="underlined"
        density="comfortable"
        :label="$t('data-pages.foods.mass-quantity')"
        :min="0.0001"
        step="any"
        style="flex: 1"
      />
      <v-autocomplete
        v-model="massUnit"
        return-object
        :items="massUnits"
        :custom-filter="normalizeFilter"
        item-title="name"
        :label="$t('data-pages.foods.mass-unit')"
        variant="solo-filled"
        flat
        density="comfortable"
        style="flex: 2"
      />
    </div>
  </template>

  <div class="d-flex align-center gap-2 px-2 pb-2">
    <v-text-field
      v-model.number="densityValue"
      type="number"
      variant="underlined"
      density="comfortable"
      :label="$t('data-pages.foods.density')"
      :min="0"
      step="any"
      style="flex: 1"
    />
    <BaseButton
      color="secondary"
      class="mb-2"
      @click="showCalculator = !showCalculator"
    >
      <template #icon>
        {{ $globals.icons.testTube }}
      </template>
      {{ $t('data-pages.foods.calculate-density') }}
    </BaseButton>
  </div>
</template>

<script setup lang="ts">
import type { IngredientUnit } from "~/lib/api/types/recipe";
import { convertToGram, convertToMilliliter } from "~/composables/recipes/use-recipe-ingredients";
import { normalizeFilter } from "~/composables/use-utils";

const props = withDefaults(defineProps<{
  modelValue?: number | null;
  volumeUnits: IngredientUnit[];
  massUnits: IngredientUnit[];
  defaultMassUnitId?: string | null;
  resetKey?: string | number;
}>(), {
  modelValue: null,
  defaultMassUnitId: null,
  resetKey: "",
});

const emit = defineEmits<{
  "update:modelValue": [value: number | undefined];
}>();

const showCalculator = ref(false);
const volumeQty = ref<number | null>(null);
const volumeUnit = ref<IngredientUnit | null>(null);
const massQty = ref<number | null>(null);
const massUnit = ref<IngredientUnit | null>(null);

const densityValue = computed<number | null>({
  get() {
    return props.modelValue ?? null;
  },
  set(value) {
    emit("update:modelValue", value ?? undefined);
  },
});

function applyDefaultMassUnit() {
  if (!props.defaultMassUnitId) {
    massUnit.value = null;
    return;
  }

  massUnit.value = props.massUnits.find(unit => unit.id === props.defaultMassUnitId) ?? null;
}

function resetCalculator() {
  showCalculator.value = false;
  volumeQty.value = null;
  volumeUnit.value = null;
  massQty.value = null;
  applyDefaultMassUnit();
}

watch(
  () => props.resetKey,
  () => {
    resetCalculator();
  },
);

watch(
  () => [props.defaultMassUnitId, props.massUnits] as const,
  () => {
    if (!massUnit.value || !props.massUnits.some(unit => unit.id === massUnit.value?.id)) {
      applyDefaultMassUnit();
    }
  },
  { deep: true },
);

watch(
  [volumeQty, volumeUnit, massQty, massUnit],
  () => {
    if (!volumeQty.value || !volumeUnit.value || !massQty.value || !massUnit.value) {
      return;
    }

    const ml = convertToMilliliter(volumeQty.value, volumeUnit.value);
    const grams = convertToGram(massQty.value, massUnit.value);

    if (ml && grams) {
      densityValue.value = Math.round((grams / ml) * 1000) / 1000;
    }
  },
);

onMounted(() => {
  applyDefaultMassUnit();
});
</script>
