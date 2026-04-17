<template>
  <div>
    <template v-for="time, index in modelValue" :key="index">
      <div class="d-flex align-center">
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
import type { RecipeInstructionTimer } from "~/lib/api/types/recipe";
import TimerInput from "./TimerInput.vue";

const modelValue = defineModel<RecipeInstructionTimer[]>({ required: true });

function addTimer() {
  modelValue.value.push({ id: uuid4(), duration: 0, text: "" });
}

function deleteTimer(index: number) {
  modelValue.value = [...modelValue.value.slice(0, index), ...modelValue.value.slice(index + 1)];
}
</script>
