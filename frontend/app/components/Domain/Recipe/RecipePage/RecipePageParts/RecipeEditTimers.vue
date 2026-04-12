<template>
  <div>
    <template v-for="time, index in value" :key="index">
      <div class="d-flex align-center">
        <TimerInput v-model="value[index]" class="mb-3" />
        <v-btn icon class="ml-2" @click="$emit('input', [...value.slice(0, index), ...value.slice(index + 1)])">
          <v-icon>mdi-delete</v-icon>
        </v-btn>
      </div>
    </template>
    <v-btn small @click="$emit('input', [...value, 0])">
      <v-icon>mdi-plus</v-icon> Add timer
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import TimerInput from "./TimerInput.vue";

defineProps({
  value: {
    type: Array, // or any other type that fits your needs
    required: true,
  },
});
</script>
