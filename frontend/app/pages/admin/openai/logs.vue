<template>
  <v-container fluid>
    <BasePageTitle divider>
      <template #title>
        {{ $t("admin.openai-logs") }}
      </template>
    </BasePageTitle>

    <v-card class="pa-4 mb-4">
      <v-row>
        <v-col cols="12" md="3">
          <v-text-field v-model="filters.endpoint" :label="$t('admin.openai-endpoint')" hide-details />
        </v-col>
        <v-col cols="12" md="2">
          <v-select v-model="filters.status" :items="statuses" :label="$t('general.status')" hide-details />
        </v-col>
        <v-col cols="12" md="3">
          <v-text-field v-model="filters.userName" :label="$t('user.username')" hide-details />
        </v-col>
        <v-col cols="12" md="2">
          <v-menu
            v-model="startDateMenu"
            :close-on-content-click="false"
            transition="scale-transition"
            offset-y
            max-width="290px"
          >
            <template #activator="{ props: activatorProps }">
              <v-text-field
                :model-value="filters.startDate || ''"
                :label="$t('admin.openai-start-date')"
                :prepend-icon="$globals.icons.calendar"
                v-bind="activatorProps"
                readonly
                clearable
                hide-details
                @click:clear="filters.startDate = ''"
              />
            </template>
            <v-date-picker
              v-model="filters.startDate"
              hide-header
              @update:model-value="startDateMenu = false"
            />
          </v-menu>
        </v-col>
        <v-col cols="12" md="2">
          <v-menu
            v-model="endDateMenu"
            :close-on-content-click="false"
            transition="scale-transition"
            offset-y
            max-width="290px"
          >
            <template #activator="{ props: activatorProps }">
              <v-text-field
                :model-value="filters.endDate || ''"
                :label="$t('admin.openai-end-date')"
                :prepend-icon="$globals.icons.calendar"
                v-bind="activatorProps"
                readonly
                clearable
                hide-details
                @click:clear="filters.endDate = ''"
              />
            </template>
            <v-date-picker
              v-model="filters.endDate"
              hide-header
              @update:model-value="endDateMenu = false"
            />
          </v-menu>
        </v-col>
      </v-row>
      <div class="d-flex justify-end mt-4" style="gap: 0.5rem;">
        <v-menu>
          <template #activator="{ props }">
            <BaseButton color="info" v-bind="props">
              {{ $t("admin.openai-columns") }}
            </BaseButton>
          </template>
          <v-list density="compact">
            <v-list-item v-for="column in allColumns" :key="column.value">
              <v-checkbox
                v-model="visibleColumns"
                :value="column.value"
                :label="column.title"
                hide-details
                density="compact"
              />
            </v-list-item>
          </v-list>
        </v-menu>
        <BaseButton color="info" :loading="loading" @click="fetchLogs(1)">
          {{ $t("general.search") }}
        </BaseButton>
      </div>
    </v-card>

    <template v-if="hasLoaded">
      <v-data-table
        :headers="headers"
        :items="logs.items"
        :no-data-text="noDataText"
        class="elevation-0"
        :items-per-page="-1"
        hide-default-footer
        disable-pagination
        :loading="loading"
      >
        <template #[`item.timestamp`]="{ item }">
          {{ $d(Date.parse(item.timestamp)) }}
        </template>
        <template #[`item.time`]="{ item }">
          {{ formatTime(item.timestamp) }}
        </template>
        <template #[`item.userName`]="{ item }">
          {{ item.userName || "-" }}
        </template>
        <template #[`item.totalTokens`]="{ item }">
          {{ item.totalTokens ?? 0 }}
        </template>
        <template #[`item.inputTokens`]="{ item }">
          {{ item.inputTokens ?? 0 }}
        </template>
        <template #[`item.outputTokens`]="{ item }">
          {{ item.outputTokens ?? 0 }}
        </template>
        <template #[`item.latencyMs`]="{ item }">
          {{ item.latencyMs ?? 0 }} ms
        </template>
      </v-data-table>

      <div class="d-flex justify-space-between align-center mt-4">
        <v-select
          v-model="pagination.perPage"
          :items="[25, 50, 100]"
          label="Per Page"
          density="compact"
          max-width="120"
          hide-details
          @update:model-value="() => fetchLogs(1)"
        />
        <v-pagination
          v-model="pagination.page"
          :length="logs.totalPages || 1"
          @update:model-value="(page) => fetchLogs(page)"
        />
        <div>{{ logs.total }} {{ $t("admin.openai-requests") }}</div>
      </div>
    </template>
    <div
      v-else
      class="d-flex justify-center py-8"
    >
      <AppLoader :waiting-text="$t('general.loading')" />
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { useAdminApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import type { OpenAIUsageLogPagination } from "~/lib/api/admin/admin-openai";
import AppLoader from "~/components/global/AppLoader.vue";

definePageMeta({
  layout: "admin",
});

const i18n = useI18n();
const api = useAdminApi();
const loading = ref(false);
const hasLoaded = ref(false);
const startDateMenu = ref(false);
const endDateMenu = ref(false);

useSeoMeta({
  title: i18n.t("admin.openai-logs"),
});

const logs = ref<OpenAIUsageLogPagination>({
  page: 1,
  perPage: 25,
  total: 0,
  totalPages: 0,
  items: [],
});

const pagination = reactive({
  page: 1,
  perPage: 25,
});

const filters = reactive({
  endpoint: "",
  status: "",
  userName: "",
  startDate: "",
  endDate: "",
  allGroups: false,
});

const statuses = ["", "success", "error", "rate_limit"];

const allColumns = [
  { title: i18n.t("general.date"), value: "timestamp" },
  { title: i18n.t("general.time"), value: "time" },
  { title: i18n.t("admin.openai-endpoint"), value: "endpoint" },
  { title: i18n.t("general.status"), value: "status" },
  { title: i18n.t("user.username"), value: "userName" },
  { title: i18n.t("admin.openai-input-tokens"), value: "inputTokens" },
  { title: i18n.t("admin.openai-output-tokens"), value: "outputTokens" },
  { title: i18n.t("admin.openai-total-tokens"), value: "totalTokens" },
  { title: i18n.t("admin.openai-latency-ms"), value: "latencyMs" },
];

const visibleColumns = ref<string[]>(allColumns.map(c => c.value));

const headers = computed(() => allColumns.filter(column => visibleColumns.value.includes(column.value)));

const hasActiveFilters = computed(() => {
  return Boolean(filters.endpoint || filters.status || filters.userName || filters.startDate || filters.endDate);
});

const noDataText = computed(() => {
  if (hasActiveFilters.value) {
    return i18n.t("admin.openai-no-results");
  }
  return i18n.t("admin.openai-no-data");
});

function formatTime(timestamp: string) {
  return new Intl.DateTimeFormat(i18n.locale.value, {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(timestamp));
}

async function fetchLogs(page = 1) {
  loading.value = true;
  pagination.page = page;

  const { data, error } = await api.openai.logs({
    page,
    per_page: pagination.perPage,
    endpoint: filters.endpoint || undefined,
    status: filters.status || undefined,
    user_name: filters.userName || undefined,
    all_groups: filters.allGroups,
    start_at: filters.startDate ? `${filters.startDate}T00:00:00` : undefined,
    end_at: filters.endDate ? `${filters.endDate}T23:59:59` : undefined,
  });

  if (data) {
    logs.value = data;
  }
  else {
    logs.value = {
      page: 1,
      perPage: pagination.perPage,
      total: 0,
      totalPages: 0,
      items: [],
    };

    if (error) {
      alert.error(i18n.t("admin.openai-load-failed"));
    }
  }

  hasLoaded.value = true;
  loading.value = false;
}

onMounted(() => {
  fetchLogs(1);
});
</script>
