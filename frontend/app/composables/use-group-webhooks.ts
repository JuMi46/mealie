import { useAsyncKey } from "./use-utils";
import { useUserApi } from "~/composables/api";
import { useMealieAuth } from "~/composables/use-mealie-auth";
import type { TimerWebhookTestPayload } from "~/lib/api/user/group-webhooks";
import type { ReadWebhook, WebhookType, TimerEvent } from "~/lib/api/types/household";

export const useGroupWebhooks = function (webhookType: Ref<WebhookType | null>) {
  const api = useUserApi();
  const loading = ref(false);
  const validForm = ref(true);

  const actions = {
    getAll() {
      loading.value = true;
      const { data: units } = useAsyncData(useAsyncKey(), async () => {
        const { data } = await api.groupWebhooks.getAll(1, -1, { webhook_type: webhookType.value || undefined });

        if (data) {
          return data.items;
        }
        else {
          return null;
        }
      });

      loading.value = false;
      return units;
    },
    async refreshAll() {
      loading.value = true;
      const { data } = await api.groupWebhooks.getAll(1, -1, { webhook_type: webhookType.value || undefined });

      if (data && data.items) {
        webhooks.value = data.items;
      }

      loading.value = false;
    },
    async createOne() {
      if (!webhookType.value) {
        return;
      }
      const { user } = useMealieAuth();
      loading.value = true;

      const payload = {
        enabled: true,
        name: "New Webhook",
        url: "",
        scheduledTime: webhookType.value == "mealplan" ? "00:00" : undefined,
        timerEvent: webhookType.value == "timer" ? ("started" as TimerEvent) : undefined,
        webhookType: webhookType.value,
        userId: webhookType.value == "timer" ? user.value?.id : undefined,
      };

      const { data } = await api.groupWebhooks.createOne(payload);
      if (data) {
        this.refreshAll();
      }

      loading.value = false;
    },
    async updateOne(updateData: ReadWebhook) {
      if (!updateData.id) {
        return;
      }

      const payload = {
        ...updateData,
      };

      if (updateData.webhookType === "mealplan" && updateData.scheduledTime) {
        // Convert to UTC time
        const [hours, minutes] = updateData.scheduledTime.split(":");

        const newDt = new Date();
        newDt.setHours(Number(hours));
        newDt.setMinutes(Number(minutes));

        updateData.scheduledTime = `${pad(newDt.getUTCHours(), 2)}:${pad(newDt.getUTCMinutes(), 2)}`;
        payload.scheduledTime = updateData.scheduledTime;
      }

      loading.value = true;
      const { data } = await api.groupWebhooks.updateOne(updateData.id, payload);
      if (data) {
        this.refreshAll();
      }
      loading.value = false;
    },

    async deleteOne(id: string | number) {
      loading.value = true;
      const { data } = await api.groupWebhooks.deleteOne(id);
      if (data) {
        this.refreshAll();
      }
      loading.value = false;
    },

    async testMealplanOne(id: string | number) {
      loading.value = true;
      await api.groupWebhooks.testMealplanOne(id);
      loading.value = false;
    },

    async testTimerOne(request: { id: string | number } & TimerWebhookTestPayload) {
      loading.value = true;
      const { id, ...payload } = request;
      await api.groupWebhooks.testTimerOne(id, payload);
      loading.value = false;
    },

  };

  const webhooks = actions.getAll();

  return { webhooks, actions, validForm };
};

function pad(num: number, size: number) {
  let numStr = num.toString();
  while (numStr.length < size) numStr = "0" + numStr;
  return numStr;
}

export function timeUTC(time: string): Date {
  const [hours, minutes] = time.split(":");
  const dt = new Date();
  dt.setUTCMinutes(Number(minutes));
  dt.setUTCHours(Number(hours));
  return dt;
}

export function timeUTCToLocal(time: string): string {
  const dt = timeUTC(time);
  return `${pad(dt.getHours(), 2)}:${pad(dt.getMinutes(), 2)}`;
}

export function timeLocalToUTC(time: string) {
  const [hours, minutes] = time.split(":");
  const dt = new Date();
  dt.setHours(Number(hours));
  dt.setMinutes(Number(minutes));
  return `${pad(dt.getUTCHours(), 2)}:${pad(dt.getUTCMinutes(), 2)}`;
}
