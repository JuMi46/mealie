import { BaseCRUDAPI } from "../base/base-clients";
import type { CreateWebhook, ReadWebhook } from "~/lib/api/types/household";

export interface TimerWebhookTestPayload {
  timerId?: string;
  length?: string;
  message?: string;
  recipeLink?: string;
  completeTime?: string;
  completeTimeInMs?: number;
}

const prefix = "/api";

const routes = {
  webhooks: `${prefix}/households/webhooks`,
  webhooksId: (id: string | number) => `${prefix}/households/webhooks/${id}`,
  webhooksIdTest: (id: string | number) => `${prefix}/households/webhooks/${id}/test`,
  webhooksIdTestTimer: (id: string | number) => `${prefix}/households/webhooks/${id}/test/timer`,
};

export class WebhooksAPI extends BaseCRUDAPI<CreateWebhook, ReadWebhook> {
  override baseRoute = routes.webhooks;
  override itemRoute = routes.webhooksId;
  itemTestMealplanRoute = routes.webhooksIdTest;
  itemTestTimerRoute = routes.webhooksIdTestTimer;

  async testMealplanOne(itemId: string | number) {
    return await this.requests.post<null>(`${this.itemTestMealplanRoute(itemId)}`, {});
  }

  async testTimerOne(itemId: string | number, payload: TimerWebhookTestPayload) {
    return await this.requests.post<null>(`${this.itemTestTimerRoute(itemId)}`, payload);
  }
}
