import { BaseCRUDAPI } from "../base/base-clients";
import type { CreateIngredientFood, IngredientFood } from "~/lib/api/types/recipe";
import type { SuccessResponse } from "~/lib/api/types/response";

const prefix = "/api";

const routes = {
  food: `${prefix}/foods`,
  foodsFood: (tag: string) => `${prefix}/foods/${tag}`,
  merge: `${prefix}/foods/merge`,
  translateJp: `${prefix}/foods/translate-jp`,
};

export class FoodAPI extends BaseCRUDAPI<CreateIngredientFood, IngredientFood> {
  baseRoute: string = routes.food;
  itemRoute = routes.foodsFood;

  merge(fromId: string, toId: string) {
    return this.requests.put<IngredientFood>(routes.merge, { fromFood: fromId, toFood: toId });
  }

  translateJp() {
    return this.requests.post<SuccessResponse>(routes.translateJp, {});
  }
}
