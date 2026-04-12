<template>
  <v-sheet max-width="300" class="d-flex align-center justify-space-between mt-3">
    <v-icon class="mr-2">mdi-alarm</v-icon>
    <v-text-field
      v-model="hours"
      :label="$t('timer.hours')"
      type="number"
      class="mr-2"
      min="0"
      max="23"
      outlined
      dense
      hide-details
      @input="updateSeconds()"
    ></v-text-field>
    <v-text-field
      :value="minutes"
      :label="$t('timer.minutes')"
      type="number"
      class="mr-2"
      min="0"
      max="59"
      outlined
      dense
      hide-details
      @input="minutes = Math.min(60, Number($event)); updateSeconds()"
    ></v-text-field>
    <v-text-field
      :value="seconds"
      :label="$t('timer.seconds')"
      type="number"
      min="0"
      max="59"
      outlined
      dense
      hide-details
      @input="seconds = Math.min(60, Number($event)); updateSeconds()"
    ></v-text-field>
  </v-sheet>
</template>

<script>
export default {
  props: {
    value: Number,
  },
  data() {
    return {
      hours: 0,
      minutes: 0,
      seconds: 0,
    };
  },
  watch: {
    value: {
      immediate: true,
      handler(newVal) {
        this.hours = Math.floor(newVal / 3600);
        this.minutes = Math.floor((newVal % 3600) / 60);
        this.seconds = newVal % 60;
      },
    },
  },
  methods: {
    updateSeconds() {
      const totalSeconds =
        Number(this.hours) * 3600 + Number(this.minutes) * 60 + Number(this.seconds);
      this.$emit("input", totalSeconds);
    },
  },
};
</script>

<style scoped>
.v-card {
  display: flex;
  justify-content: space-around;
}
</style>
