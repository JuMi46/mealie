<template>
  <div>
    <v-container :fluid="isCookMode" :class="isCookMode ? 'pa-0' : ''">
      <BasePageTitle v-if="!isCookMode" divider>
        <template #title>
          {{ $t("recipe.combined-view") }}
        </template>
        <template v-if="openRecipes.length === 0" #content>
          {{ $t("recipe.combined-view-description") }}
        </template>
      </BasePageTitle>

      <v-sheet
        v-if="openRecipes.length > 0"
        :height="isCookMode && !hasLinkedIngredients && activeRecipe && $vuetify.display.smAndUp ? 'calc(100vh - 48px)' : 'auto'"
        class="overflow-hidden"
      >
        <v-row :style="isCookMode && !hasLinkedIngredients && activeRecipe ? 'height: 100%' : ''" :no-gutters="isCookMode && !hasLinkedIngredients && !!activeRecipe" class="overflow-hidden">
          <v-col
            v-if="!isCookMode || !hasLinkedIngredients"
            cols="12"
            :md="!isCookMode ? 4 : undefined"
            :sm="isCookMode ? 5 : undefined"
            :class="isCookMode ? 'overflow-y-auto pl-4 pr-3 py-2' : ''"
            :style="isCookMode ? 'height: 100%' : ''"
          >
            <v-card v-if="!isCookMode" class="mb-4">
              <RecipeIngredients
                :value="openRecipes.map(recipe => (
                  {
                    recipeName: recipe.name || '',
                    recipeIngredient:
                      recipe.recipeIngredient
                      || [],
                    scale:
                      scaleFor(recipe.slug) }) as IngredientsByRecipe)"
                :is-cook-mode="isCookMode"
              />
            </v-card>

            <template v-else>
              <RecipePageIngredientToolsView
                v-if="activeRecipe"
                :recipe="activeRecipe"
                :scale="scaleFor(activeRecipe?.slug)"
                :is-cook-mode="isCookMode"
                :is-combined-view="true"
              />
              <v-divider />
            </template>
          </v-col>

          <v-col
            cols="12"
            :md="!isCookMode ? 8 : undefined"
            :sm="isCookMode && !hasLinkedIngredients ? 7 : undefined"
            :class="isCookMode && !hasLinkedIngredients ? ['overflow-y-auto', $vuetify.display.smAndDown ? 'py-2' : 'py-6'] : ''"
            :style="isCookMode && !hasLinkedIngredients ? 'height: 100%' : ''"
          >
            <h2 v-if="isCookMode && !hasLinkedIngredients" class="text-h5 px-4 font-weight-medium opacity-80">
              {{ $t('recipe.instructions') }}
            </h2>

            <v-card>
              <v-tabs v-model="activeTabSlug" color="primary" align-tabs="start">
                <v-tab v-for="recipe in openRecipes" :key="recipe.slug" :value="recipe.slug">
                  {{ recipe.name }}
                </v-tab>
              </v-tabs>

              <v-window v-model="activeTabSlug" class="mt-4">
                <v-window-item v-for="recipe in openRecipes" :key="recipe.slug" :value="recipe.slug">
                  <RecipePageInstructions
                    v-if="!isCookMode"
                    :model-value="recipe.recipeInstructions || []"
                    :assets="recipe.assets || []"
                    :class="isCookMode
                      ? hasLinkedIngredients
                        ? 'overflow-y-hidden mt-n5 px-2 px-md-4'
                        : 'overflow-y-hidden px-4'
                      : ''"
                    :recipe="recipe as any"
                    :scale="scaleFor(recipe.slug)"
                    :is-combined-view="true"
                    @update:model-value="recipe.recipeInstructions = $event"
                    @update:assets="recipe.assets = $event"
                  />
                  <RecipePageInstructions
                    v-else-if="activeRecipe"
                    :model-value="activeRecipe.recipeInstructions || []"
                    :assets="activeRecipe.assets || []"
                    :class="isCookMode
                      ? hasLinkedIngredients
                        ? 'overflow-y-hidden mt-n5 px-2 px-md-4'
                        : 'overflow-y-hidden px-4'
                      : ''"
                    :recipe="activeRecipe as any"
                    :scale="scaleFor(activeRecipe?.slug)"
                    :is-combined-view="true"
                    @update:model-value="activeRecipe.recipeInstructions = $event"
                    @update:assets="activeRecipe.assets = $event"
                  />
                  <template v-if="ingredientTipsByRecipe?.length">
                    <v-divider class="my-2" />
                    <v-list density="compact" class="px-2 px-md-4">
                      <v-list-item
                        v-for="tip in ingredientTipsByRecipe"
                        :key="tip.ingredient"
                      >
                        {{ tip.text }}
                      </v-list-item>
                    </v-list>
                  </template>
                </v-window-item>
              </v-window>
            </v-card>

            <div v-if="isCookMode && hasLinkedIngredients && (notLinkedIngredients?.length || 0) > 0" class="px-2 px-md-4 pb-4">
              <v-divider />
              <v-card flat>
                <v-card-title>{{ $t("recipe.not-linked-ingredients") }}</v-card-title>
                <RecipeIngredients
                  v-if="activeRecipe"
                  :value="[{
                    recipeName: activeRecipe.name || '',
                    recipeIngredient: notLinkedIngredients,
                    scale: scaleFor(activeRecipe.slug) } as IngredientsByRecipe]"
                  :is-cook-mode="isCookMode"
                />
              </v-card>
            </div>
          </v-col>
        </v-row>
      </v-sheet>
    </v-container>

    <v-container v-if="!isCookMode">
      <v-card class="mb-4">
        <v-card-title>{{ $t("recipe.open-recipes") }}</v-card-title>
        <v-list v-if="openRecipes.length > 0">
          <v-list-item v-for="recipe in openRecipes" :key="recipe.slug">
            <template #prepend>
              <NuxtLink :to="`/g/${groupSlug}/r/${recipe.slug}`">
                {{ recipe.name }}
              </NuxtLink>
            </template>
            <template #append>
              <div class="d-flex align-center ga-2">
                <RecipePageScale :value="scaleFor(recipe.slug)" :recipe="recipe" @update:model-value="setScale(recipe.slug, $event)" />
                <v-btn icon size="small" color="error" @click="removeRecipe(recipe.slug)">
                  <v-icon>{{ $globals.icons.delete }}</v-icon>
                </v-btn>
              </div>
            </template>
          </v-list-item>
        </v-list>
        <div class="d-flex flex-wrap ga-2 align-center">
          <BaseButton v-if="openRecipes.length > 0" @click="showPicker = !showPicker">
            <template #icon>
              {{ $globals.icons.plus }}
            </template>
            {{ $t("recipe.add-recipe") }}
          </BaseButton>
          <BaseButton v-if="openRecipes.length > 0" @click="madeTheseDialog = true">
            {{ $t("recipe.made-these") }}
          </BaseButton>
        </div>

        <div v-if="showPicker || openRecipes.length === 0" class="mt-4">
          <v-autocomplete
            v-model="selectedRecipeSlug"
            :items="pickerItems"
            item-title="label"
            item-value="slug"
            clearable
            :label="$t('recipe.select-recipe')"
          >
            <template #item="{ props, item }">
              <v-list-item v-bind="props">
                <template #prepend>
                  <v-icon v-if="item.recommended">
                    {{ $globals.icons.star }}
                  </v-icon>
                </template>
              </v-list-item>
            </template>
          </v-autocomplete>
          <BaseButton :disabled="!selectedRecipeSlug" @click="addSelectedRecipe">
            {{ $t("recipe.open-recipe") }}
          </BaseButton>
        </div>
      </v-card>

      <BaseDialog
        v-model="madeTheseDialog"
        :title="$t('recipe.made-these')"
        :icon="$globals.icons.check"
        can-confirm
        @confirm="markAllAsMade"
      >
        <v-card-text>
          <v-text-field v-model="madeTheseAt" type="datetime-local" :label="$t('general.date')" />
        </v-card-text>
      </BaseDialog>
    </v-container>

    <v-btn
      v-if="isCookMode"
      icon
      color="primary"
      style="position: fixed; right: 12px; top: 60px"
      @click="toggleCookMode()"
    >
      <v-icon>{{ $globals.icons.close }}</v-icon>
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import RecipeIngredients from "~/components/Domain/Recipe/RecipeIngredients.vue";
import type { IngredientsByRecipe } from "~/components/Domain/Recipe/RecipeIngredients.vue";
import RecipePageInstructions from "~/components/Domain/Recipe/RecipePage/RecipePageParts/RecipePageInstructions.vue";
import { useUserApi } from "~/composables/api";
import type { Recipe, RecipeSummary } from "~/lib/api/types/recipe";
import { clearPageState, PageMode, usePageState } from "~/composables/recipe-page/shared-state";
import { useHouseholdSelf } from "~/composables/use-households";
import { useRouteQuery } from "~/composables/use-router";

interface PickerItem {
  slug: string;
  label: string;
  recommended: boolean;
}

const i18n = useI18n();
const route = useRoute();
const router = useRouter();
const api = useUserApi();
const { household } = useHouseholdSelf();

const temperatureDisplayTemplate = computed(() => household.value?.preferences?.temperatureDisplayTemplate);
const groupSlug = computed(() => String(route.params.groupSlug || ""));

const { setMode, isCookMode, toggleCookMode } = usePageState("combined-view");
const allRecipes = ref<RecipeSummary[]>([]);
const openRecipes = ref<Recipe[]>([]);
const selectedRecipeSlug = ref<string | null>(null);
const showPicker = ref(true);
const activeTabSlug = ref<string>("");
const scalesBySlug = ref<Record<string, number>>({});

const madeTheseDialog = ref(false);
const madeTheseAt = ref<string>(new Date().toISOString().slice(0, 16));

/** =============================================================
 * onMounted and query handling
 */
const paramsRecipes = useRouteQuery<string>("recipes", "");
const paramsTab = useRouteQuery<string>("tab", "");

onMounted(async () => {
  const response = await api.recipes.search({ perPage: -1, orderBy: "name", orderDirection: "asc" });
  allRecipes.value = response.data.items || [];

  if (paramsRecipes.value) {
    const recipes = paramsRecipes.value.split(";").reduce((acc, token) => {
      const [slug, scaleText] = token.split(":");
      if (scaleText === undefined) {
        acc[slug] = 1;
        return acc;
      }
      const scale = Number(scaleText);
      if (slug && Number.isFinite(scale) && scale > 0) {
        acc[slug] = scale;
      }
      return acc;
    }, {} as Record<string, number>);

    const targetSlugs = Object.keys(recipes);
    if (targetSlugs.length) {
      const loaded = await Promise.all(targetSlugs.map(slug => loadRecipe(slug)));
      openRecipes.value = loaded.filter(recipe => !!recipe.slug);
      scalesBySlug.value = recipes;
      if (typeof paramsTab.value === "string") {
        activeTabSlug.value = openRecipes.value[paramsTab.value]?.slug || "";
      }
      else if (openRecipes.value.length > 0) {
        activeTabSlug.value = openRecipes.value[0].slug;
        paramsTab.value = "0";
      }
    }
    else {
      openRecipes.value = [];
      activeTabSlug.value = "";
    }
  }
});

onUnmounted(() => {
  setMode(PageMode.VIEW);
  clearPageState("combined-view");
});

function syncQuery() {
  const query: Record<string, string> = {
    ...route.query as Record<string, string>,
  };

  const serializedScales = Object.entries(scalesBySlug.value)
    .filter(([, scale]) => Number.isFinite(scale) && scale > 0)
    .map(([slug, scale]) => `${slug}:${scale}`)
    .join(";");
  if (serializedScales) {
    query.recipes = serializedScales;
  }
  else {
    delete query.recipes;
  }

  if (activeTabSlug.value) {
    query.tab = openSlugs.value.indexOf(activeTabSlug.value).toString();
  }
  else {
    delete query.tab;
  }
  router.replace({ query });
}

watch(activeTabSlug, () => {
  syncQuery();
});

/** =============================================================
 *
 */

const openSlugs = computed(() => openRecipes.value.map(recipe => recipe.slug).filter(Boolean) as string[]);

const activeRecipe = computed(() => openRecipes.value.length === 0
  ? null
  : openRecipes.value.length === 1
    ? openRecipes.value[0]
    : openRecipes.value.find(recipe => recipe.slug === activeTabSlug.value) || openRecipes.value[0] || null);

function scaleFor(slug: string | undefined): number {
  return slug ? scalesBySlug.value[slug] || 1 : 1;
}

function setScale(slug: string, scale: number) {
  if (!slug || !Number.isFinite(scale) || scale <= 0) {
    return;
  }

  scalesBySlug.value = {
    ...scalesBySlug.value,
    [slug]: scale,
  };

  syncQuery();
}
/** =============================================================
 *
 */

const hasLinkedIngredients = computed(() => {
  return activeRecipe.value?.recipeInstructions?.some(
    step => step.ingredientReferences && step.ingredientReferences.length > 0,
  );
});
const notLinkedIngredients = computed(() => {
  return activeRecipe.value?.recipeIngredient?.filter((ingredient) => {
    return !activeRecipe.value?.recipeInstructions?.some(step =>
      step.ingredientReferences?.map(ref => ref.referenceId).includes(ingredient.referenceId),
    );
  });
});

const ingredientTipsByRecipe = computed(
  () => activeRecipe.value?.recipeIngredient?.reduce((res, ingredient) => {
    if (ingredient.food?.tip && !res.some(tip => tip.ingredient == ingredient.food.name)) {
      res.push({
        text: `${ingredient.food.name}: ${parseTemperaturesInText(ingredient.food.tip, temperatureDisplayTemplate.value)}`,
        ingredient: ingredient.food.name,
      });
    }
    return res;
  }, [] as {
    text: string;
    ingredient: string;
  }[]),
);

/** =============================================================
 * Picker and recommendation logic
 */
const recommendedByMain = computed(() => {
  const mains = openRecipes.value.filter((recipe) => {
    return (recipe.recipeCategory || []).some(category => category.name?.toLowerCase() === "main");
  });

  return mains
    .map((mainRecipe) => {
      const items = (mainRecipe.recommendedSideDishes || [])
        .filter(side => !!side.slug)
        .map((side) => {
          const categoryName = firstCategoryName(side.recipeCategory || []);
          return {
            slug: side.slug || "",
            categoryName,
            sideName: side.name || "",
            label: `${categoryName}: ${side.name}`,
            mainName: mainRecipe.name || "",
          };
        });

      return {
        mainName: mainRecipe.name || "",
        items,
      };
    })
    .filter(group => group.items.length > 0);
});

const pickerItems = computed<PickerItem[]>(() => {
  const seen = new Set<string>();
  const items: PickerItem[] = [];

  for (const group of recommendedByMain.value) {
    for (const item of group.items) {
      if (!item.slug || seen.has(item.slug) || openSlugs.value.includes(item.slug)) {
        continue;
      }
      seen.add(item.slug);
      items.push({
        slug: item.slug,
        label: `${item.categoryName}: ${item.sideName}`,
        recommended: true,
      });
    }
  }

  const normalItems = allRecipes.value
    .filter(recipe => !!recipe.slug && !seen.has(recipe.slug) && !openSlugs.value.includes(recipe.slug))
    .map((recipe) => {
      const category = firstCategory(recipe.recipeCategory || []);
      const categoryName = category?.name || i18n.t("recipe.uncategorized");
      return {
        slug: recipe.slug || "",
        label: `${categoryName}: ${recipe.name}`,
        recommended: false,
        position: category?.position || Number.POSITIVE_INFINITY,
        positionRecipe: category?.positionRecipe || Number.POSITIVE_INFINITY,
      };
    })
    .sort((a, b) => a.positionRecipe - b.positionRecipe);

  return [...items, ...normalItems];
});

function firstCategory(categories: Array<{ name?: string; position?: number; positionRecipe?: number }>) {
  if (!categories.length) {
    return null;
  }

  const sorted = [...categories].sort((a, b) => (a.position || 0) - (b.position || 0));
  return sorted[0];
}

function firstCategoryName(categories: Array<{ name?: string; position?: number }>) {
  const category = firstCategory(categories);
  return category?.name || i18n.t("recipe.uncategorized");
}

/** =============================================================
 * Recipe loading logic
 */
async function loadRecipe(slug: string) {
  const response = await api.recipes.getOne(slug);
  return response.data;
}

async function addSelectedRecipe() {
  if (!selectedRecipeSlug.value) {
    return;
  }

  if (openSlugs.value.includes(selectedRecipeSlug.value)) {
    selectedRecipeSlug.value = null;
    showPicker.value = false;
    return;
  }

  const recipe = await loadRecipe(selectedRecipeSlug.value);
  openRecipes.value = [...openRecipes.value, recipe];
  scalesBySlug.value[recipe.slug] = scalesBySlug.value[recipe.slug] || 1;
  activeTabSlug.value = recipe.slug;

  selectedRecipeSlug.value = null;
  showPicker.value = false;
  syncQuery();
}

function removeRecipe(slug: string) {
  openRecipes.value = openRecipes.value.filter(recipe => recipe.slug !== slug);
  const { [slug]: _removed, ...remainingScales } = scalesBySlug.value;
  scalesBySlug.value = remainingScales;

  if (activeTabSlug.value === slug) {
    activeTabSlug.value = openRecipes.value[0]?.slug || "";
  }

  syncQuery();
}

async function markAllAsMade() {
  if (!openSlugs.value.length || !madeTheseAt.value) {
    madeTheseDialog.value = false;
    return;
  }

  await api.bulk.bulkMarkMade({
    recipes: openSlugs.value,
    timestamp: new Date(madeTheseAt.value).toISOString(),
  });

  madeTheseDialog.value = false;
}

/** =============================================================
 * Scroll position handling when toggling cook mode on and off
 */
const scrollPositions = { beforeCookMode: 0, inCookMode: 0 };
let previousIsCookMode = false;

onBeforeUpdate(() => {
  if (previousIsCookMode == isCookMode.value) return;
  if (isCookMode.value) {
    scrollPositions.beforeCookMode = window.scrollY;
  }
  else {
    scrollPositions.inCookMode = window.scrollY;
  }
});
onUpdated(() => {
  if (previousIsCookMode == isCookMode.value) return;
  if (isCookMode.value) {
    window.scrollTo({ top: scrollPositions.inCookMode });
  }
  else {
    window.scrollTo({ top: scrollPositions.beforeCookMode });
  }
  previousIsCookMode = isCookMode.value;
});
</script>
