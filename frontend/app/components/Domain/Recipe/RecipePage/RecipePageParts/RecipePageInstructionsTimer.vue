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
            @click="resetTimer(timer)"
          ><v-icon>{{ $globals.icons.restore }}</v-icon></v-btn>
        </span>
        <span v-else>
          <v-btn
            icon
            @click="resetTimer(timer)"
          ><v-icon>{{ $globals.icons.restore }}</v-icon></v-btn>
        </span>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import useTimer from "~/composables/use-timer";
import type { RecipeTimer, RecipeTimerActive, RecipeTimerActiveCreate, RecipeTimerActiveUpdate } from "~/lib/api/types/recipe";

interface Props {
  timers?: RecipeTimer[];
  isCookMode?: boolean;
  stepTitle?: string;
}
const props = withDefaults(defineProps<Props>(), {
  timers: () => [],
  isCookMode: false,
  stepTitle: () => "",
});

const userApi = useUserApi();
const auth = useMealieAuth();
const route = useRoute();
const i18n = useI18n();
const runtimeConfig = useRuntimeConfig();
const currentUserId = computed(() => auth.user.value?.id);
const showAllHouseholdTimersInRecipe = computed(() => auth.user.value?.showAllHouseholdTimersInRecipe ?? false);
const timerRecipeLinkByActiveId = ref<Record<string, string>>({});
const stoppedByActiveScreenSentByActiveId = ref<Record<string, true>>({});
const timerThresholdWatcherStops = ref<Array<() => void>>([]);
const isScreenActive = ref(true);
const timerThreshold = 3; // seconds remaining while screen is active to trigger stop timer webhooks
const remoteTimerSyncInFlight = ref(false);
const timerActiveSocket = ref<WebSocket | null>(null);
const timerActiveSocketReconnectTimeout = ref<number | null>(null);
const timerActiveSocketHeartbeatInterval = ref<number | null>(null);
const isComponentUnmounted = ref(false);

const groupSlug = computed(() => (route.params.groupSlug as string | undefined) || auth.user.value?.groupSlug || "");
const recipeSlug = computed(() => (route.params.slug as string | undefined) || "");

const compTimers = ref<ReturnType<typeof useTimer>[]>();

interface TimerActiveSocketEvent {
  type: "timer-active";
  event: "created" | "updated" | "deleted";
  timerActive: RecipeTimerActive | Record<string, unknown>;
}

function normalizeSocketTimerActive(raw: RecipeTimerActive | Record<string, unknown>) {
  const data = raw as Record<string, unknown>;

  return {
    ...raw,
    completeTime: (data.completeTime ?? data.complete_time) as string,
    recipeTimerId: (data.recipeTimerId ?? data.recipe_timer_id ?? null) as string | null,
    userId: (data.userId ?? data.user_id) as string,
  } as RecipeTimerActive;
}

function remainingSecondsFromCompleteTime(completeTime: string) {
  return Math.floor((new Date(completeTime).getTime() - Date.now()) / 1000);
}

function syncExistingTimerFromActives(timer: ReturnType<typeof useTimer>, actives: RecipeTimerActive[]) {
  const activeTimer = actives[0];

  if (!activeTimer) {
    if (timer.recipeTimerActiveId) {
      if (timer.timerEnded) {
        // Active timer removal after completion means another mode dismissed the alarm.
        timer.resetTimer();
      }
      else if (timer.timerRunning) {
        timer.pauseTimer();
      }
    }
    timer.recipeTimerActiveId = "";
    return;
  }

  timer.recipeTimerActiveId = activeTimer.id;
  const remaining = remainingSecondsFromCompleteTime(activeTimer.completeTime);

  if (remaining > 0) {
    timer.updateTimerValue(remaining);
    if (!timer.timerRunning) {
      timer.resumeTimer();
    }
  }
  else {
    // Timer elapsed on another device but not yet dismissed.
    // Show as ended locally so the user can dismiss it.
    if (timer.timerRunning) {
      timer.pauseTimer();
    }
    timer.updateTimerValue(0);
    timer.timerEnded = true;
  }
}

watch([() => props.timers, currentUserId, showAllHouseholdTimersInRecipe], ([newTimers]) => {
  const currentTimers = compTimers.value ?? [];
  const timersById = new Map(currentTimers.map(timer => [timer.recipeTimerId, timer]));

  const nextTimers = newTimers.map((t) => {
    const allTimersActive = t.timersActive ?? [];
    const timersActive = showAllHouseholdTimersInRecipe.value
      ? allTimersActive
      : allTimersActive.filter(ta => ta.userId === currentUserId.value);

    const existing = timersById.get(t.id);
    if (existing) {
      existing.timerText = (t.text ?? null) as string | null;
      syncExistingTimerFromActives(existing, timersActive);
      return existing;
    }

    const newTimer = useTimer("00", "00", t.duration.toString(), { padTimes: false }, t.text, null, t.id, timersActive);
    newTimer.initializeTimer();
    return newTimer;
  });

  const nextTimerIds = new Set(nextTimers.map(timer => timer.recipeTimerId));
  currentTimers.forEach((timer) => {
    if (!nextTimerIds.has(timer.recipeTimerId)) {
      timer.resetTimer();
    }
  });

  compTimers.value = nextTimers;
}, { immediate: true, deep: true });

function getSourceTimerById(timerId: string | null | undefined) {
  if (!timerId) {
    return undefined;
  }

  return props.timers.find(sourceTimer => sourceTimer.id === timerId);
}

function getTimerActives(sourceTimer: RecipeTimer) {
  if (!sourceTimer.timersActive) {
    sourceTimer.timersActive = [];
  }

  return sourceTimer.timersActive;
}

function syncTimerActiveAdded(timerId: string | null | undefined, active: RecipeTimerActive) {
  const sourceTimer = getSourceTimerById(timerId);
  if (!sourceTimer) {
    return;
  }

  const actives = getTimerActives(sourceTimer);
  const existingIdx = actives.findIndex(item => item.id === active.id);

  if (existingIdx === -1) {
    actives.push(active);
    return;
  }

  actives.splice(existingIdx, 1, active);
}

function syncTimerActiveUpdated(activeId: string, completeTime: string) {
  props.timers.forEach((sourceTimer) => {
    const actives = getTimerActives(sourceTimer);
    const existing = actives.find(item => item.id === activeId);

    if (existing) {
      existing.completeTime = completeTime;
    }
  });
}

function syncTimerActiveRemoved(activeId: string) {
  props.timers.forEach((sourceTimer) => {
    const actives = getTimerActives(sourceTimer);
    const existingIdx = actives.findIndex(item => item.id === activeId);

    if (existingIdx !== -1) {
      actives.splice(existingIdx, 1);
    }
  });
}

async function refreshActiveTimersFromServer() {
  if (remoteTimerSyncInFlight.value || !props.timers.length) {
    return;
  }

  remoteTimerSyncInFlight.value = true;

  try {
    const { data } = await userApi.recipes.timersActive.getTimersActive();
    if (!data) {
      return;
    }

    const localTimerIds = new Set(props.timers.map(timer => timer.id));
    const activesByRecipeTimerId: Record<string, RecipeTimerActive[]> = {};

    data.forEach((activeTimer) => {
      const recipeTimerId = activeTimer.recipeTimerId;
      if (!recipeTimerId || !localTimerIds.has(recipeTimerId)) {
        return;
      }

      if (!activesByRecipeTimerId[recipeTimerId]) {
        activesByRecipeTimerId[recipeTimerId] = [];
      }

      activesByRecipeTimerId[recipeTimerId].push(activeTimer);
    });

    props.timers.forEach((sourceTimer) => {
      sourceTimer.timersActive = activesByRecipeTimerId[sourceTimer.id] ?? [];
    });
  }
  catch (error) {
    console.error("Failed to refresh active timers:", error);
  }
  finally {
    remoteTimerSyncInFlight.value = false;
  }
}

function normalizeSubPath(value: string) {
  if (!value) {
    return "";
  }

  const withLeadingSlash = value.startsWith("/") ? value : `/${value}`;
  return withLeadingSlash.endsWith("/") ? withLeadingSlash.slice(0, -1) : withLeadingSlash;
}

function isLocalHostName(hostname: string) {
  return hostname === "localhost" || hostname === "127.0.0.1" || hostname === "::1" || hostname === "0.0.0.0";
}

function buildTimerActiveWebSocketUrl() {
  let wsOrigin = window.location.origin;
  let subPath = normalizeSubPath(runtimeConfig.public.SUB_PATH || "");

  const apiUrl = runtimeConfig.public.API_URL;
  if (apiUrl) {
    try {
      const parsedApiUrl = new URL(apiUrl, window.location.origin);
      const browserHostIsLocal = isLocalHostName(window.location.hostname);
      const apiHostIsLocal = isLocalHostName(parsedApiUrl.hostname);

      if (apiHostIsLocal && !browserHostIsLocal) {
        // When API_URL is localhost but the browser is remote (phone/tablet),
        // map websocket host to the current page host while preserving API port.
        const rewrittenApiUrl = new URL(parsedApiUrl.toString());
        rewrittenApiUrl.hostname = window.location.hostname;
        wsOrigin = rewrittenApiUrl.origin;
      }
      else {
        wsOrigin = parsedApiUrl.origin;
      }

      const apiPath = parsedApiUrl.pathname.replace(/\/+$/, "");
      if (apiPath && apiPath !== "/" && apiPath !== "/api") {
        subPath = normalizeSubPath(apiPath);
      }
    }
    catch {
      // Fallback to current origin if API_URL is invalid.
    }
  }

  const wsUrl = new URL(wsOrigin);
  wsUrl.protocol = wsUrl.protocol === "https:" ? "wss:" : "ws:";
  wsUrl.pathname = `${subPath}/api/timers/ws/active`;

  if (auth.token.value) {
    wsUrl.searchParams.set("token", auth.token.value);
  }

  return wsUrl.toString();
}

function scheduleTimerActiveSocketReconnect() {
  if (isComponentUnmounted.value || timerActiveSocketReconnectTimeout.value) {
    return;
  }

  timerActiveSocketReconnectTimeout.value = window.setTimeout(() => {
    timerActiveSocketReconnectTimeout.value = null;
    connectTimerActiveSocket();
  }, 2000);
}

function clearTimerActiveSocketHeartbeat() {
  if (timerActiveSocketHeartbeatInterval.value) {
    clearInterval(timerActiveSocketHeartbeatInterval.value);
    timerActiveSocketHeartbeatInterval.value = null;
  }
}

function applyRemoteTimerActiveEvent(payload: TimerActiveSocketEvent) {
  if (payload.type !== "timer-active" || !payload.timerActive) {
    return;
  }

  const timerActive = normalizeSocketTimerActive(payload.timerActive);
  const recipeTimerId = timerActive.recipeTimerId;
  if (!recipeTimerId || !props.timers.some(timer => timer.id === recipeTimerId)) {
    return;
  }

  if (payload.event === "deleted") {
    syncTimerActiveRemoved(timerActive.id);
    return;
  }

  syncTimerActiveAdded(recipeTimerId, timerActive);
}

function connectTimerActiveSocket() {
  if (isComponentUnmounted.value || typeof window === "undefined") {
    return;
  }

  const existingSocket = timerActiveSocket.value;
  if (existingSocket && (existingSocket.readyState === WebSocket.OPEN || existingSocket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  const socket = new WebSocket(buildTimerActiveWebSocketUrl());
  timerActiveSocket.value = socket;

  socket.onopen = () => {
    refreshActiveTimersFromServer();

    clearTimerActiveSocketHeartbeat();
    timerActiveSocketHeartbeatInterval.value = window.setInterval(() => {
      if (socket.readyState === WebSocket.OPEN) {
        socket.send("ping");
      }
    }, 20000);
  };

  socket.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data) as TimerActiveSocketEvent;
      applyRemoteTimerActiveEvent(payload);
    }
    catch {
      // Ignore non-json or unexpected websocket payloads.
    }
  };

  socket.onclose = () => {
    if (timerActiveSocket.value === socket) {
      timerActiveSocket.value = null;
    }
    clearTimerActiveSocketHeartbeat();
    scheduleTimerActiveSocketReconnect();
  };

  socket.onerror = () => {
    socket.close();
  };
}

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

function resetTimer(timer: ReturnType<typeof useTimer>) {
  deleteTimerActive(timer);
  timer.resetTimer();
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

  const newTimerActive: RecipeTimerActiveCreate = {
    completeTime: new Date(Date.now() + timer.timerValue * 1000).toISOString(),
    text: resolveTimerWebhookText(timer),
    recipeLink,
  };

  userApi.recipes.timersActive.createTimerActive(timer.recipeTimerId, newTimerActive)
    .then((response) => {
      if (response.data) {
        timer.recipeTimerActiveId = response.data.id;
        syncTimerActiveAdded(timer.recipeTimerId, response.data);
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

function resolveTimerWebhookText(timer: ReturnType<typeof useTimer>) {
  if (compTimers.value?.length === 1 && !timer.timerText) {
    return `${props.stepTitle}`;
  }
  const timerIndex = compTimers.value?.indexOf(timer) ?? -1;
  const timerTitle = (timer.timerText || i18n.t("timer.timer-index", { index: timerIndex + 1 })).trim();
  return i18n.t("timer.step-title-and-timer-title", { stepTitle: props.stepTitle, timerTitle });
}

function updateTimerActive(timer: ReturnType<typeof useTimer>) {
  if (!timer.recipeTimerActiveId) return;

  const activeId = timer.recipeTimerActiveId;
  const recipeLink = timerRecipeLinkByActiveId.value[activeId] || buildRecipeLink(timer.recipeTimerId || "", props.isCookMode);

  const updatedTimerActive: RecipeTimerActiveUpdate = {
    completeTime: new Date(Date.now() + timer.timerValue * 1000).toISOString(),
    recipeLink,
  };

  userApi.recipes.timersActive.updateTimerActive(timer.recipeTimerActiveId, updatedTimerActive)
    .then((response) => {
      if (response.data) {
        syncTimerActiveAdded(timer.recipeTimerId, response.data);
      }
      else {
        syncTimerActiveUpdated(timer.recipeTimerActiveId, updatedTimerActive.completeTime);
      }
      console.log("timer updated", response.data);
    })
    .catch((error) => {
      console.error("Failed to update active timer:", error);
    });
}

function deleteTimerActive(timer: ReturnType<typeof useTimer>) {
  if (!timer.recipeTimerActiveId) return;

  const activeId = timer.recipeTimerActiveId;
  const recipeLink = timerRecipeLinkByActiveId.value[activeId] || buildRecipeLink(timer.recipeTimerId || "", props.isCookMode);

  // Optimistically clear local/shared state so reset/pause does not get overridden
  // by a stale active timer while waiting for the API response.
  syncTimerActiveRemoved(activeId);
  const { [activeId]: _removed, ...rest } = timerRecipeLinkByActiveId.value;
  timerRecipeLinkByActiveId.value = rest;

  const { [activeId]: _thresholdRemoved, ...thresholdRest } = stoppedByActiveScreenSentByActiveId.value;
  stoppedByActiveScreenSentByActiveId.value = thresholdRest;

  timer.recipeTimerActiveId = "";

  userApi.recipes.timersActive.deleteTimerActive(activeId, { recipeLink })
    .then((response) => {
      console.log("timer deleted", response.data);
    })
    .catch((error) => {
      console.error("Failed to delete active timer:", error);
      refreshActiveTimersFromServer();
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

  return `${window.location.origin}/g/${encodeURIComponent(groupSlug.value)}/r/${encodeURIComponent(recipeSlug.value)}?${query.toString()}`;
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

function reconcileTimerCountdownsFromActives() {
  if (!compTimers.value?.length) {
    return;
  }

  compTimers.value.forEach((timer) => {
    const sourceTimer = getSourceTimerById(timer.recipeTimerId);
    if (!sourceTimer) {
      return;
    }

    const allTimersActive = sourceTimer.timersActive ?? [];
    const timersActive = showAllHouseholdTimersInRecipe.value
      ? allTimersActive
      : allTimersActive.filter(ta => ta.userId === currentUserId.value);

    syncExistingTimerFromActives(timer, timersActive);
  });
}

function onAppBecameActive() {
  updateScreenActiveState();
  if (!isScreenActive.value) {
    return;
  }

  // Recalculate remaining values immediately from known active timers,
  // then refresh from server for cross-device/background updates.
  reconcileTimerCountdownsFromActives();
  refreshActiveTimersFromServer();

  const socket = timerActiveSocket.value;
  if (!socket || socket.readyState === WebSocket.CLOSED || socket.readyState === WebSocket.CLOSING) {
    connectTimerActiveSocket();
  }
}

function onVisibilityChange() {
  updateScreenActiveState();
  if (isScreenActive.value) {
    onAppBecameActive();
  }
}

onMounted(() => {
  isComponentUnmounted.value = false;
  updateScreenActiveState();
  document.addEventListener("visibilitychange", onVisibilityChange);
  window.addEventListener("focus", onAppBecameActive);
  window.addEventListener("pageshow", onAppBecameActive);

  refreshActiveTimersFromServer();
  connectTimerActiveSocket();
});

watch(() => auth.token.value, () => {
  const socket = timerActiveSocket.value;
  if (!socket) {
    connectTimerActiveSocket();
    return;
  }

  socket.close();
});

onUnmounted(() => {
  isComponentUnmounted.value = true;
  timerThresholdWatcherStops.value.forEach(stop => stop());
  timerThresholdWatcherStops.value = [];
  document.removeEventListener("visibilitychange", onVisibilityChange);
  window.removeEventListener("focus", onAppBecameActive);
  window.removeEventListener("pageshow", onAppBecameActive);

  if (timerActiveSocketReconnectTimeout.value) {
    clearTimeout(timerActiveSocketReconnectTimeout.value);
    timerActiveSocketReconnectTimeout.value = null;
  }

  clearTimerActiveSocketHeartbeat();
  timerActiveSocket.value?.close();
  timerActiveSocket.value = null;
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
