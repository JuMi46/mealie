<template v-if="timers && timers.length">
  <div class="mb-n4" @click.stop>
    <v-divider class="mb-2 mt-3 mb-2" />
    <div
      v-for="(timer, i) in compTimers"
      :id="timer.recipeTimerId ? `recipe-timer-${timer.recipeTimerId}` : undefined"
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
  isCookMode?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  timers: () => [],
  isCookMode: false,
});

const userApi = useUserApi();
const auth = useMealieAuth();
const route = useRoute();
const currentUserId = computed(() => auth.user.value?.id);
const showAllHouseholdTimersInRecipe = computed(() => auth.user.value?.showAllHouseholdTimersInRecipe ?? false);
const timerRecipeLinkByActiveId = ref<Record<string, string>>({});
const stoppedByActiveScreenSentByActiveId = ref<Record<string, true>>({});
const timerThresholdWatcherStops = ref<Array<() => void>>([]);
const isScreenActive = ref(true);
const timerThreshold = 3; // seconds remaining while screen is active to trigger stop timer webhooks

const groupSlug = computed(() => (route.params.groupSlug as string | undefined) || auth.user.value?.groupSlug || "");
const recipeSlug = computed(() => (route.params.slug as string | undefined) || "");

const compTimers = ref<ReturnType<typeof useTimer>[]>();

watch([() => props.timers, currentUserId, showAllHouseholdTimersInRecipe], ([newTimers]) => {
  console.log("new timers", newTimers);

  compTimers.value = newTimers.map((t) => {
    const timersActive = showAllHouseholdTimersInRecipe.value
      ? t.timersActive
      : t.timersActive.filter(ta => ta.userId === currentUserId.value);

    const newTimer = useTimer("00", "00", t.duration.toString(), { padTimes: false }, t.text, null, t.id, timersActive);
    newTimer.initializeTimer();
    return newTimer;
  });
}, { immediate: true });

watch(compTimers, (timers) => {
  timerThresholdWatcherStops.value.forEach(stop => stop());
  timerThresholdWatcherStops.value = [];

  if (!timers?.length) {
    return;
  }

  timerThresholdWatcherStops.value = timers.map(timer =>
    watch(
      () => [timer.timerValue, timer.timerRunning, timer.timerEnded, timer.recipeTimerActiveId, isScreenActive.value],
      () => {
        if (!isScreenActive.value || !timer.timerRunning || timer.timerEnded || timer.timerValue !== timerThreshold) {
          return;
        }

        const activeId = timer.recipeTimerActiveId;
        if (!activeId || stoppedByActiveScreenSentByActiveId.value[activeId]) {
          return;
        }

        stoppedByActiveScreenSentByActiveId.value[activeId] = true;
        postStoppedWebhookForActiveTimer(timer);
      },
      { immediate: true },
    ),
  );
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

  const recipeLink = buildRecipeLink(timer.recipeTimerId, props.isCookMode);

  const newTimerActive: RecipeTimerActiveIn = {
    completeTime: new Date(Date.now() + timer.timerValue * 1000).toISOString(),
    text: timer.timerText,
    recipeLink,
  };

  userApi.recipes.timersActive.createTimerActive(timer.recipeTimerId, newTimerActive)
    .then((response) => {
      if (response.data) {
        timer.recipeTimerActiveId = response.data.id;
        timerRecipeLinkByActiveId.value[response.data.id] = recipeLink;
        const { [response.data.id]: _removed, ...rest } = stoppedByActiveScreenSentByActiveId.value;
        stoppedByActiveScreenSentByActiveId.value = rest;
      }
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

  const activeId = timer.recipeTimerActiveId;

  const recipeLink = timerRecipeLinkByActiveId.value[timer.recipeTimerActiveId] || buildRecipeLink(timer.recipeTimerId || "", props.isCookMode);

  userApi.recipes.timersActive.deleteTimerActive(timer.recipeTimerActiveId, { recipeLink })
    .then((response) => {
      if (activeId) {
        const { [activeId]: _removed, ...rest } = timerRecipeLinkByActiveId.value;
        timerRecipeLinkByActiveId.value = rest;

        const { [activeId]: _thresholdRemoved, ...thresholdRest } = stoppedByActiveScreenSentByActiveId.value;
        stoppedByActiveScreenSentByActiveId.value = thresholdRest;
      }
      timer.recipeTimerActiveId = "";
      console.log("timer deleted", response.data);
    })
    .catch((error) => {
      console.error("Failed to delete active timer:", error);
    });
}

function postStoppedWebhookForActiveTimer(timer: ReturnType<typeof useTimer>) {
  if (!timer.recipeTimerActiveId) return;

  const activeId = timer.recipeTimerActiveId;
  const recipeLink = timerRecipeLinkByActiveId.value[activeId] || buildRecipeLink(timer.recipeTimerId || "", props.isCookMode);

  userApi.recipes.timersActive.postStoppedWebhookForActiveTimer(activeId, { recipeLink })
    .then((response) => {
      console.log("stopped webhook triggered", response.data);
    })
    .catch((error) => {
      const { [activeId]: _thresholdRemoved, ...thresholdRest } = stoppedByActiveScreenSentByActiveId.value;
      stoppedByActiveScreenSentByActiveId.value = thresholdRest;
      console.error("Failed to trigger stopped webhook:", error);
    });
}

function buildRecipeLink(timerId: string, includeCookMode: boolean) {
  if (!groupSlug.value || !recipeSlug.value || !timerId) {
    return "";
  }

  const query = new URLSearchParams({ timerId });
  if (includeCookMode) {
    query.set("isCookMode", "true");
  }

  return `/g/${encodeURIComponent(groupSlug.value)}/r/${encodeURIComponent(recipeSlug.value)}?${query.toString()}`;
}

async function scrollToTimerFromQuery() {
  const timerId = typeof route.query.timerId === "string" ? route.query.timerId : "";
  if (!timerId) {
    return;
  }

  await nextTick();
  const target = document.getElementById(`recipe-timer-${timerId}`);
  if (target) {
    target.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

watch([() => compTimers.value, () => route.query.timerId], () => {
  scrollToTimerFromQuery();
}, { immediate: true });

function updateScreenActiveState() {
  isScreenActive.value = typeof document === "undefined"
    ? true
    : document.visibilityState === "visible";
}

onMounted(() => {
  updateScreenActiveState();
  document.addEventListener("visibilitychange", updateScreenActiveState);
});

onUnmounted(() => {
  timerThresholdWatcherStops.value.forEach(stop => stop());
  timerThresholdWatcherStops.value = [];
  document.removeEventListener("visibilitychange", updateScreenActiveState);
});
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
