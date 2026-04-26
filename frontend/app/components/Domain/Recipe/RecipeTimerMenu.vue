<template>
  <div class="text-center">
    <v-menu
      v-model="showMenu"
      offset-x
      offset-overflow
      left
      allow-overflow
      close-delay="125"
      :close-on-content-click="false"
      content-class="d-print-none"
      :z-index="2"
    >
      <template #activator="{ props: activatorProps }">
        <v-badge :value="timerEnded" overlap color="red" content="!">
          <v-btn
            :fab="fab"
            :small="fab"
            :color="timerEnded ? 'secondary' : color"
            :icon="!fab"
            dark
            v-bind="activatorProps"
            @click.prevent
          >
            <v-progress-circular
              v-if="timerInitialized && !timerEnded"
              :value="timerProgress"
              :rotate="270"
              :color="timerRunning ? undefined : 'primary'"
            >
              <v-icon small>
                {{ timerRunning ? $globals.icons.timer : $globals.icons.timerPause }}
              </v-icon>
            </v-progress-circular>
            <v-icon v-else>
              {{ $globals.icons.timer }}
            </v-icon>
          </v-btn>
        </v-badge>
      </template>
      <v-card>
        <v-card-title>
          <v-icon class="pr-2">
            {{ $globals.icons.timer }}
          </v-icon>
          {{ $t("recipe.timer.kitchen-timer") }}
        </v-card-title>
        <div class="mx-auto" style="width: fit-content;">
          <v-progress-circular
            :value="timerProgress"
            :rotate="270"
            color="primary"
            class="mb-2"
            :size="128"
            :width="24"
          >
            <v-icon
              v-if="timerInitialized && !timerRunning"
              x-large
              :color="timerEnded ? 'red' : 'primary'"
              @click="() => timerEnded ? resetTimer() : resumeTimer()"
            >
              {{ timerEnded ? $globals.icons.stop : $globals.icons.pause }}
            </v-icon>
          </v-progress-circular>
        </div>
        <v-container width="100%" fluid class="ma-0 px-auto py-2">
          <v-row no-gutters justify="center">
            <v-col cols="3" align-self="center">
              <v-text-field
                :value="timerHours"
                :min="0"
                outlined
                single-line
                solo
                hide-details
                type="number"
                :disabled="timerInitialized"
                class="centered-input my-0 py-0"
                style="font-size: large; width: 100px;"
                @input="(v) => timerHours = v.toString().padStart(2, '0')"
              />
            </v-col>
            <v-col cols="1" align-self="center" style="text-align: center;">
              <h1>:</h1>
            </v-col>
            <v-col cols="3" align-self="center">
              <v-text-field
                :value="timerMinutes"
                :min="0"
                outlined
                single-line
                solo
                hide-details
                type="number"
                :disabled="timerInitialized"
                class="centered-input my-0 py-0"
                style="font-size: large; width: 100px;"
                @input="(v) => timerMinutes = v.toString().padStart(2, '0')"
              />
            </v-col>
            <v-col cols="1" align-self="center" style="text-align: center;">
              <h1>:</h1>
            </v-col>
            <v-col cols="3" align-self="center">
              <v-text-field
                :value="timerSeconds"
                :min="0"
                outlined
                single-line
                solo
                hide-details
                type="number"
                :disabled="timerInitialized"
                class="centered-input my-0 py-0"
                style="font-size: large; width: 100px;"
                @input="(v) => timerSeconds = v.toString().padStart(2, '0')"
              />
            </v-col>
          </v-row>
        </v-container>
        <div class="mx-auto" style="width: 100%;">
          <BaseButtonGroup
            stretch
            :buttons="timerButtons"
            @initialize-timer="startTimer"
            @pause-timer="pauseTimer"
            @resume-timer="resumeTimer"
            @stop-timer="resetTimer"
          />
        </div>
      </v-card>
    </v-menu>
  </div>
</template>

<script setup lang="ts">
import type { ButtonOption } from "~/components/global/BaseButtonGroup.vue";
import useTimer from "~/composables/use-timer";

interface Props {
  fab?: boolean;
  color?: string;
}
withDefaults(defineProps<Props>(), {
  fab: false,
  color: "primary",
});

const i18n = useI18n();
const { $globals } = useNuxtApp();
const timer = useTimer("00", "00", "00", { padTimes: true });

const showMenu = ref(false);

const {
  timerInitialized,
  timerRunning,
  timerEnded,
  timerHours,
  timerMinutes,
  timerSeconds,
  timerProgress,
  pauseTimer,
  resumeTimer,
  resetTimer,
  startTimer,
} = toRefs(timer);

watch(
  () => showMenu,
  () => {
    if (showMenu.value && timer.timerEnded) {
      timer.resetTimer();
    }
  },
);

const initializeButton: ButtonOption = {
  icon: $globals.icons.timerPlus,
  text: i18n.t("recipe.timer.start-timer"),
  event: "initialize-timer",
};

const pauseButton: ButtonOption = {
  icon: $globals.icons.pause,
  text: i18n.t("recipe.timer.pause-timer"),
  event: "pause-timer",
};

const resumeButton: ButtonOption = {
  icon: $globals.icons.play,
  text: i18n.t("recipe.timer.resume-timer"),
  event: "resume-timer",
};

const stopButton: ButtonOption = {
  icon: $globals.icons.stop,
  text: i18n.t("recipe.timer.stop-timer"),
  event: "stop-timer",
  color: "red",
};

const timerButtons = computed<ButtonOption[]>(() => {
  const buttons: ButtonOption[] = [];
  if (timer.timerInitialized) {
    if (timer.timerEnded) {
      buttons.push(stopButton);
    }
    else if (timer.timerRunning) {
      buttons.push(pauseButton, stopButton);
    }
    else {
      buttons.push(resumeButton, stopButton);
    }
  }
  else {
    buttons.push(initializeButton);
  }

  // I don't know why this is failing the frontend lint test ¯\_(ツ)_/¯

  return buttons;
});
</script>

<style scoped>
    .centered-input >>> input {
  text-align: center;
}
</style>
