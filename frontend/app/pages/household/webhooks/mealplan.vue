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
        {{ $t('settings.webhooks.mealplan-webhooks') }}
      </template>
      <v-card-text class="pb-0">
        {{ $t('settings.webhooks.description') }}
      </v-card-text>
    </BasePageTitle>

    <BaseButton
      create
      @click="actions.createOne()"
    />
    <v-expansion-panels class="mt-2">
      <v-expansion-panel
        v-for="(webhook, index) in webhooks"
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
            {{ webhook.name }} - {{ $d(timeUTC(webhook.scheduledTime || "00:00"), "time") }}
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
            @save="actions.updateOne($event)"
            @delete="actions.deleteOne($event)"
            @test-mealplan="actions.testMealplanOne($event).then(() => alert.success($t('events.test-message-sent')))"
          />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-container>
</template>

<script setup lang="ts">
import { useGroupWebhooks, timeUTC } from "~/composables/use-group-webhooks";
import GroupWebhookEditor from "~/components/Domain/Household/GroupWebhookEditor.vue";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["advanced-only"],
});

const i18n = useI18n();
const webhookType = ref<"mealplan">("mealplan");
const { actions, webhooks } = useGroupWebhooks(webhookType);

useSeoMeta({
  title: i18n.t("settings.webhooks.mealplan-webhooks"),
});
</script>
