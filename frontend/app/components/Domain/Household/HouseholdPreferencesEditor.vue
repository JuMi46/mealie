<template>
  <div v-if="preferences">
    <BaseCardSectionTitle :title="$t('household.household-preferences')" />
    <div class="mb-6">
      <v-checkbox v-model="local.privateHousehold" hide-details density="compact" :label="$t('household.private-household')" color="primary" />
      <div class="ml-8">
        <p class="text-subtitle-2 my-0 py-0">
          {{ $t("household.private-household-description") }}
        </p>
        <DocLink class="mt-2" link="/documentation/getting-started/faq/#how-do-private-groups-and-recipes-work" />
      </div>
    </div>
    <div class="mb-6">
      <v-checkbox v-model="local.lockRecipeEditsFromOtherHouseholds" hide-details density="compact" :label="$t('household.lock-recipe-edits-from-other-households')" color="primary" />
      <div class="ml-8">
        <p class="text-subtitle-2 my-0 py-0">
          {{ $t("household.lock-recipe-edits-from-other-households-description") }}
        </p>
      </div>
    </div>
    <div class="mb-6">
      <v-checkbox
        v-model="local.showAnnouncements"
        hide-details
        density="compact"
        color="primary"
        :label="$t('announcements.show-announcements-from-mealie')"
      />
      <div class="ml-8">
        <p class="text-subtitle-2 my-0 py-0">
          {{ $t("announcements.show-announcements-setting-description") }}
        </p>
      </div>
    </div>
    <v-select
      v-model="local.firstDayOfWeek"
      :prepend-icon="$globals.icons.calendarWeekBegin"
      :items="allDays"
      item-title="name"
      item-value="value"
      :label="$t('settings.first-day-of-week')"
      variant="underlined"
      flat
    />
    <v-text-field
      v-model="local.temperatureDisplayTemplate"
      :label="$t('household.temperature-display-template')"
      :hint="$t('household.temperature-display-template-description')"
      persistent-hint
      variant="underlined"
      flat
    />
    <v-select
      v-model="local.defaultShoppingListId"
      :prepend-icon="$globals.icons.cartCheck"
      :items="shoppingListItems"
      item-title="title"
      item-value="value"
      :label="$t('household.default-shopping-list-when-adding-from-recipes')"
      :hint="$t('household.default-shopping-list-when-adding-from-recipes-description')"
      persistent-hint
      variant="underlined"
      flat
    />

    <BaseCardSectionTitle class="mt-5" :title="$t('household.household-recipe-preferences')">
      {{ $t("household.default-recipe-preferences-description") }}
    </BaseCardSectionTitle>
    <div class="preference-container">
      <div v-for="p in recipePreferences" :key="p.key">
        <v-checkbox v-model="local[p.key]" hide-details density="compact" :label="p.label" color="primary" />
        <p class="ml-8 text-subtitle-2 my-0 py-0">
          {{ p.description }}
        </p>
      </div>
    </div>

    <BaseCardSectionTitle class="mt-5" title="Household Unit Display Preferences">
      Choose unit lists used when displaying volume and mass values for this household.
    </BaseCardSectionTitle>
    <div class="preference-container">
      <v-select
        v-model="local.volumeDisplayMode"
        :items="displayModeItems"
        item-title="title"
        item-value="value"
        label="Volume display mode"
        variant="underlined"
        flat
      />
      <v-select
        v-model="local.primaryVolumeUnits"
        :items="volumeUnitItems"
        item-title="title"
        item-value="value"
        label="Primary volume units"
        variant="underlined"
        flat
        chips
        multiple
      />
      <v-select
        v-model="local.secondaryVolumeUnits"
        :items="volumeUnitItems"
        item-title="title"
        item-value="value"
        label="Secondary volume units"
        variant="underlined"
        flat
        chips
        multiple
      />

      <v-select
        v-model="local.massDisplayMode"
        :items="displayModeItems"
        item-title="title"
        item-value="value"
        label="Mass display mode"
        variant="underlined"
        flat
      />
      <v-select
        v-model="local.primaryMassUnits"
        :items="massUnitItems"
        item-title="title"
        item-value="value"
        label="Primary mass units"
        variant="underlined"
        flat
        chips
        multiple
      />
      <v-select
        v-model="local.secondaryMassUnits"
        :items="massUnitItems"
        item-title="title"
        item-value="value"
        label="Secondary mass units"
        variant="underlined"
        flat
        chips
        multiple
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ReadHouseholdPreferences, ShoppingListSummary } from "~/lib/api/types/household";
import type { IngredientUnit } from "~/lib/api/types/recipe";
import { useUserApi } from "~/composables/api";

type UnitPreferenceValue = string | { id?: string | null };

function normalizeUnitPreferenceValues(values: UnitPreferenceValue[] | undefined): string[] {
  if (!values?.length) {
    return [];
  }

  return values.flatMap((value) => {
    if (typeof value === "string") {
      return value;
    }

    return value.id ? [value.id] : [];
  });
}

const preferences = defineModel<ReadHouseholdPreferences>({ required: true });
const local = reactive({
  ...preferences.value,
  defaultShoppingListId: (preferences.value as { defaultShoppingListId?: string | null }).defaultShoppingListId ?? null,
  temperatureDisplayTemplate: preferences.value.temperatureDisplayTemplate ?? "℃ / ℉",
  primaryVolumeUnits: normalizeUnitPreferenceValues(preferences.value.primaryVolumeUnits as UnitPreferenceValue[] | undefined),
  secondaryVolumeUnits: normalizeUnitPreferenceValues(preferences.value.secondaryVolumeUnits as UnitPreferenceValue[] | undefined),
  primaryMassUnits: normalizeUnitPreferenceValues(preferences.value.primaryMassUnits as UnitPreferenceValue[] | undefined),
  secondaryMassUnits: normalizeUnitPreferenceValues(preferences.value.secondaryMassUnits as UnitPreferenceValue[] | undefined),
  volumeDisplayMode: preferences.value.volumeDisplayMode ?? "primary_only",
  massDisplayMode: preferences.value.massDisplayMode ?? "primary_only",
});
watch(local, (newVal) => {
  preferences.value = {
    ...newVal,
    primaryVolumeUnits: normalizeUnitPreferenceValues(newVal.primaryVolumeUnits as UnitPreferenceValue[] | undefined),
    secondaryVolumeUnits: normalizeUnitPreferenceValues(newVal.secondaryVolumeUnits as UnitPreferenceValue[] | undefined),
    primaryMassUnits: normalizeUnitPreferenceValues(newVal.primaryMassUnits as UnitPreferenceValue[] | undefined),
    secondaryMassUnits: normalizeUnitPreferenceValues(newVal.secondaryMassUnits as UnitPreferenceValue[] | undefined),
  } as unknown as ReadHouseholdPreferences;
});

const i18n = useI18n();
const api = useUserApi();

type UnitKind = "mass" | "volume";
type UnitItem = { title: string; value: string; kind: UnitKind };

const MASS_STANDARD_UNITS = new Set(["gram", "kilogram", "ounce", "pound"]);
const VOLUME_STANDARD_UNITS = new Set(["milliliter", "liter", "fluid_ounce", "cup"]);

function unitKindByStandardUnit(standardUnit: IngredientUnit["standardUnit"]): UnitKind | null {
  if (!standardUnit) {
    return null;
  }

  if (MASS_STANDARD_UNITS.has(standardUnit)) {
    return "mass";
  }

  if (VOLUME_STANDARD_UNITS.has(standardUnit)) {
    return "volume";
  }

  return null;
}

const unitItems = ref<UnitItem[]>([]);
const volumeUnitItems = computed(() => unitItems.value.filter(unit => unit.kind === "volume"));
const massUnitItems = computed(() => unitItems.value.filter(unit => unit.kind === "mass"));
const shoppingLists = ref<ShoppingListSummary[]>([]);
const shoppingListItems = computed(() => [
  { title: i18n.t("general.none"), value: null },
  ...shoppingLists.value.map(list => ({ title: list.name, value: list.id })),
]);
const displayModeItems = [
  { title: "Primary only", value: "primary_only" },
  { title: "Secondary only", value: "secondary_only" },
  { title: "Both", value: "both" },
];

onMounted(async () => {
  const [{ data: unitData }, { data: shoppingListData }] = await Promise.all([
    api.units.getAll(1, -1, { orderBy: "name", orderDirection: "asc" }),
    api.shopping.lists.getAll(1, -1, { orderBy: "name", orderDirection: "asc" }),
  ]);

  shoppingLists.value = (shoppingListData?.items ?? []) as ShoppingListSummary[];

  unitItems.value = (unitData?.items ?? []).flatMap((unit) => {
    const kind = unitKindByStandardUnit(unit.standardUnit);

    if (!kind) {
      return [];
    }

    return {
      title: unit.name,
      value: unit.id,
      kind,
    };
  });
});

type Preference = {
  key: keyof ReadHouseholdPreferences;
  label: string;
  description: string;
};

const recipePreferences: Preference[] = [
  {
    key: "recipePublic",
    label: i18n.t("group.allow-users-outside-of-your-group-to-see-your-recipes"),
    description: i18n.t("group.allow-users-outside-of-your-group-to-see-your-recipes-description"),
  },
  {
    key: "recipeShowNutrition",
    label: i18n.t("group.show-nutrition-information"),
    description: i18n.t("group.show-nutrition-information-description"),
  },
  {
    key: "recipeShowAssets",
    label: i18n.t("group.show-recipe-assets"),
    description: i18n.t("group.show-recipe-assets-description"),
  },
  {
    key: "recipeLandscapeView",
    label: i18n.t("group.default-to-landscape-view"),
    description: i18n.t("group.default-to-landscape-view-description"),
  },
  {
    key: "recipeDisableComments",
    label: i18n.t("group.disable-users-from-commenting-on-recipes"),
    description: i18n.t("group.disable-users-from-commenting-on-recipes-description"),
  },
];

const allDays = [
  {
    name: i18n.t("general.sunday"),
    value: 0,
  },
  {
    name: i18n.t("general.monday"),
    value: 1,
  },
  {
    name: i18n.t("general.tuesday"),
    value: 2,
  },
  {
    name: i18n.t("general.wednesday"),
    value: 3,
  },
  {
    name: i18n.t("general.thursday"),
    value: 4,
  },
  {
    name: i18n.t("general.friday"),
    value: 5,
  },
  {
    name: i18n.t("general.saturday"),
    value: 6,
  },
];
</script>

<style lang="css">
.preference-container {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 600px;
}
</style>
