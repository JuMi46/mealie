<template>
  <v-sheet class="timer-input-row d-flex mt-3">
    <v-text-field
      :model-value="hours"
      :label="$t('timer.hours')"
      type="number"
      class="timer-number-field"
      min="0"
      max="99"
      outlined
      dense
      hide-details
      @update:model-value="handleHoursInput"
    />
    <v-text-field
      :model-value="minutes"
      :label="$t('timer.minutes')"
      type="number"
      class="timer-number-field"
      min="0"
      max="59"
      outlined
      dense
      hide-details
      @update:model-value="handleMinutesInput"
    />
    <v-text-field
      :model-value="seconds"
      :label="$t('timer.seconds')"
      type="number"
      class="timer-number-field"
      min="0"
      max="59"
      outlined
      dense
      hide-details
      @update:model-value="handleSecondsInput"
    />
    <v-text-field
      :model-value="modelValue.text"
      :label="$t('timer.text')"
      type="text"
      class="timer-text-field"
      outlined
      dense
      hide-details
      clearable
      @update:model-value="modelValue.text = $event"
    />
  </v-sheet>
</template>

<script setup lang="ts">
import type { RecipeTimer } from "~/lib/api/types/recipe";

const modelValue = defineModel<RecipeTimer>({ required: true });

const hours = ref(0);
const minutes = ref(0);
const seconds = ref(0);

watch(() => modelValue, (newVal) => {
  if (newVal.value) {
    hours.value = Math.floor(newVal.value.duration / 3600);
    minutes.value = Math.floor((newVal.value.duration % 3600) / 60);
    seconds.value = newVal.value.duration % 60;
  }
}, { immediate: true });

function handleHoursInput(value: string) {
  hours.value = Math.min(99, Number(value));
  updateSeconds();
}

function handleMinutesInput(value: string) {
  minutes.value = Math.min(59, Number(value));
  updateSeconds();
}

function handleSecondsInput(value: string) {
  seconds.value = Math.min(59, Number(value));
  updateSeconds();
}

function updateSeconds() {
  const totalSeconds
    = Number(hours.value) * 3600 + Number(minutes.value) * 60 + Number(seconds.value);
  modelValue.value.duration = totalSeconds;
}
</script>

<style scoped>
.timer-input-row {
  --timer-gap: 8px;
  --timer-number-width: 80px;

  flex-wrap: wrap;
  gap: var(--timer-gap);
  flex-grow: 1;
}

.timer-number-field {
  flex: 0 0 var(--timer-number-width);
  width: var(--timer-number-width);
}

.timer-text-field {
  flex-grow: 1;
  min-width: calc(var(--timer-number-width) * 2 + var(--timer-gap) * 2);
}
</style>
