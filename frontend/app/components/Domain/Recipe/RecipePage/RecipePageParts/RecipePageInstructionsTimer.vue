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

      <v-btn
        icon
        :disabled="timer.timerValue <= 30"
        depressed
        @click="timer.timerValue -= 30"
      >
        <v-icon>{{ $globals.icons.minus }}</v-icon>
      </v-btn>
      {{ timer.simpleDisplayValue }}
      <v-btn
        icon
        depressed
        @click="timer.timerValue += 30"
      >
        <v-icon>{{ $globals.icons.createAlt }}</v-icon>
      </v-btn>
      <v-btn
        v-if="!timer.timerRunning && !timer.timerPaused && !timer.timerEnded"
        rounded
        depressed
        @click="timer.startTimer"
      >
        {{ $t("recipe.timer.start-timer") }}
      </v-btn>
      <template v-else>
        <v-btn
          v-if="(!timer.timerEnded && timer.timerRunning && !timer.timerPaused)"
          rounded
          depressed
          @click="timer.pauseTimer"
        >
          {{ $t("recipe.timer.pause") }}
        </v-btn>
        <span v-else-if="!timer.timerEnded">
          <v-btn
            rounded
            depressed
            @click="timer.resumeTimer"
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
import useTimer from "~/composables/use-timer";

interface Props {
  timers?: number[];
}
const props = withDefaults(defineProps<Props>(), {
  timers: () => [],
});

const compTimers = ref<ReturnType<typeof useTimer>[]>();

watch(() => props.timers as number[], (newTimers) => {
  console.log("new timers", newTimers);

  compTimers.value = newTimers.map((t) => {
    const newTimer = useTimer("00", "00", t.toString(), { padTimes: false });
    newTimer.initializeTimer();
    return newTimer;
  });
}, { immediate: true });
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
