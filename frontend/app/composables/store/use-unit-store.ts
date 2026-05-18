import type { Composer } from "vue-i18n";
import { useData, useStore } from "../partials/use-store-factory";
import type { IngredientUnit } from "~/lib/api/types/recipe";
import { useUserApi } from "~/composables/api";
import { UnitNames } from "~/composables/use-unit";

const store: Ref<IngredientUnit[]> = ref([]);
const loading = ref(false);

export function resetUnitStore() {
  store.value = [];
  loading.value = false;
  milliliterUnit.value = null;
  gramUnit.value = null;
}

export const useUnitData = function () {
  return useData<IngredientUnit>({
    id: "",
    name: "",
    fraction: true,
    abbreviation: "",
    description: "",
  });
};

export const useUnitStore = function (i18n?: Composer) {
  const api = useUserApi(i18n);
  return useStore<IngredientUnit>("unit", store, loading, api.units, {
    orderBy: "position",
    orderByNullPosition: "last",
    orderDirection: "asc",
  });
};

export const milliliterUnit: Ref<IngredientUnit | null> = ref(null);
export const gramUnit: Ref<IngredientUnit | null> = ref(null);

watch(store, (units) => {
  milliliterUnit.value = units.find(unit => unit.standardUnit === UnitNames.milliliter && unit.standardQuantity === 1) || null;
  gramUnit.value = units.find(unit => unit.standardUnit === UnitNames.gram && unit.standardQuantity === 1) || null;
});
