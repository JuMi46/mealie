<template>
  <div v-if="valueNotNull || edit">
    <v-card class="mt-2">
      <div class="d-flex">
        <v-card-title class="pt-2 pb-0">
          {{ $t("recipe.nutrition") }}
        </v-card-title>
        <BaseButton
          v-if="!edit"
          only-icon
          minor
          color="primary"
          @click="minimizeNutrition = !minimizeNutrition"
        >
          <template #icon>
            {{ minimizeNutrition ? $globals.icons.createAlt : $globals.icons.minus }}
          </template>
        </BaseButton>
      </div>
      <v-divider class="mx-2 my-1" />
      <v-card-text v-if="edit">
        <div
          v-for="(item, key, index) in modelValue"
          :key="index"
        >
          <v-number-input
            :model-value="modelValue[key]"
            group-separator=","
            decimal-separator="."
            :label="labels[key].label"
            :suffix="labels[key].suffix"
            density="compact"
            autocomplete="off"
            variant="underlined"
            control-variant="stacked"
            inset
            :precision="null"
            :min="0"
            @update:model-value="updateValue(key, $event)"
          />
        </div>
      </v-card-text>
      <v-list
        v-if="showViewer"
        density="compact"
        class="mt-0 pt-0"
      >
        <v-list-item
          v-for="(item, key, index) in renderedList"
          :key="index"
          style="min-height: 25px"
        >
          <v-list-item-title class="pl-2 d-flex">
            <div>{{ item.label }}</div>
            <div class="ml-auto mr-1">
              {{ item.value }}
            </div>
            <div>{{ item.suffix }}</div>
          </v-list-item-title>
        </v-list-item>
      </v-list>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { useNutritionLabels } from "~/composables/recipes";
import type { Nutrition } from "~/lib/api/types/recipe";
import type { NutritionLabelType } from "~/composables/recipes/use-recipe-nutrition";

interface Props {
  edit?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  edit: true,
});

const modelValue = defineModel<Nutrition>({ required: true });

const minimizeNutrition = ref(true);
const { labels } = useNutritionLabels();
const valueNotNull = computed(() => {
  let key: keyof Nutrition;
  for (key in modelValue.value) {
    if (modelValue.value[key] !== null) {
      return true;
    }
  }
  return false;
});

const showViewer = computed(() => !props.edit && valueNotNull.value);

function updateValue(key: number | string, event: Event) {
  modelValue.value = { ...modelValue.value, [key]: event };
}

const minimizedNutritionList = ["calories", "carbohydrateContent", "fiberContent", "proteinContent"]; // TODO: Make this list editable in settings
// Build a new list that only contains nutritional information that has a value
const renderedList = computed(() => {
  return Object.entries(labels).reduce((item: NutritionLabelType, [key, label]) => {
    if (modelValue.value[key]?.trim() && (!minimizeNutrition.value || minimizedNutritionList.includes(key))) {
      item[key] = {
        ...label,
        value: modelValue.value[key],
      };
    }
    return item;
  }, {});
});
</script>

<style lang="scss" scoped></style>
