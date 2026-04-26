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
        {{ $t('settings.webhooks.timer-webhooks') }}
      </template>
      <v-card-text class="pb-0">
        {{ $t('profile.timer-webhooks-description') }}
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
            {{ webhook.name }} - {{ $t(`settings.webhooks.timer-event-${webhook.timerEvent}`) }} - {{ getWebhookUserLabel(webhook.userId) }}
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
            @test-timer="actions.testTimerOne($event).then(() => alert.success($t('events.test-message-sent')))"
          />
        </v-expansion-panel-text>
      </v-expansion-panel>
    </v-expansion-panels>
  </v-container>
</template>

<script setup lang="ts">
import { useGroupWebhooks } from "~/composables/use-group-webhooks";
import { useUserApi } from "~/composables/api";
import GroupWebhookEditor from "~/components/Domain/Household/GroupWebhookEditor.vue";
import { alert } from "~/composables/use-toast";

definePageMeta({
  middleware: ["advanced-only"],
});

const i18n = useI18n();
const api = useUserApi();
const webhookType = ref<"timer">("timer");
const { actions, webhooks } = useGroupWebhooks(webhookType);
const memberNameById = ref<Record<string, string>>({});

function getWebhookUserLabel(userId?: string) {
  if (!userId) {
    return i18n.t("general.none");
  }

  return memberNameById.value[userId] || userId;
}

onMounted(async () => {
  const { data } = await api.households.fetchMembers();
  if (!data?.items) {
    return;
  }

  memberNameById.value = Object.fromEntries(
    data.items.map(member => [member.id, member.fullName || member.username || member.email]),
  );
});

useSeoMeta({
  title: i18n.t("settings.webhooks.timer-webhooks"),
});
</script>
