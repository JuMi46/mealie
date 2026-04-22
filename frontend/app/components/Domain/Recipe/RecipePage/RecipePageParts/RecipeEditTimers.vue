<template>
  <div>
    <template v-for="time, index in modelValue" :key="index">
      <div class="timer-wrapper d-flex align-center">
        <v-icon>
          {{ $globals.icons.alarm }}
        </v-icon>
        <TimerInput v-model="modelValue[index]" class="mb-3" />
        <v-btn icon class="ml-2" @click="deleteTimer(index)">
          <v-icon>{{ $globals.icons.delete }}</v-icon>
        </v-btn>
      </div>
    </template>
    <BaseButton
      :icon="$globals.icons.timerPlus"
      :text="$t('recipe.timer.add-timer')"
      @click="addTimer"
    />
  </div>
</template>

<script setup lang="ts">
import type { RecipeTimer } from "~/lib/api/types/recipe";
import TimerInput from "./TimerInput.vue";

const modelValue = defineModel<RecipeTimer[]>({ required: true });

function addTimer() {
  modelValue.value = [...modelValue.value, { id: uuid4(), duration: 0, text: "", timersActive: [] }];
}

function deleteTimer(index: number) {
  modelValue.value = [...modelValue.value.slice(0, index), ...modelValue.value.slice(index + 1)];
}
</script>

<style scoped>
.timer-wrapper {
  gap: 8px;
}
</style>
