import { BaseCRUDAPI } from "../../base/base-clients";
import type { RecipeTimerActiveDelete, RecipeTimerActiveIn, RecipeTimerActiveOut, RecipeTimerActiveUpdate } from "~/lib/api/types/recipe";

const prefix = "/api";

const routes = {
  recipeTimers: `${prefix}/timers`,
  recipeTimersActive: `${prefix}/timers/active`,
  recipeTimerActive: (timerActiveId: string) => `${prefix}/timers/active/${timerActiveId}`,
  recipeTimerActiveStoppedWebhook: (timerActiveId: string) => `${prefix}/timers/active/${timerActiveId}/webhook/stopped`,
  recipesTimersActive: (recipeTimerId: string) => `${prefix}/timers/${recipeTimerId}/active`,
  recipesTimersActiveOnRecipe: (recipeId: string) => `${prefix}/timers/recipes/${recipeId}/active`,
};

export class TimersActiveApi extends BaseCRUDAPI<RecipeTimerActiveIn, RecipeTimerActiveOut, RecipeTimerActiveUpdate> {
  override baseRoute: string = routes.recipeTimers;
  override itemRoute = routes.recipesTimersActive;

  async createTimerActive(instructionTimerId: string, payload: RecipeTimerActiveIn) {
    return await this.requests.post<RecipeTimerActiveOut>(routes.recipesTimersActive(instructionTimerId), payload);
  }

  async createTimerActiveOnRecipe(recipeId: string, payload: RecipeTimerActiveIn) {
    return await this.requests.post<RecipeTimerActiveOut>(routes.recipesTimersActiveOnRecipe(recipeId), payload);
  }

  async getTimersActive() {
    return await this.requests.get<RecipeTimerActiveOut[]>(routes.recipeTimersActive);
  }

  async getTimerActive(timerActiveId: string) {
    return await this.requests.get<RecipeTimerActiveOut>(routes.recipeTimerActive(timerActiveId));
  }

  async updateTimerActive(timerActiveId: string, payload: RecipeTimerActiveUpdate) {
    return await this.requests.put<RecipeTimerActiveOut, RecipeTimerActiveUpdate>(routes.recipeTimerActive(timerActiveId), payload);
  }

  async deleteTimerActive(timerActiveId: string, payload?: RecipeTimerActiveDelete) {
    return await this.requests.delete<RecipeTimerActiveOut>(routes.recipeTimerActive(timerActiveId), {
      data: payload,
    });
  }

  async postStoppedWebhookForActiveTimer(timerActiveId: string, payload?: RecipeTimerActiveDelete) {
    return await this.requests.post<RecipeTimerActiveOut>(routes.recipeTimerActiveStoppedWebhook(timerActiveId), payload || {});
  }
}
