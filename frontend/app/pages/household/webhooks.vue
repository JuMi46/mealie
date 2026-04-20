<template>
  <v-container class="narrow-container">
    <BasePageTitle divider>
      <template #header>
        <v-img
          width="100%"
          max-height="125"
          max-width="125"
          src="/svgs/manage-webhooks.svg"
        />
      </template>
      <template #title>
        {{ $t('settings.webhooks.webhooks') }}
      </template>
      <v-card-text class="pb-0">
        {{ $t('settings.webhooks.description') }}
      </v-card-text>
    </BasePageTitle>

    <!-- Mealplan Webhooks -->
    <div class="d-flex align-center mt-4 mb-1">
      <h2 class="text-h6">
        {{ $t('settings.webhooks.mealplan-webhooks') }}
      </h2>
      <v-spacer />
      <BaseButton
        create
        @click="mealplanActions.createOne()"
      />
    </div>
    <v-expansion-panels class="mt-2">
      <v-expansion-panel
        v-for="(webhook, index) in mealplanWebhooks"
        :key="index"
        class="my-2 left-border rounded"
      >
        <v-expansion-panel-title
          disable-icon-rotate
          class="headline"
        >
          <div class="d-flex align-center">
            <v-icon
              size="large"
              start
              :color="webhook.enabled ? 'info' : undefined"
            >
              {{ $globals.icons.webhook }}
            </v-icon>
            {{ webhook.name }} - {{ $d(timeUTC(webhook.scheduledTime), "time") }}
          </div>
          <template #actions>
            <v-btn
              size="small"
              icon
              flat
              class="ml-2"
            >
              <v-icon>
                {{ $globals.icons.edit }}
              </v-icon>
            </v-btn>
          </template>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <GroupWebhookEditor
            :key="webhook.id"
            :webhook="webhook"
            @save="mealplanActions.updateOne($event)"
            @delete="mealplanActions.deleteOne($event)"
            @test="mealplanActions.testOne($event).then(() => alert.success($t('events.test-message-sent')))"
          />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>

    <!-- Timer Webhooks -->
    <div class="d-flex align-center mt-6 mb-1">
      <h2 class="text-h6">
        {{ $t('settings.webhooks.timer-webhooks') }}
      </h2>
      <v-spacer />
      <BaseButton
        create
        @click="timerActions.createOne()"
      />
    </div>
    <v-expansion-panels class="mt-2">
      <v-expansion-panel
        v-for="(webhook, index) in timerWebhooks"
        :key="index"
        class="my-2 left-border rounded"
      >
        <v-expansion-panel-title
          disable-icon-rotate
          class="headline"
        >
          <div class="d-flex align-center">
            <v-icon
              size="large"
              start
              :color="webhook.enabled ? 'info' : undefined"
            >
              {{ $globals.icons.webhook }}
            </v-icon>
            {{ webhook.name }} - {{ $t(`settings.webhooks.timer-event-${webhook.timerEvent}`) }}
          </div>
          <template #actions>
            <v-btn
              size="small"
              icon
              flat
              class="ml-2"
            >
              <v-icon>
                {{ $globals.icons.edit }}
              </v-icon>
            </v-btn>
          </template>
        </v-expansion-panel-title>
        <v-expansion-panel-text>
          <GroupWebhookEditor
            :key="webhook.id"
            :webhook="webhook"
            @save="timerActions.updateOne($event)"
            @delete="timerActions.deleteOne($event)"
            @test="timerActions.testOne($event).then(() => alert.success($t('events.test-message-sent')))"
          />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-container>
</template>

<script setup lang="ts">
import { useGroupWebhooks, timeUTC } from "~/composables/use-group-webhooks";
import type { WebhookType } from "~/lib/api/types/household";
import GroupWebhookEditor from "~/components/Domain/Household/GroupWebhookEditor.vue";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["advanced-only"],
});

const i18n = useI18n();

const mealplanType = ref<WebhookType>("mealplan");
const timerType = ref<WebhookType>("timer");

const { actions: mealplanActions, webhooks: mealplanWebhooks } = useGroupWebhooks(mealplanType);
const { actions: timerActions, webhooks: timerWebhooks } = useGroupWebhooks(timerType);

useSeoMeta({
  title: i18n.t("settings.webhooks.webhooks"),
});
</script>
