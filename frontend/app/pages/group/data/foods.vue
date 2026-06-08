<template>
  <div>
    <!-- Merge Dialog -->
    <BaseDialog
      v-model="mergeDialog"
      :icon="$globals.icons.foods"
      :title="$t('data-pages.foods.combine-food')"
      can-confirm
      @confirm="mergeFoods"
    >
      <v-card-text>
        <div>
          {{ $t("data-pages.foods.merge-dialog-text") }}
        </div>
        <v-autocomplete
          v-model="fromFood"
          return-object
          :items="foods"
          :custom-filter="normalizeFilter"
          item-title="name"
          :label="$t('data-pages.foods.source-food')"
        />
        <v-autocomplete
          v-model="toFood"
          return-object
          :items="foods"
          :custom-filter="normalizeFilter"
          item-title="name"
          :label="$t('data-pages.foods.target-food')"
        />

        <template v-if="canMerge && fromFood && toFood">
          <div class="text-center">
            {{ $t("data-pages.foods.merge-food-example", { food1: fromFood.name, food2: toFood.name }) }}
          </div>
        </template>
      </v-card-text>
    </BaseDialog>

    <!-- Seed Dialog -->
    <BaseDialog
      v-model="seedDialog"
      :icon="$globals.icons.foods"
      :title="$t('data-pages.seed-data')"
      can-confirm
      @confirm="seedDatabase"
    >
      <v-card-text>
        <div class="pb-2">
          {{ $t("data-pages.foods.seed-dialog-text") }}
        </div>
        <v-autocomplete
          v-model="locale"
          :items="locales"
          item-title="name"
          :custom-filter="normalizeFilter"
          :label="$t('data-pages.select-language')"
          class="my-3"
          hide-details
          variant="outlined"
          offset
        >
          <template #item="{ item, props }">
            <v-list-item v-bind="props">
              <v-list-item-subtitle>
                {{ item.progress }}% {{ $t("language-dialog.translated") }}
              </v-list-item-subtitle>
            </v-list-item>
          </template>
        </v-autocomplete>

        <v-alert v-if="foods && foods.length > 0" type="error" class="mb-0 text-body-2">
          {{ $t("data-pages.foods.seed-dialog-warning") }}
        </v-alert>
      </v-card-text>
    </BaseDialog>

    <!-- Alias Sub-Dialog -->
    <RecipeDataAliasManagerDialog
      v-if="editForm.data"
      v-model="aliasManagerDialog"
      :data="editForm.data"
      @submit="updateFoodAlias"
      @cancel="aliasManagerDialog = false"
    />

    <!-- Bulk Assign Labels Dialog -->
    <BaseDialog
      v-model="bulkAssignLabelDialog"
      :title="$t('data-pages.labels.assign-label')"
      :icon="$globals.icons.tags"
      can-confirm
      @confirm="assignSelected"
    >
      <v-card-text>
        <v-card class="mb-4">
          <v-card-title>{{ $t("general.caution") }}</v-card-title>
          <v-card-text>{{ $t("data-pages.foods.label-overwrite-warning") }}</v-card-text>
        </v-card>

        <v-autocomplete
          v-model="bulkAssignLabelId"
          clearable
          :items="allLabels"
          :custom-filter="normalizeFilter"
          item-value="id"
          item-title="name"
          :label="$t('data-pages.foods.food-label')"
        />
        <v-card variant="outlined">
          <v-virtual-scroll height="400" item-height="25" :items="bulkAssignTarget">
            <template #default="{ item }">
              <v-list-item class="pb-2">
                <v-list-item-title>{{ item.name }}</v-list-item-title>
              </v-list-item>
            </template>
          </v-virtual-scroll>
        </v-card>
      </v-card-text>
    </BaseDialog>

    <GroupDataPage
      :icon="$globals.icons.foods"
      :title="$t('data-pages.foods.food-data')"
      :create-title="$t('data-pages.foods.create-food')"
      :edit-title="$t('data-pages.foods.edit-food')"
      :table-headers="tableHeaders"
      :table-config="tableConfig"
      :data="foods || []"
      :bulk-actions="[
        { icon: $globals.icons.delete, text: $t('general.delete'), event: 'delete-selected' },
        { icon: $globals.icons.tags, text: $t('data-pages.labels.assign-label'), event: 'assign-selected' },
      ]"
      :create-form="createForm"
      :edit-form="editForm"
      :on-delete-dialog-open="onDeleteDialogOpen"
      @create-one="handleCreate"
      @edit-one="handleEdit"
      @delete-one="foodStore.actions.deleteOne"
      @bulk-action="handleBulkAction"
    >
      <template #table-button-row>
        <BaseButton @click="mergeDialog = true">
          <template #icon>
            {{ $globals.icons.externalLink }}
          </template>
          {{ $t("data-pages.combine") }}
        </BaseButton>
      </template>

      <template #[`item.label`]="{ item }">
        <MultiPurposeLabel v-if="item.label" :label="item.label">
          {{ item.label.name }}
        </MultiPurposeLabel>
      </template>

      <template #[`item.onHand`]="{ item }">
        <v-icon :color="item.onHand ? 'success' : undefined">
          {{ item.onHand ? $globals.icons.check : $globals.icons.close }}
        </v-icon>
      </template>

      <template #[`item.substitutionDisplay`]="{ item }">
        {{ item.substitutionDisplay || "" }}
      </template>

      <template #[`item.substitutionRatio`]="{ item }">
        {{ item.substitutionRatio ?? "" }}
      </template>

      <template #[`item.createdAt`]="{ item }">
        {{ item.createdAt ? $d(new Date(item.createdAt)) : "" }}
      </template>

      <template #table-button-bottom>
        <BaseButton
          v-if="isAiEnabled"
          :loading="isTranslatingJp"
          @click="translateJp"
        >
          {{ $t('data-pages.foods.translate-jp') }}
        </BaseButton>
        <BaseButton @click="seedDialog = true">
          <template #icon>
            {{ $globals.icons.database }}
          </template>
          {{ $t("data-pages.seed") }}
        </BaseButton>
      </template>

      <template #create-dialog-bottom>
        <RecipeDensityCalculator
          v-model="createForm.data.density"
          :volume-units="volumeUnits"
          :mass-units="massUnits"
          :default-mass-unit-id="defaultMassUnitId"
          :reset-key="createDensityCalculatorResetKey"
        />
      </template>

      <template #edit-dialog-custom-action>
        <BaseButton edit @click="aliasManagerDialog = true">
          {{ $t("data-pages.manage-aliases") }}
        </BaseButton>
      </template>

      <template #delete-dialog-bottom>
        <v-alert v-if="affectedRecipes.length > 0" type="warning" density="compact" class="mt-4 mb-0">
          {{ $t("data-pages.foods.delete-affects-recipes", { count: affectedRecipesTotal }) }}
          <ul class="mt-1 pl-5 mb-0">
            <li v-for="recipe in affectedRecipes.slice(0, 5)" :key="recipe.slug">
              <NuxtLink :to="recipe.url" class="text-white">{{ recipe.name }}</NuxtLink>
            </li>
          </ul>
          <NuxtLink
            v-if="affectedRecipesTotal > 5"
            :to="affectedRecipesMoreLink"
            class="text-white d-inline-block mt-1"
          >
            {{ $t("data-pages.foods.delete-affects-recipes-more", { count: affectedRecipesTotal }) }}
          </NuxtLink>
        </v-alert>
      </template>

      <template #edit-dialog-bottom>
        <RecipeDensityCalculator
          v-model="editForm.data.density"
          :volume-units="volumeUnits"
          :mass-units="massUnits"
          :default-mass-unit-id="defaultMassUnitId"
          :reset-key="editDensityCalculatorResetKey"
        />

        <v-autocomplete
          v-model="editForm.data.substituteTarget"
          clearable
          :items="substituteOptions"
          :custom-filter="normalizeFilter"
          item-title="title"
          item-value="value"
          :label="$t('data-pages.foods.substitute-target')"
          :hint="$t('data-pages.foods.substitute-target-hint')"
          persistent-hint
        />

        <v-text-field
          v-model.number="editForm.data.substitutionRatio"
          type="number"
          :min="0.0001"
          :step="0.1"
          variant="solo-filled"
          :label="$t('data-pages.foods.substitution-ratio')"
          :hint="$t('data-pages.foods.substitution-ratio-hint')"
          persistent-hint
        />
      </template>
    </GroupDataPage>
  </div>
</template>

<script setup lang="ts">
import type { LocaleObject } from "@nuxtjs/i18n";
import RecipeDataAliasManagerDialog from "~/components/Domain/Recipe/RecipeDataAliasManagerDialog.vue";
import RecipeDensityCalculator from "~/components/Domain/Recipe/RecipeDensityCalculator.vue";
import { validators } from "~/composables/use-validators";
import { useUserApi } from "~/composables/api";
import type { UpdateHouseholdFoodSubstitution } from "~/lib/api/types/household";
import type { CreateIngredientFood, IngredientFood, IngredientFoodAlias, RecipeSummary } from "~/lib/api/types/recipe";
import MultiPurposeLabel from "~/components/Domain/ShoppingList/MultiPurposeLabel.vue";
import { useGroupSelf } from "~/composables/use-groups";
import { useLocales } from "~/composables/use-locales";
import { normalizeFilter } from "~/composables/use-utils";
import { useFoodStore, useLabelStore, useUnitStore } from "~/composables/store";
import type { MultiPurposeLabelOut } from "~/lib/api/types/labels";
import type { AutoFormItems } from "~/types/auto-forms";
import type { TableHeaders, TableConfig } from "~/components/global/CrudTable.vue";
import { fieldTypes } from "~/composables/forms";
import { compareLabel } from "~/composables/use-extend-object";

interface CreateIngredientFoodWithOnHand extends CreateIngredientFood {
  onHand: boolean;
  householdsWithIngredientFood: string[];
}

interface IngredientFoodWithOnHand extends IngredientFood {
  onHand: boolean;
  householdLabelId?: string | null;
  substituteTarget?: string | null;
  substitutionRatio?: number;
  substitutionDisplay?: string | null;
}

type SubstituteOptionType = "food" | "recipe";

interface SubstituteOption {
  title: string;
  value: string;
  type: SubstituteOptionType;
  id: string;
}

const userApi = useUserApi();
const i18n = useI18n();
const auth = useMealieAuth();
const { group } = useGroupSelf();
const { household, actions: householdActions } = useHouseholdSelf();
const isTranslatingJp = ref(false);
const isAiEnabled = computed(() => !!group.value?.aiProviderSettings?.aiEnabled);
const tableConfig: TableConfig = {
  hideColumns: true,
  canExport: true,
};
const tableHeaders: TableHeaders[] = [
  {
    text: i18n.t("general.id"),
    value: "id",
    show: false,
  },
  {
    text: i18n.t("general.name"),
    value: "name",
    show: true,
    sortable: true,
  },
  {
    text: i18n.t("data-pages.foods.name-jp"),
    value: "nameJp",
    show: false,
    sortable: true,
  },
  {
    text: i18n.t("data-pages.foods.name-jp-kanji"),
    value: "nameJpKanji",
    show: false,
    sortable: true,
  },
  {
    text: i18n.t("general.plural-name"),
    value: "pluralName",
    show: true,
    sortable: true,
  },
  {
    text: i18n.t("recipe.description"),
    value: "description",
    show: false,
  },
  {
    text: i18n.t("data-pages.foods.density"),
    value: "density",
    show: false,
    sortable: true,
  },
  {
    text: i18n.t("data-pages.foods.tip"),
    value: "tip",
    show: false,
    sortable: true,
  },
  {
    text: i18n.t("shopping-list.label"),
    value: "label",
    show: true,
    sortable: true,
    sort: (a: MultiPurposeLabelOut | null, b: MultiPurposeLabelOut | null) => compareLabel(a, b),
  },
  {
    text: i18n.t("tool.on-hand"),
    value: "onHand",
    show: true,
    sortable: true,
  },
  {
    text: i18n.t("data-pages.foods.substitute-target"),
    value: "substitutionDisplay",
    show: false,
    sortable: true,
  },
  {
    text: i18n.t("data-pages.foods.substitution-ratio"),
    value: "substitutionRatio",
    show: false,
    sortable: true,
  },
  {
    text: i18n.t("general.date-added"),
    value: "createdAt",
    show: false,
    sortable: true,
  },
];

const userHousehold = computed(() => auth.user.value?.householdSlug || "");
const userGroup = computed(() => auth.user.value?.groupSlug || "");
const foodStore = useFoodStore();
const recipeOptions = ref<RecipeSummary[]>([]);
const substitutionsBySourceFoodId = computed(() => {
  const substitutions = household.value?.preferences?.foodSubstitutions ?? [];
  return new Map(substitutions.map(substitution => [substitution.sourceFoodId, substitution]));
});
const foodsById = computed(() => {
  return new Map(foodStore.store.value.map(food => [food.id, food]));
});
const recipesById = computed(() => {
  return new Map(
    recipeOptions.value
      .filter((recipe): recipe is RecipeSummary & { id: string } => Boolean(recipe.id))
      .map(recipe => [recipe.id, recipe]),
  );
});
const foods = computed(() => foodStore.store.value.map((food) => {
  const onHand = food.householdsWithIngredientFood?.includes(userHousehold.value) || false;
  const substitution = substitutionsBySourceFoodId.value.get(food.id);

  let substituteTarget: string | null = null;
  let substitutionDisplay: string | null = null;
  let substitutionRatio: number | undefined;

  if (substitution?.substituteFoodId) {
    const substituteFood = foodsById.value.get(substitution.substituteFoodId);
    substituteTarget = `food:${substitution.substituteFoodId}`;
    substitutionDisplay = `${i18n.t("data-pages.foods.substitute-type-food")} ${substituteFood?.name ?? substitution.substituteFoodId}`;
    substitutionRatio = substitution.ratio && substitution.ratio > 0 ? substitution.ratio : 1;
  }
  else if (substitution?.substituteRecipeId) {
    const substituteRecipe = recipesById.value.get(substitution.substituteRecipeId);
    substituteTarget = `recipe:${substitution.substituteRecipeId}`;
    substitutionDisplay = `${i18n.t("data-pages.foods.substitute-type-recipe")} ${substituteRecipe?.name ?? substitution.substituteRecipeId}`;
    substitutionRatio = substitution.ratio && substitution.ratio > 0 ? substitution.ratio : 1;
  }

  return {
    ...food,
    onHand,
    substituteTarget,
    substitutionDisplay,
    substitutionRatio,
  } as IngredientFoodWithOnHand;
}));
const substituteOptions = computed<SubstituteOption[]>(() => {
  const foodItems = foods.value.map(food => ({
    title: `${i18n.t("data-pages.foods.substitute-type-food")} ${food.name}`,
    value: `food:${food.id}`,
    type: "food" as const,
    id: food.id,
  }));
  const recipeItems = recipeOptions.value.flatMap((recipe) => {
    if (!recipe.id) {
      return [];
    }

    return [{
      title: `${i18n.t("data-pages.foods.substitute-type-recipe")} ${recipe.name}`,
      value: `recipe:${recipe.id}`,
      type: "recipe" as const,
      id: recipe.id,
    }];
  });

  return [...foodItems, ...recipeItems];
});

// ============================================================
// Units (for density calculator)
const { store: allUnits } = useUnitStore();

const VOLUME_STANDARD_UNIT = "milliliter";
const MASS_STANDARD_UNIT = "gram";

const volumeUnits = computed(() =>
  allUnits.value.filter(u => u.standardUnit === VOLUME_STANDARD_UNIT),
);
const massUnits = computed(() =>
  allUnits.value.filter(u => u.standardUnit === MASS_STANDARD_UNIT),
);
const defaultMassUnitId = computed<string | null>(() => {
  const primaryMassUnits = household.value?.preferences?.primaryMassUnits ?? [];
  if (primaryMassUnits.length === 0) {
    return null;
  }

  const sorted = [...primaryMassUnits].sort(
    (a, b) => (a.standardQuantity ?? Infinity) - (b.standardQuantity ?? Infinity),
  );

  return sorted.at(0)?.id ?? null;
});

// ============================================================
// Labels
const { store: allLabels } = useLabelStore();
const labelOptions = computed(() => allLabels.value.map(label => ({ text: parseLabelName(label, true, i18n.t("shopping-list.no-label")), value: label.id })) || []);

// ============================================================
// Form items (shared)
type FormMode = "create" | "edit";
type ModeAwareFormItem = AutoFormItems[number] & { onlyInMode?: FormMode };

const allFormItems = computed((): ModeAwareFormItem[] => ([
  {
    label: i18n.t("general.name"),
    varName: "name",
    type: fieldTypes.TEXT,
    rules: [validators.required],
  },
  {
    label: i18n.t("general.plural-name"),
    varName: "pluralName",
    type: fieldTypes.TEXT,
  },
  {
    label: i18n.t("recipe.description"),
    varName: "description",
    type: fieldTypes.TEXT,
  },
  {
    label: i18n.t("data-pages.foods.tip"),
    varName: "tip",
    type: fieldTypes.TEXT,
  },
  {
    label: i18n.t("data-pages.foods.food-label"),
    varName: "labelId",
    type: fieldTypes.SELECT,
    options: labelOptions.value,
    selectReturnValue: "value",
  },
  {
    label: i18n.t("data-pages.foods.household-food-label-override"),
    varName: "householdLabelId",
    type: fieldTypes.SELECT,
    onlyInMode: "edit",
    options: labelOptions.value,
    selectReturnValue: "value",
  },
  {
    label: i18n.t("tool.on-hand"),
    varName: "onHand",
    type: fieldTypes.BOOLEAN,
    hint: i18n.t("data-pages.foods.on-hand-checkbox-label"),
  },
  {
    label: i18n.t("data-pages.foods.name-jp"),
    varName: "nameJp",
    type: fieldTypes.TEXT,
  },
  {
    label: i18n.t("data-pages.foods.name-jp-kanji"),
    varName: "nameJpKanji",
    type: fieldTypes.TEXT,
  },
]));

function getFormItems(mode: FormMode): AutoFormItems {
  return allFormItems.value.filter((item) => {
    return !item.onlyInMode || item.onlyInMode === mode;
  }) as AutoFormItems;
}

// ===============================================================
// Create

const createForm = reactive({
  get items() {
    return getFormItems("create");
  },
  data: {
    name: "",
    nameJp: "",
    nameJpKanji: "",
    onHand: false,
    householdsWithIngredientFood: [],
  } as CreateIngredientFoodWithOnHand,
});
const createDensityCalculatorResetKey = ref(0);

async function handleCreate() {
  if (!createForm.data || !createForm.data.name) {
    return;
  }

  if (createForm.data.onHand) {
    createForm.data.householdsWithIngredientFood = [userHousehold.value];
  }

  // @ts-expect-error the createOne function erroneously expects an id because it uses the IngredientFood type
  await foodStore.actions.createOne(createForm.data);
  createForm.data = {
    name: "",
    nameJp: "",
    nameJpKanji: "",
    onHand: false,
    householdsWithIngredientFood: [],
  };
  createDensityCalculatorResetKey.value += 1;
}

// ===============================================================
// Edit

const editForm = reactive({
  get items() {
    return getFormItems("edit");
  },
  data: {} as IngredientFoodWithOnHand,
});

const editDensityCalculatorResetKey = computed(() => editForm.data?.id ?? "");

async function handleEdit() {
  if (!editForm.data) {
    return;
  }
  if (!editForm.data.householdsWithIngredientFood) {
    editForm.data.householdsWithIngredientFood = [];
  }

  if (editForm.data.onHand && !editForm.data.householdsWithIngredientFood.includes(userHousehold.value)) {
    editForm.data.householdsWithIngredientFood.push(userHousehold.value);
  }
  else if (!editForm.data.onHand && editForm.data.householdsWithIngredientFood.includes(userHousehold.value)) {
    const idx = editForm.data.householdsWithIngredientFood.indexOf(userHousehold.value);
    if (idx !== -1) editForm.data.householdsWithIngredientFood.splice(idx, 1);
  }

  await foodStore.actions.updateOne(editForm.data);
  await saveFoodSubstitution(editForm.data);
  editForm.data = {} as IngredientFoodWithOnHand;
}

async function saveFoodSubstitution(food: IngredientFoodWithOnHand) {
  if (!(household.value?.preferences && food.id)) {
    return;
  }

  const currentSubstitutions: UpdateHouseholdFoodSubstitution[] = (household.value.preferences.foodSubstitutions ?? [])
    .map(substitution => ({
      sourceFoodId: substitution.sourceFoodId,
      substituteFoodId: substitution.substituteFoodId,
      substituteRecipeId: substitution.substituteRecipeId,
      ratio: substitution.ratio,
    }));
  const nextSubstitutions = currentSubstitutions.filter(sub => sub.sourceFoodId !== food.id);

  const ratio = typeof food.substitutionRatio === "number" && food.substitutionRatio > 0 ? food.substitutionRatio : 1;
  const target = parseSubstituteTarget(food.substituteTarget || null);
  if (target) {
    nextSubstitutions.push({
      sourceFoodId: food.id,
      substituteFoodId: target.type === "food" ? target.id : null,
      substituteRecipeId: target.type === "recipe" ? target.id : null,
      ratio,
    });
  }

  await householdActions.updatePreferences({ foodSubstitutions: nextSubstitutions });
}

function parseSubstituteTarget(target: string | null): { type: SubstituteOptionType; id: string } | null {
  if (!target) {
    return null;
  }

  const [type, id] = target.split(":", 2);
  if (!id || (type !== "food" && type !== "recipe")) {
    return null;
  }

  return { type, id };
}

function hydrateSubstitutionFields(foodId?: string) {
  if (!foodId || !editForm.data) {
    return;
  }

  const substitutions = household.value?.preferences?.foodSubstitutions ?? [];
  const substitution = substitutions.find(sub => sub.sourceFoodId === foodId);

  if (!substitution) {
    editForm.data.substituteTarget = null;
    editForm.data.substitutionRatio = 1;
    return;
  }

  if (substitution.substituteFoodId) {
    editForm.data.substituteTarget = `food:${substitution.substituteFoodId}`;
  }
  else if (substitution.substituteRecipeId) {
    editForm.data.substituteTarget = `recipe:${substitution.substituteRecipeId}`;
  }
  else {
    editForm.data.substituteTarget = null;
  }

  editForm.data.substitutionRatio = substitution.ratio && substitution.ratio > 0 ? substitution.ratio : 1;
}

// ============================================================
// Bulk Actions
async function handleBulkAction(event: string, items: IngredientFoodWithOnHand[]) {
  if (event === "delete-selected") {
    const ids = items.map(item => item.id);
    await foodStore.actions.deleteMany(ids);
    affectedRecipes.value = [];
    affectedRecipesTotal.value = 0;
    affectedRecipesMoreLink.value = "";
  }
  else if (event === "assign-selected") {
    bulkAssignEventHandler(items);
  }
}

// ============================================================
// Alias Manager

const aliasManagerDialog = ref(false);
function updateFoodAlias(newAliases: IngredientFoodAlias[]) {
  if (!editForm.data) {
    return;
  }
  editForm.data.aliases = newAliases;
  aliasManagerDialog.value = false;
}

// ============================================================
// Delete Foods

// fetch affected recipes before confirming deletion
const affectedRecipes = ref<{ name: string; slug: string; url: string }[]>([]);
const affectedRecipesTotal = ref(0);
const affectedRecipesMoreLink = ref("");

async function onDeleteDialogOpen(items: IngredientFoodWithOnHand[]) {
  const ids = items.map(item => item.id);
  const { data } = await userApi.recipes.search({ foods: ids, perPage: 5 });
  affectedRecipes.value = (data?.items ?? []).map(r => ({
    name: r.name ?? "",
    slug: r.slug ?? "",
    url: `/g/${userGroup.value}/r/${r.slug}`,
  }));
  affectedRecipesTotal.value = data?.total ?? 0;
  affectedRecipesMoreLink.value = `/g/${userGroup.value}?${ids.map(id => `foods=${id}`).join("&")}`;
}

// ============================================================
// Merge Foods

const mergeDialog = ref(false);
const fromFood = ref<IngredientFoodWithOnHand | null>(null);
const toFood = ref<IngredientFoodWithOnHand | null>(null);

const canMerge = computed(() => {
  return fromFood.value && toFood.value && fromFood.value.id !== toFood.value.id;
});

async function mergeFoods() {
  if (!canMerge.value || !fromFood.value || !toFood.value) {
    return;
  }

  const { data } = await userApi.foods.merge(fromFood.value.id, toFood.value.id);

  if (data) {
    foodStore.actions.refresh();
  }
}

// ============================================================
// Seed

const seedDialog = ref(false);
const locale = ref("");

const { locales: LOCALES, locale: currentLocale } = useLocales();

onMounted(() => {
  locale.value = currentLocale.value;

  userApi.recipes.getAll(1, -1).then(({ data }) => {
    recipeOptions.value = data?.items || [];
  });
});

watch(
  () => editForm.data?.id,
  (foodId) => {
    hydrateSubstitutionFields(foodId);
  },
);

const locales = LOCALES.filter(locale =>
  (i18n.locales.value as LocaleObject[]).map(i18nLocale => i18nLocale.code).includes(locale.value as any),
);

async function seedDatabase() {
  const { data } = await userApi.seeders.foods({ locale: locale.value });

  if (data) {
    foodStore.actions.refresh();
  }
}

async function translateJp() {
  isTranslatingJp.value = true;

  try {
    await userApi.foods.translateJp();
    await foodStore.actions.refresh();
  }
  finally {
    isTranslatingJp.value = false;
  }
}

// ============================================================
// Bulk Assign Labels
const bulkAssignLabelDialog = ref(false);
const bulkAssignTarget = ref<IngredientFoodWithOnHand[]>([]);
const bulkAssignLabelId = ref<string | undefined>();

function bulkAssignEventHandler(selection: IngredientFoodWithOnHand[]) {
  bulkAssignTarget.value = selection;
  bulkAssignLabelDialog.value = true;
}

async function assignSelected() {
  if (!bulkAssignLabelId.value) {
    return;
  }
  for (const item of bulkAssignTarget.value) {
    item.labelId = bulkAssignLabelId.value;
    await foodStore.actions.updateOne(item);
  }
  bulkAssignTarget.value = [];
  bulkAssignLabelId.value = undefined;
  foodStore.actions.refresh();
}
</script>
