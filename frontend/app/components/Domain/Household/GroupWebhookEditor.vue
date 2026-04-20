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
        <v-switch
          v-model="webhookCopy.isDeepLink"
          color="primary"
          :label="$t('settings.webhooks.deep-link')"
          :hint="$t('settings.webhooks.deep-link-hint')"
          persistent-hint
        />
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
        @test="$emit('test', webhookCopy.id)"
      />
    </v-card-actions>
  </div>
</template>

<script setup lang="ts">
import type { ReadWebhook, TimerEvent } from "~/lib/api/types/household";
import { timeLocalToUTC, timeUTCToLocal } from "~/composables/use-group-webhooks";

const props = defineProps<{
  webhook: ReadWebhook;
}>();

const emit = defineEmits<{
  delete: [id: string];
  save: [webhook: ReadWebhook];
  test: [id: string];
}>();

const i18n = useI18n();

const isMealplan = computed(() => !props.webhook.webhookType || props.webhook.webhookType === "mealplan");
const isTimer = computed(() => props.webhook.webhookType === "timer");

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
  { title: i18n.t("settings.webhooks.timer-event-paused"), value: "paused" as TimerEvent },
  { title: i18n.t("settings.webhooks.timer-event-resumed"), value: "resumed" as TimerEvent },
  { title: i18n.t("settings.webhooks.timer-event-stopped"), value: "stopped" as TimerEvent },
]);

const webhookCopy = ref({ ...props.webhook });

function handleSave() {
  if (isMealplan.value) {
    webhookCopy.value.scheduledTime = timeLocalToUTC(itemLocal.value);
  }
  else {
    webhookCopy.value.scheduledTime = undefined;
  }
  emit("save", webhookCopy.value);
}
</script>
