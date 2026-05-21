<template>
  <v-container fluid>
    <BasePageTitle divider>
      <template #title>
        {{ $t("admin.openai-usage-summary") }}
      </template>
    </BasePageTitle>

    <div class="d-flex justify-end mb-4">
      <BaseButton color="info" :loading="loading" @click="fetchSummary">
        {{ $t("general.refresh") }}
      </BaseButton>
    </div>

    <v-row>
      <v-col cols="12" md="3">
        <v-card class="pa-4">
          <div class="text-caption">
            {{ $t("admin.openai-requests") }}
          </div>
          <div class="text-h5">
            {{ summary.totalRequests }}
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="pa-4">
          <div class="text-caption">
            {{ $t("admin.openai-failed-requests") }}
          </div>
          <div class="text-h5">
            {{ summary.failedRequests }}
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="pa-4">
          <div class="text-caption">
            {{ $t("admin.openai-total-tokens") }}
          </div>
          <div class="text-h5">
            {{ summary.totalTokens }}
          </div>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card class="pa-4">
          <div class="text-caption">
            {{ $t("admin.openai-latency-ms") }}
          </div>
          <div class="text-h5">
            {{ summary.avgLatencyMs }}
          </div>
        </v-card>
      </v-col>
    </v-row>

    <v-row class="mt-2">
      <v-col cols="12" md="6">
        <BaseCardSectionTitle :title="$t('admin.openai-daily-usage')" />
        <v-data-table
          :headers="dailyHeaders"
          :items="summary.daily"
          class="elevation-0"
          :items-per-page="-1"
          hide-default-footer
          disable-pagination
          :loading="loading"
        />
      </v-col>
      <v-col cols="12" md="6">
        <BaseCardSectionTitle :title="$t('admin.openai-top-endpoints')" />
        <v-data-table
          :headers="namedHeaders"
          :items="summary.topEndpoints"
          class="elevation-0 mb-4"
          :items-per-page="-1"
          hide-default-footer
          disable-pagination
          :loading="loading"
        />

        <BaseCardSectionTitle :title="$t('admin.openai-top-models')" />
        <v-data-table
          :headers="namedHeaders"
          :items="summary.topModels"
          class="elevation-0"
          :items-per-page="-1"
          hide-default-footer
          disable-pagination
          :loading="loading"
        />
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useAdminApi } from "~/composables/api";
import type { OpenAIUsageSummary } from "~/lib/api/admin/admin-openai";

definePageMeta({
  layout: "admin",
});

const i18n = useI18n();
const api = useAdminApi();
const loading = ref(false);

useSeoMeta({
  title: i18n.t("admin.openai-usage-summary"),
});

const summary = ref<OpenAIUsageSummary>({
  totalRequests: 0,
  failedRequests: 0,
  inputTokens: 0,
  outputTokens: 0,
  totalTokens: 0,
  avgLatencyMs: 0,
  daily: [],
  topEndpoints: [],
  topModels: [],
});

const dailyHeaders = [
  { title: i18n.t("general.date"), value: "day" },
  { title: i18n.t("admin.openai-requests"), value: "requests" },
  { title: i18n.t("admin.openai-input-tokens"), value: "inputTokens" },
  { title: i18n.t("admin.openai-output-tokens"), value: "outputTokens" },
  { title: i18n.t("admin.openai-total-tokens"), value: "totalTokens" },
];

const namedHeaders = [
  { title: i18n.t("admin.openai-endpoint"), value: "name" },
  { title: i18n.t("admin.openai-requests"), value: "requests" },
  { title: i18n.t("admin.openai-total-tokens"), value: "totalTokens" },
];

async function fetchSummary() {
  loading.value = true;
  const { data } = await api.openai.summary({});
  if (data) {
    summary.value = data;
  }
  loading.value = false;
}

onMounted(() => {
  fetchSummary();
});
</script>
