<template v-if="timers && timers.length">
  <div class="mb-n4" @click.stop>
    <v-divider class="mb-2 mt-3 mb-2" />
    <div
      v-for="(timer, i) in compTimers"
      :key="i"
      class="d-flex align-center my-2 justify-center"
    >
      <v-icon
        v-if="!timer.timerRunning && !timer.timerPaused"
        :color="timer.timerEnded ? 'success' : ''"
        :class="timer.timerEnded ? 'shake' : ''"
      >
        {{ $globals.icons.alarm }}
      </v-icon>
      <v-icon
        v-else
        color="primary"
        :class="timer.timerRunning ? 'tick' : ''"
      >
        {{ $globals.icons.alarm }}
      </v-icon>

      {{ timer.timerText }}
      <v-btn
        icon
        :disabled="timer.timerValue <= 30"
        depressed
        @click="changeTimerValue(timer, timer.timerValue - 30)"
      >
        <v-icon>{{ $globals.icons.minus }}</v-icon>
      </v-btn>
      {{ timer.simpleDisplayValue }}
      <v-btn
        icon
        depressed
        @click="changeTimerValue(timer, timer.timerValue + 30)"
      >
        <v-icon>{{ $globals.icons.createAlt }}</v-icon>
      </v-btn>
      <v-btn
        v-if="!timer.timerRunning && !timer.timerPaused && !timer.timerEnded"
        rounded
        depressed
        @click="startTimer(timer)"
      >
        {{ $t("recipe.timer.start-timer") }}
      </v-btn>
      <template v-else>
        <v-btn
          v-if="(!timer.timerEnded && timer.timerRunning && !timer.timerPaused)"
          rounded
          depressed
          @click="pauseTimer(timer)"
        >
          {{ $t("recipe.timer.pause") }}
        </v-btn>
        <span v-else-if="!timer.timerEnded">
          <v-btn
            rounded
            depressed
            @click="resumeTimer(timer)"
          >
            {{ $t("recipe.timer.continue") }}
          </v-btn>
          <v-btn
            icon
            @click="timer.resetTimer"
          ><v-icon>{{ $globals.icons.restore }}</v-icon></v-btn>
        </span>
        <span v-else>
          <v-btn
            icon
            @click="timer.resetTimer"
          ><v-icon>{{ $globals.icons.restore }}</v-icon></v-btn>
        </span>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import useTimer from "~/composables/use-timer";
import type { RecipeTimer, RecipeTimerActiveIn, RecipeTimerActiveUpdate } from "~/lib/api/types/recipe";

interface Props {
  timers?: RecipeTimer[];
}
const props = withDefaults(defineProps<Props>(), {
  timers: () => [],
});

const userApi = useUserApi();

const compTimers = ref<ReturnType<typeof useTimer>[]>();

watch(() => props.timers, (newTimers) => {
  console.log("new timers", newTimers);

  compTimers.value = newTimers.map((t) => {
    const newTimer = useTimer("00", "00", t.duration.toString(), { padTimes: false }, t.text, null, t.id, t.timersActive);
    newTimer.initializeTimer();
    return newTimer;
  });
}, { immediate: true });

function startTimer(timer: ReturnType<typeof useTimer>) {
  timer.startTimer();
  saveTimerActive(timer);
}

function pauseTimer(timer: ReturnType<typeof useTimer>) {
  timer.pauseTimer();
  deleteTimerActive(timer);
}

function resumeTimer(timer: ReturnType<typeof useTimer>) {
  timer.resumeTimer();
  saveTimerActive(timer);
}

function changeTimerValue(timer: ReturnType<typeof useTimer>, newValue: number) {
  timer.timerValue = newValue;
  if (timer.timerRunning) {
    updateTimerActive(timer);
  }
}

function saveTimerActive(timer: ReturnType<typeof useTimer>) {
  if (!timer.recipeTimerId) return;

  const newTimerActive: RecipeTimerActiveIn = {
    completeTime: new Date(Date.now() + timer.timerValue * 1000).toISOString(),
    text: timer.timerText,
  };

  userApi.recipes.timersActive.createTimerActive(timer.recipeTimerId, newTimerActive)
    .then((response) => {
      timer.recipeTimerActiveId = response.data.id;
      console.log("timer saved", response.data);
    })
    .catch((error) => {
      console.error("Failed to save active timer:", error);
    });
}

function updateTimerActive(timer: ReturnType<typeof useTimer>) {
  if (!timer.recipeTimerActiveId) return;
  const updatedTimerActive: RecipeTimerActiveUpdate = {
    completeTime: new Date(Date.now() + timer.timerValue * 1000).toISOString(),
  };

  userApi.recipes.timersActive.updateTimerActive(timer.recipeTimerActiveId, updatedTimerActive)
    .then((response) => {
      console.log("timer updated", response.data);
    })
    .catch((error) => {
      console.error("Failed to update active timer:", error);
    });
}

function deleteTimerActive(timer: ReturnType<typeof useTimer>) {
  if (!timer.recipeTimerActiveId) return;

  userApi.recipes.timersActive.deleteTimerActive(timer.recipeTimerActiveId)
    .then((response) => {
      timer.recipeTimerActiveId = "";
      console.log("timer deleted", response.data);
    })
    .catch((error) => {
      console.error("Failed to delete active timer:", error);
    });
}
</script>

<style scoped>
.tick {
  animation: tick 4s linear infinite;
}

@keyframes tick {
  0% {
    transform: rotate(15deg);
  }

  25% {
    transform: rotate(-15deg);
  }

  50% {
    transform: rotate(15deg);
  }

  75% {
    transform: rotate(-15deg);
  }

  100% {
    transform: rotate(15deg);
  }
}

.shake {
  animation: shake 0.82s cubic-bezier(0.36, 0.07, 0.19, 0.97) infinite;
}

@keyframes shake {
  10%,
  90% {
    transform: translate3d(-1px, 0, 0);
  }

  20%,
  80% {
    transform: translate3d(2px, 0, 0);
  }

  30%,
  50%,
  70% {
    transform: translate3d(-4px, 0, 0);
  }

  40%,
  60% {
    transform: translate3d(4px, 0, 0);
  }
}
</style>
