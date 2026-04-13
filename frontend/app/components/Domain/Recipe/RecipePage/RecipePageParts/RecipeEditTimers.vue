<template>
  <div>
    <template v-for="time, index in modelValue" :key="index">
      <div class="d-flex align-center">
        <TimerInput v-model="modelValue[index]" class="mb-3" />
        <v-btn icon class="ml-2" @click="modelValue = [...modelValue.slice(0, index), ...modelValue.slice(index + 1)]">
          <v-icon>{{ $globals.icons.delete }}</v-icon>
        </v-btn>
      </div>
    </template>
    <BaseButton
      :icon="$globals.icons.timerPlus"
      :text="$t('recipe.timer.add-timer')"
      @click="modelValue = [...modelValue, 0]"
    />
  </div>
</template>

<script setup lang="ts">
import TimerInput from "./TimerInput.vue";

const modelValue = defineModel<number[]>({ required: true });
</script>
