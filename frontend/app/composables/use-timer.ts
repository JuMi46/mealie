import { computed, onUnmounted, reactive, ref, toRefs, watch } from "@nuxtjs/composition-api";
// @ts-ignore typescript can't find our audio file, but it's there!
import timerAlarmAudio from "~/assets/audio/kitchen_alarm.mp3";


export default function createTimer(initialHour = "00", initialMin = "00", initialSec = "00", options = { padTimes: true }) {
  const state = reactive({
    timerInitialized: false,
    timerRunning: false,
    timerEnded: false,
    timerInitialValue: 0,
    timerValue: 0,
    timerPaused: false
  });

  // ts doesn't recognize timerAlarmAudio because it's a weird import
  // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
  const timerAlarm = new Audio(timerAlarmAudio);
  timerAlarm.loop = true;

  const timerHours = ref<string | number>(initialHour || "00");
  const timerMinutes = ref<string | number>(initialMin || "00");
  const timerSeconds = ref<string | number>(initialSec || "00");


  const timerProgress = computed(() => {
    if (state.timerInitialValue) {
      return (state.timerValue / state.timerInitialValue) * 100;
    } else {
      return 0;
    }
  });

  function updateHourMinSec(timerValue: number) {
    timerHours.value = Math.floor(timerValue / 3600).toString()
    timerMinutes.value = Math.floor(timerValue % 3600 / 60).toString()
    timerSeconds.value = Math.floor(timerValue % 3600 % 60).toString()
    if (options.padTimes) {
      timerHours.value = timerHours.value.padStart(2, "0");
      timerMinutes.value = timerMinutes.value.padStart(2, "0");
      timerSeconds.value = timerSeconds.value.padStart(2, "0");
    }
  }
  watch(() => state.timerValue, () => updateHourMinSec(state.timerValue));
  function updateTimerValue(newValue: number) {
    state.timerValue = newValue
  }
  let timerInterval: number | null = null;
  function decrementTimer() {
    if (state.timerValue > 0) {
      state.timerValue -= 1;
    }
    else {
      state.timerRunning = false;
      state.timerEnded = true;
      timerAlarm.currentTime = 0;
      timerAlarm.play();

      if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
      }
    }
  }

  function initializeTimer() {
    state.timerInitialized = true;
    state.timerEnded = false;

    console.log(timerSeconds.value);

    const hours = parseFloat(timerHours.value.toString()) > 0 ? parseFloat(timerHours.value.toString()) : 0;
    const minutes = parseFloat(timerMinutes.value.toString()) > 0 ? parseFloat(timerMinutes.value.toString()) : 0;
    const seconds = parseFloat(timerSeconds.value.toString()) > 0 ? parseFloat(timerSeconds.value.toString()) : 0;

    state.timerInitialValue = (hours * 3600) + (minutes * 60) + seconds;
    state.timerValue = state.timerInitialValue;

  };

  function startTimer() {
    if (!state.timerInitialized) {
      initializeTimer();
    }
    resumeTimer();
  }

  function pauseTimer() {
    state.timerRunning = false;
    state.timerPaused = true;
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  };

  function resumeTimer() {
    state.timerRunning = true;
    state.timerPaused = false;
    timerInterval = setInterval(decrementTimer, 1000) as unknown as number;
  };

  function resetTimer() {
    state.timerInitialized = false;
    state.timerRunning = false;
    state.timerEnded = false;
    state.timerPaused = false;
    timerAlarm.pause();
    timerAlarm.currentTime = 0;

    timerHours.value = "00";
    timerMinutes.value = "00";
    timerSeconds.value = "00";

    state.timerValue = state.timerInitialValue;
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }

  };
  const simpleDisplayValue = computed(() => {
    return computed(() => {
      const h = parseInt(timerHours.value.toString());
      const m = parseInt(timerMinutes.value.toString());
      const s = parseInt(timerSeconds.value.toString());
      const hours = h > 0 ? `${h}h` : "";
      const minutes = m > 0 ? `${m}m` : "";
      const seconds = m > 0 && s === 0 ? "" : `${s}s`;
      return [hours, minutes, seconds].filter(Boolean).join("");
    })
  })
  onUnmounted(() => {
    resetTimer();
  })
  return reactive({
    ...toRefs(state),
    timerHours,
    timerMinutes,
    timerSeconds,
    timerProgress,
    initializeTimer,
    pauseTimer,
    resumeTimer,
    resetTimer,
    startTimer,
    updateTimerValue,
    simpleDisplayValue: simpleDisplayValue.value
  })
}
