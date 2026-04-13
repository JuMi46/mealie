<template>
  <v-sheet max-width="300" class="d-flex align-center justify-space-between mt-3">
    <v-icon class="mr-2">
      {{ $globals.icons.alarm }}
    </v-icon>
    <v-text-field
      :model-value="hours"
      :label="$t('timer.hours')"
      type="number"
      class="mr-2"
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
      class="mr-2"
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
      min="0"
      max="59"
      outlined
      dense
      hide-details
      @update:model-value="handleSecondsInput"
    />
  </v-sheet>
</template>

<script setup lang="ts">
const modelValue = defineModel<number>();

const hours = ref(0);
const minutes = ref(0);
const seconds = ref(0);

watch(() => modelValue, (newVal) => {
  if (newVal.value) {
    hours.value = Math.floor(newVal.value / 3600);
    minutes.value = Math.floor((newVal.value % 3600) / 60);
    seconds.value = newVal.value % 60;
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
  modelValue.value = totalSeconds;
}
</script>

<style scoped>
.v-card {
  display: flex;
  justify-content: space-around;
}
</style>
