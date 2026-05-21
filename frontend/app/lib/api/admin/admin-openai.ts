import { BaseAPI } from "../base/base-clients";

const prefix = "/api";

const routes = {
  logs: `${prefix}/admin/openai/logs`,
  summary: `${prefix}/admin/openai/summary`,
  prune: `${prefix}/admin/openai/prune`,
};

export interface OpenAIUsageLogItem {
  id: string;
  timestamp: string;
  endpoint: string;
  operation: string;
  status: string;
  model?: string | null;
  provider?: string | null;
  requestId?: string | null;
  inputTokens?: number | null;
  outputTokens?: number | null;
  totalTokens?: number | null;
  latencyMs?: number | null;
  hadAttachments: boolean;
  errorClass?: string | null;
  errorMessage?: string | null;
  groupId?: string | null;
  householdId?: string | null;
  userId?: string | null;
  userName?: string | null;
}

export interface OpenAIUsageLogPagination {
  page: number;
  perPage: number;
  total: number;
  totalPages: number;
  next?: string | null;
  previous?: string | null;
  items: OpenAIUsageLogItem[];
}

export interface OpenAIUsageDailySummary {
  day: string;
  requests: number;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
}

export interface OpenAIUsageNamedSummary {
  name: string;
  requests: number;
  totalTokens: number;
}

export interface OpenAIUsageSummary {
  totalRequests: number;
  failedRequests: number;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  avgLatencyMs: number;
  daily: OpenAIUsageDailySummary[];
  topEndpoints: OpenAIUsageNamedSummary[];
  topModels: OpenAIUsageNamedSummary[];
}

export interface OpenAIUsageLogsQuery {
  page?: number;
  per_page?: number;
  all_groups?: boolean;
  group_id?: string;
  user_id?: string;
  user_name?: string;
  endpoint?: string;
  status?: string;
  model?: string;
  search?: string;
  start_at?: string;
  end_at?: string;
}

export class AdminOpenAIApi extends BaseAPI {
  async logs(params: OpenAIUsageLogsQuery) {
    return await this.requests.get<OpenAIUsageLogPagination>(routes.logs, params);
  }

  async summary(params: Omit<OpenAIUsageLogsQuery, "page" | "per_page">) {
    return await this.requests.get<OpenAIUsageSummary>(routes.summary, params);
  }

  async prune(days = 90) {
    return await this.requests.post(routes.prune, {}, { params: { days } });
  }
}
