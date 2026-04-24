<template>
  <div>
    <v-card-text>
      <v-switch
        v-model="webhookCopy.enabled"
        color="primary"
        :label="$t('general.enabled')"
      />
      <v-text-field
        v-model="webhookCopy.name"
        :label="$t('settings.webhooks.webhook-name')"
        variant="underlined"
      />
      <v-text-field
        v-model="webhookCopy.url"
        :label="$t('settings.webhooks.webhook-url')"
        variant="underlined"
      />

      <!-- Mealplan-only fields -->
      <v-text-field
        v-if="isMealplan"
        v-model="scheduledTime"
        type="time"
        clearable
        variant="underlined"
      />

      <!-- Timer-only fields -->
      <template v-if="isTimer">
        <v-select
          v-model="webhookCopy.timerEvent"
          :items="timerEventOptions"
          :label="$t('settings.webhooks.timer-event')"
          variant="underlined"
        />
        <v-select
          v-model="webhookCopy.userId"
          :items="timerUserOptions"
          item-title="title"
          item-value="value"
          :label="$t('general.owner')"
          variant="underlined"
        />
        <v-switch
          v-model="webhookCopy.isDeepLink"
          color="primary"
          :label="$t('settings.webhooks.deep-link')"
          :hint="$t('settings.webhooks.deep-link-hint')"
          persistent-hint
        />

        <v-expand-transition>
          <div v-if="showTimerTestPanel" class="mt-2">
            <v-text-field
              v-if="showTimerLength"
              v-model="timerTestLength"
              type="number"
              min="1"
              :label="$t('settings.webhooks.timer-length')"
              variant="underlined"
            />
            <v-text-field
              v-model="timerTestMessage"
              :label="$t('general.message')"
              variant="underlined"
            />
            <v-text-field
              v-model="timerTestTimerId"
              :label="$t('settings.webhooks.timer-id')"
              variant="underlined"
            />

            <p class="text-body-2 mb-1">
              {{ $t('settings.webhooks.parsed-webhook-url') }}
            </p>
            <p class="text-body-2 mb-3">
              {{ parsedWebhookUrl }}
            </p>

            <template v-if="!webhookCopy.isDeepLink">
              <p class="text-body-2 mb-1">
                {{ $t('settings.webhooks.webhook-payload-preview') }}
              </p>
              <pre class="text-caption bg-grey-lighten-4 pa-3 rounded">{{ renderedWebhookPayload }}</pre>
            </template>
          </div>
        </v-expand-transition>
      </template>
    </v-card-text>
    <v-card-actions class="py-0 justify-end">
      <BaseButtonGroup
        :buttons="[
          {
            icon: $globals.icons.delete,
            text: $t('general.delete'),
            event: 'delete',
          },
          {
            icon: $globals.icons.testTube,
            text: $t('general.test'),
            event: 'test',
          },
          {
            icon: $globals.icons.save,
            text: $t('general.save'),
            event: 'save',
          },
        ]"
        @delete="$emit('delete', webhookCopy.id)"
        @save="handleSave"
        @test="handleTest"
      />
    </v-card-actions>
  </div>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import type { ReadWebhook, TimerEvent } from "~/lib/api/types/household";
import type { UserOut } from "~/lib/api/types/user";
import { timeLocalToUTC, timeUTCToLocal } from "~/composables/use-group-webhooks";

const props = defineProps<{
  webhook: ReadWebhook;
}>();

const emit = defineEmits<{
  delete: [id: string];
  save: [webhook: ReadWebhook];
  testMealplan: [id: string];
  testTimer: [{
    id: string;
    timerId?: string;
    length?: string;
    message?: string;
    completeTime?: string;
    completeTimeInMs?: number;
  }];
}>();

const i18n = useI18n();
const api = useUserApi();

const isMealplan = computed(() => !props.webhook.webhookType || props.webhook.webhookType === "mealplan");
const isTimer = computed(() => props.webhook.webhookType === "timer");
const householdMembers = useState<UserOut[]>("household-webhook-member-options", () => []);

const itemLocal = ref<string>(
  isMealplan.value && props.webhook.scheduledTime ? timeUTCToLocal(props.webhook.scheduledTime) : "00:00",
);

const scheduledTime = computed({
  get() {
    return itemLocal.value;
  },
  set(v: string) {
    itemLocal.value = v;
  },
});

const timerEventOptions = computed(() => [
  { title: i18n.t("settings.webhooks.timer-event-started"), value: "started" as TimerEvent },
  { title: i18n.t("settings.webhooks.timer-event-updated"), value: "updated" as TimerEvent },
  { title: i18n.t("settings.webhooks.timer-event-stopped"), value: "stopped" as TimerEvent },
]);

const timerUserOptions = computed(() =>
  householdMembers.value.map(member => ({
    title: member.fullName || member.username || member.email,
    value: member.id,
  })),
);

const webhookCopy = ref({ ...props.webhook });
const showTimerTestPanel = ref(false);
const timerTestTimerId = ref("timer-1");
const timerTestLength = ref("300");
const timerTestMessage = ref("Test Webhook");

const timerTestAction = computed<"create" | "update" | "delete">(() => {
  if (webhookCopy.value.timerEvent === "updated") {
    return "update";
  }
  if (webhookCopy.value.timerEvent === "stopped") {
    return "delete";
  }
  return "create";
});

function getTimerTestCompleteTime(): string {
  const parsedSeconds = Number.parseInt(timerTestLength.value, 10);
  const seconds = Number.isFinite(parsedSeconds) && parsedSeconds > 0 ? parsedSeconds : 0;
  return new Date(Date.now() + seconds * 1000).toISOString();
}

function getTimerTestCompleteTimeInMs(): number {
  const parsedSeconds = Number.parseInt(timerTestLength.value, 10);
  const seconds = Number.isFinite(parsedSeconds) && parsedSeconds > 0 ? parsedSeconds : 0;
  return Date.now() + seconds * 1000;
}

const timerTestCompleteTime = ref(getTimerTestCompleteTime());
const timerTestCompleteTimeInMs = ref(getTimerTestCompleteTimeInMs());

watch(timerTestLength, () => {
  timerTestCompleteTime.value = getTimerTestCompleteTime();
  timerTestCompleteTimeInMs.value = getTimerTestCompleteTimeInMs();
});

const showTimerLength = computed(
  () => webhookCopy.value.timerEvent === "started" || webhookCopy.value.timerEvent === "updated",
);

const parsedWebhookUrl = computed(() => {
  const safeLength = showTimerLength.value ? encodeURIComponent(timerTestLength.value) : "";
  const safeMessage = encodeURIComponent(timerTestMessage.value);

  return (webhookCopy.value.url || "")
    .replaceAll("{length}", safeLength)
    .replaceAll("{message}", safeMessage);
});

const renderedWebhookPayload = computed(() => {
  const payload: Record<string, string | number> = {
    action: timerTestAction.value,
    timerId: timerTestTimerId.value,
    message: timerTestMessage.value,
  };

  if (showTimerLength.value) {
    payload.length = timerTestLength.value;
    payload.completeTime = timerTestCompleteTime.value;
    payload.completeTimeInMs = timerTestCompleteTimeInMs.value;
  }

  return JSON.stringify(payload, null, 2);
});

function handleTest() {
  handleSave();
  if (isTimer.value) {
    if (!showTimerTestPanel.value) {
      showTimerTestPanel.value = true;
      return;
    }

    timerTestCompleteTime.value = getTimerTestCompleteTime();
    timerTestCompleteTimeInMs.value = getTimerTestCompleteTimeInMs();

    emit("testTimer", {
      id: webhookCopy.value.id,
      timerId: timerTestTimerId.value,
      length: showTimerLength.value ? timerTestLength.value : undefined,
      message: timerTestMessage.value,
      completeTime: timerTestCompleteTime.value,
      completeTimeInMs: timerTestCompleteTimeInMs.value,
    });
    return;
  }

  emit("testMealplan", webhookCopy.value.id);
}

function handleSave() {
  if (isMealplan.value) {
    webhookCopy.value.scheduledTime = timeLocalToUTC(itemLocal.value);
  }
  else {
    webhookCopy.value.scheduledTime = undefined;
  }
  emit("save", webhookCopy.value);
}

onMounted(async () => {
  if (!isTimer.value || householdMembers.value.length) {
    return;
  }

  const { data } = await api.households.fetchMembers();
  if (data?.items) {
    householdMembers.value = data.items;
  }
});
</script>
