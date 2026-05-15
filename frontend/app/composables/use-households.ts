import { useAdminApi, useUserApi } from "~/composables/api";
import type {
  HouseholdCreate,
  HouseholdInDB,
  ReadHouseholdPreferences,
  UpdateHouseholdFoodSubstitution,
  UpdateHouseholdPreferences,
} from "~/lib/api/types/household";

const householdSelfRef = ref<HouseholdInDB | null>(null);
const loading = ref(false);

function serializeUnitIds(units?: ({ id: string } | string)[] | null): string[] {
  if (!Array.isArray(units)) {
    return [];
  }

  return units.flatMap(unit => {
    if (typeof unit === "string") return [unit];
    return unit.id ? [unit.id] : [];
  });
}

function serializeFoodSubstitutions(
  substitutions?: ReadHouseholdPreferences["foodSubstitutions"],
): UpdateHouseholdFoodSubstitution[] | undefined {
  if (!Array.isArray(substitutions)) {
    return undefined;
  }

  return substitutions.map(substitution => ({
    sourceFoodId: substitution.sourceFoodId,
    substituteFoodId: substitution.substituteFoodId,
    substituteRecipeId: substitution.substituteRecipeId,
    ratio: substitution.ratio,
  }));
}

function serializeHouseholdPreferences(preferences: ReadHouseholdPreferences): UpdateHouseholdPreferences {
  return {
    privateHousehold: preferences.privateHousehold,
    showAnnouncements: preferences.showAnnouncements,
    lockRecipeEditsFromOtherHouseholds: preferences.lockRecipeEditsFromOtherHouseholds,
    firstDayOfWeek: preferences.firstDayOfWeek,
    defaultShoppingListId: preferences.defaultShoppingListId ?? null,
    recipePublic: preferences.recipePublic,
    recipeShowNutrition: preferences.recipeShowNutrition,
    recipeShowAssets: preferences.recipeShowAssets,
    recipeLandscapeView: preferences.recipeLandscapeView,
    recipeDisableComments: preferences.recipeDisableComments,
    volumeDisplayMode: preferences.volumeDisplayMode,
    massDisplayMode: preferences.massDisplayMode,
    temperatureDisplayTemplate: preferences.temperatureDisplayTemplate,
    primaryVolumeUnits: serializeUnitIds(preferences.primaryVolumeUnits),
    secondaryVolumeUnits: serializeUnitIds(preferences.secondaryVolumeUnits),
    primaryMassUnits: serializeUnitIds(preferences.primaryMassUnits),
    secondaryMassUnits: serializeUnitIds(preferences.secondaryMassUnits),
    foodSubstitutions: serializeFoodSubstitutions(preferences.foodSubstitutions),
  };
}

export const useHouseholdSelf = function () {
  const api = useUserApi();

  async function refreshHouseholdSelf() {
    loading.value = true;
    const { data } = await api.households.getCurrentUserHousehold();
    householdSelfRef.value = data;
    loading.value = false;
  }

  const actions = {
    get() {
      if (!(householdSelfRef.value || loading.value)) {
        refreshHouseholdSelf();
      }

      return householdSelfRef;
    },
    async updatePreferences(overrides?: Partial<UpdateHouseholdPreferences>) {
      if (!householdSelfRef.value) {
        await refreshHouseholdSelf();
      }
      if (!householdSelfRef.value?.preferences) {
        return;
      }

      const payload = {
        ...serializeHouseholdPreferences(householdSelfRef.value.preferences),
        ...overrides,
      };
      const { data } = await api.households.setPreferences(payload);

      if (data) {
        householdSelfRef.value.preferences = data;
      }

      return data || undefined;
    },
  };

  const household = actions.get();

  return { actions, household };
};

export const useAdminHouseholds = function () {
  const api = useAdminApi();
  const loading = ref(false);
  const households = ref<HouseholdInDB[] | null>(null);

  async function getAllHouseholds() {
    loading.value = true;
    const { data } = await api.households.getAll(1, -1, { orderBy: "name, group.name", orderDirection: "asc" });

    if (data) {
      households.value = data.items;
    }
    else {
      households.value = null;
    }

    loading.value = false;
  }

  async function refreshAllHouseholds() {
    await getAllHouseholds();
  }

  async function deleteHousehold(id: string | number) {
    loading.value = true;
    const { data } = await api.households.deleteOne(id);
    loading.value = false;
    await refreshAllHouseholds();
    return data;
  }

  async function createHousehold(payload: HouseholdCreate) {
    loading.value = true;
    const { data } = await api.households.createOne(payload);

    if (data && households.value) {
      households.value.push(data);
    }
    loading.value = false;
  }

  function useHouseholdsInGroup(groupIdRef: Ref<string>) {
    return computed(
      () => {
        return (households.value && groupIdRef.value)
          ? households.value.filter(h => h.groupId === groupIdRef.value)
          : [];
      },
    );
  }

  if (!households.value) {
    getAllHouseholds();
  }

  return {
    households,
    useHouseholdsInGroup,
    getAllHouseholds,
    refreshAllHouseholds,
    deleteHousehold,
    createHousehold,
  };
};
