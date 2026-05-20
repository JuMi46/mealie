<template>
  <div>
    <BaseDialog
      v-model="discardDialog"
      :title="$t('general.discard-changes')"
      color="warning"
      :icon="$globals.icons.alertCircle"
      can-confirm
      @confirm="confirmDiscard"
      @cancel="cancelDiscard"
    >
      <v-card-text>
        {{ $t("general.discard-changes-description") }}
      </v-card-text>
    </BaseDialog>
    <BaseDialog
      v-model="parseWithAIDialog"
      :title="$t('recipe.parse-with-ai')"
      :icon="$globals.icons.robot"
      color="accent"
      can-confirm
      @confirm="applyAIParsedRecipe"
    >
      <template #custom-card-action>
        <BaseButton v-if="aiLowConfidenceCount > 0" color="warning" @click="reviewAIIngredients">
          <template #icon>
            {{ $globals.icons.search }}
          </template>
          {{ $t("recipe.review-ai-ingredients", { count: aiLowConfidenceCount }) }}
        </BaseButton>
      </template>
      <v-card-text>
        {{ $t("recipe.apply-ai-parsed-recipe-confirmation") }}
      </v-card-text>
      <v-card-text v-if="aiParsedRecipe" class="pt-0">
        <div class="text-body-2 mb-3">
          {{ $t("recipe.ai-parse-summary", { ingredients: aiParsedRecipe.recipeIngredient.length, steps: aiParsedRecipe.recipeInstructions.length }) }}
        </div>
        <v-list density="compact" class="py-0">
          <v-list-item v-if="recipe.recipeIngredient.length !== aiParsedRecipe.recipeIngredient.length">
            <template #prepend>
              <v-icon size="small">
                {{ $globals.icons.foods }}
              </v-icon>
            </template>
            <v-list-item-title>
              {{ $t("recipe.ingredients") }}: {{ recipe.recipeIngredient.length }} -> {{ aiParsedRecipe.recipeIngredient.length }}
            </v-list-item-title>
          </v-list-item>
          <v-list-item v-if="recipe.recipeInstructions.length !== aiParsedRecipe.recipeInstructions.length">
            <template #prepend>
              <v-icon size="small">
                {{ $globals.icons.text }}
              </v-icon>
            </template>
            <v-list-item-title>
              {{ $t("recipe.instructions") }}: {{ recipe.recipeInstructions.length }} -> {{ aiParsedRecipe.recipeInstructions.length }}
            </v-list-item-title>
          </v-list-item>
          <v-list-item v-if="aiOrgUrlChanged">
            <template #prepend>
              <v-icon size="small">
                {{ $globals.icons.link }}
              </v-icon>
            </template>
            <v-list-item-title>
              {{ $t("recipe.original-url") }}: {{ $t("general.yes") }}
            </v-list-item-title>
          </v-list-item>
        </v-list>
        <v-alert v-if="aiLowConfidenceCount > 0" type="warning" variant="tonal" density="compact" class="mt-3">
          {{ $t("recipe.ai-parse-low-confidence-warning", { count: aiLowConfidenceCount }) }}
        </v-alert>
        <template v-if="aiIngredientPreview.length > 0 || aiInstructionPreview.length > 0">
          <v-divider class="my-3" />
          <div class="text-subtitle-2 mb-1">
            {{ $t("recipe.preview") }}
          </div>
          <template v-if="aiIngredientPreview.length > 0">
            <div class="text-body-2 mb-1">
              {{ $t("recipe.ingredients") }}
            </div>
            <v-chip
              v-for="(ing, index) in aiIngredientPreview"
              :key="`ai-ingredient-${index}`"
              size="small"
              class="mr-1 mb-1"
              color="accent"
              variant="tonal"
            >
              {{ ing }}
            </v-chip>
          </template>
          <template v-if="aiInstructionPreview.length > 0">
            <div class="text-body-2 mt-2 mb-1">
              {{ $t("recipe.instructions") }}
            </div>
            <v-chip
              v-for="(step, index) in aiInstructionPreview"
              :key="`ai-step-${index}`"
              size="small"
              class="mr-1 mb-1"
              color="info"
              variant="tonal"
            >
              {{ step }}
            </v-chip>
          </template>
        </template>
      </v-card-text>
    </BaseDialog>
    <RecipePageParseDialog
      :model-value="isParsing"
      :ingredients="recipe.recipeIngredient"
      :preloaded-ingredients="aiParsedIngredientsForReview.length ? aiParsedIngredientsForReview : undefined"
      :width="$vuetify.display.smAndDown ? '100%' : '80%'"
      @update:model-value="onParseDialogClose"
      @save="saveParsedIngredients"
      @review-ai="onAIReviewComplete"
    />
    <v-container v-show="!isCookMode" key="recipe-page" class="px-0" :class="{ 'pa-0': $vuetify.display.smAndDown }">
      <v-card flat class="d-print-none" :class="{ 'opacity-50': parseWithAILoading }">
        <!-- Loading Overlay -->
        <v-overlay v-if="parseWithAILoading" contained absolute class="d-flex align-center justify-center">
          <div class="text-center">
            <v-progress-circular indeterminate color="accent" size="64" class="mb-4" />
            <p class="text-body-1 font-weight-medium">
              {{ $t('recipe.parse-with-ai') }}
            </p>
            <p class="text-caption opacity-75">
              {{ $t('general.loading') }}
            </p>
          </div>
        </v-overlay>
        <RecipePageHeader
          :recipe="recipe"
          :recipe-scale="scale"
          :landscape="landscape"
          :parse-with-ai-loading="parseWithAILoading"
          :hide-parse-actions="isImportParseAIMode"
          @save="saveRecipe"
          @delete="deleteRecipe"
          @close="closeEditor"
          @link-ingredients="linkIngredients"
          @parse-with-ai="parseRecipeWithAI"
        />
        <RecipeJsonEditor
          v-if="isEditJSON"
          v-model="recipe"
          class="mt-10"
          mode="text"
          :main-menu-bar="false"
        />
        <v-card-text
          v-else
          :class="{ 'pointer-events-none': parseWithAILoading }"
        >
          <!--
            This is where most of the main content is rendered. Some components include state for both Edit and View modes
            which is why some have explicit v-if statements and others use the composition API to determine and manage
            the shared state internally.

            The global recipe object is shared down the tree of components and _is_ mutated by child components. This is
            some-what of a hack of the system and goes against the principles of Vue, but it _does_ seem to work and streamline
            a significant amount of prop management. When we move to Vue 3 and have access to some of the newer API's the plan to update this
            data management and mutation system we're using.
          -->
          <div>
            <RecipePageInfoEditor v-if="isEditMode" v-model="recipe" />
          </div>
          <div>
            <RecipePageIngredientEditor v-if="isEditForm" v-model="recipe" :disabled="parseWithAILoading" />
          </div>
          <div>
            <RecipePageScale v-model="scale" :recipe="recipe" />
          </div>

          <!--
            This section contains the 2 column layout for the recipe steps and other content.
          -->
          <v-row>
            <!--
              The left column is conditionally rendered based on cook mode.
            -->
            <v-col
              v-if="!isCookMode || isEditForm"
              cols="12"
              sm="12"
              md="4"
              :class="$vuetify.display.mdAndUp ? 'border-e-thin' : null"
            >
              <RecipePageIngredientToolsView v-if="!isEditForm" :recipe="recipe" :scale="scale" class="pr-2" />
              <RecipePageOrganizers
                v-if="$vuetify.display.mdAndUp"
                v-model="recipe"
                class="pr-2"
                @item-selected="chipClicked"
              />
            </v-col>
            <!--
              the right column is always rendered, but it's layout width is determined by where the left column is
              rendered.
            -->
            <v-col cols="12" sm="12" :md="8 + (isCookMode ? 1 : 0) * 4">
              <RecipePageInstructions
                ref="recipePageInstructions"
                v-model="recipe.recipeInstructions"
                v-model:assets="recipe.assets"
                :recipe="recipe"
                :scale="scale"
                :disabled="parseWithAILoading"
              />
              <div v-if="isEditForm" class="d-flex">
                <BaseButton class="my-2 mr-1" :disabled="isParsingTimers" @click="parseInstructionsWithAI">
                  <template #icon>
                    {{ $globals.icons.robot }}
                  </template>
                  {{ $t("recipe.parse-timers-and-temperatures") }}
                </BaseButton>
                <RecipeDialogBulkAdd class="ml-auto my-2 mr-1" @bulk-data="addStep" />
                <BaseButton class="my-2" @click="addStep()">
                  {{ $t("general.add") }}
                </BaseButton>
              </div>
              <div v-if="!$vuetify.display.mdAndUp">
                <RecipePageOrganizers v-model="recipe" />
              </div>
              <RecipeNotes v-model="recipe.notes" :edit="isEditForm" />
            </v-col>
          </v-row>
          <div>
            <RecipePageEditorToolbar v-if="isEditForm" v-model="recipe" />
          </div>
          <RecipePageFooter v-model="recipe" />
        </v-card-text>
      </v-card>
      <WakelockSwitch />
      <RecipePageComments
        v-if="!recipe.settings?.disableComments && !isEditForm && !isCookMode"
        v-model="recipe"
        class="px-1 my-4 d-print-none"
      />
      <RecipePrintContainer :recipe="recipe" :scale="scale" />
    </v-container>
    <!-- Cook mode displayes two columns with ingredients and instructions side by side, each being scrolled individually, allowing to view both at the same time -->
    <!-- The calc is to account for the navabar height (48px) -->
    <v-sheet
      v-show="isCookMode && !hasLinkedIngredients"
      key="cookmode"
      :height="$vuetify.display.smAndUp ? 'calc(100vh - 48px)' : 'auto'"
      class-name="overflow-hidden"
    >
      <!-- the calc is to account for the toolbar a more dynamic solution could be needed  -->
      <v-row style="height: 100%" no-gutters class="overflow-hidden">
        <v-col cols="12" sm="5" class="overflow-y-auto pl-4 pr-3 py-2" style="height: 100%">
          <div class="d-flex align-center">
            <RecipePageScale v-model="scale" :recipe="recipe" />
          </div>
          <RecipePageIngredientToolsView
            v-if="!isEditForm"
            :recipe="recipe"
            :scale="scale"
            :is-cook-mode="isCookMode"
          />
          <v-divider />
        </v-col>
        <v-col
          class="overflow-y-auto"
          :class="$vuetify.display.smAndDown ? 'py-2' : 'py-6'"
          style="height: 100%"
          cols="12"
          sm="7"
        >
          <h2 class="text-h5 px-4 font-weight-medium opacity-80">
            {{ $t('recipe.instructions') }}
          </h2>
          <RecipePageInstructions
            v-model="recipe.recipeInstructions"
            v-model:assets="recipe.assets"
            class="overflow-y-hidden px-4"
            :recipe="recipe"
            :scale="scale"
          />
        </v-col>
      </v-row>
    </v-sheet>
    <v-sheet v-show="isCookMode && hasLinkedIngredients">
      <div class="mt-2 px-2 px-md-4">
        <RecipePageScale v-model="scale" :recipe="recipe" />
      </div>
      <RecipePageInstructions
        v-model="recipe.recipeInstructions"
        v-model:assets="recipe.assets"
        class="overflow-y-hidden mt-n5 px-2 px-md-4"
        :recipe="recipe"
        :scale="scale"
      />

      <div v-if="notLinkedIngredients.length > 0" class="px-2 px-md-4 pb-4">
        <v-divider />
        <v-card flat>
          <v-card-title>{{ $t("recipe.not-linked-ingredients") }}</v-card-title>
          <RecipeIngredients
            :value="notLinkedIngredients"
            :scale="scale"
            :is-cook-mode="isCookMode"
          />
        </v-card>
      </div>
    </v-sheet>
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
import { invoke, until } from "@vueuse/core";
import type { RouteLocationNormalized } from "vue-router";
import RecipeIngredients from "../RecipeIngredients.vue";
import RecipePageEditorToolbar from "./RecipePageParts/RecipePageEditorToolbar.vue";
import RecipePageFooter from "./RecipePageParts/RecipePageFooter.vue";
import RecipePageHeader from "./RecipePageParts/RecipePageHeader.vue";
import RecipePageIngredientEditor from "./RecipePageParts/RecipePageIngredientEditor.vue";
import RecipePageIngredientToolsView from "./RecipePageParts/RecipePageIngredientToolsView.vue";
import RecipePageInstructions from "./RecipePageParts/RecipePageInstructions.vue";
import RecipePageOrganizers from "./RecipePageParts/RecipePageOrganizers.vue";
import RecipePageParseDialog from "./RecipePageParts/RecipePageParseDialog.vue";
import RecipePageScale from "./RecipePageParts/RecipePageScale.vue";
import RecipePageInfoEditor from "./RecipePageParts/RecipePageInfoEditor.vue";
import RecipePageComments from "./RecipePageParts/RecipePageComments.vue";
import RecipePrintContainer from "~/components/Domain/Recipe/RecipePrintContainer.vue";
import {
  clearPageState,
  PageMode,
  usePageState,
} from "~/composables/recipe-page/shared-state";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import type { ParsedIngredient, Recipe, RecipeCategory, RecipeIngredient, RecipeTag, RecipeTool } from "~/lib/api/types/recipe";
import type { ParseInstructionsWithAIStepOut, ParseWithAIOut } from "~/lib/api/user/recipes/recipe";
import { useRouteQuery } from "~/composables/use-router";
import { useUserApi } from "~/composables/api";
import { uuid4, deepCopy } from "~/composables/use-utils";
import RecipeDialogBulkAdd from "~/components/Domain/Recipe/RecipeDialogBulkAdd.vue";
import RecipeNotes from "~/components/Domain/Recipe/RecipeNotes.vue";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import { useNavigationWarning } from "~/composables/use-navigation-warning";
import { alert } from "~/composables/use-toast";

const recipe = defineModel<NoUndefinedField<Recipe>>({ required: true });

const display = useDisplay();
const auth = useMealieAuth();
const route = useRoute();
const i18n = useI18n();
const { isOwnGroup } = useLoggedInState();

const groupSlug = computed(() => (route.params.groupSlug as string) || auth.user?.value?.groupSlug || "");

const router = useRouter();
const api = useUserApi();
const { setMode, isEditForm, isEditJSON, isCookMode, isEditMode, isParsing, toggleCookMode, toggleIsParsing }
  = usePageState(recipe.value.slug);
const { deactivateNavigationWarning } = useNavigationWarning();
const notLinkedIngredients = computed(() => {
  return recipe.value.recipeIngredient.filter((ingredient) => {
    return !recipe.value.recipeInstructions.some(step =>
      step.ingredientReferences?.map(ref => ref.referenceId).includes(ingredient.referenceId),
    );
  });
});

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

/** =============================================================
 * Recipe Snapshot on Mount
 * this is used to determine if the recipe has been changed since the last save
 * and prompts the user to save if they have unsaved changes.
 */
const originalRecipe = ref<Recipe | null>(null);
const discardDialog = ref(false);
const pendingRoute = ref<RouteLocationNormalized | null>(null);
const parseWithAIDialog = ref(false);
const parseWithAILoading = ref(false);
const aiParsedRecipe = ref<ParseWithAIOut | null>(null);
const aiParsedIngredientsForReview = ref<ParsedIngredient[]>([]);

const aiOrgUrlChanged = computed(() => {
  if (!aiParsedRecipe.value) {
    return false;
  }

  return (aiParsedRecipe.value.orgURL || "") !== (recipe.value.orgURL || "");
});

function previewText(text: string | null | undefined, max = 80) {
  const value = (text || "").trim();
  if (!value) {
    return "";
  }

  return value.length > max ? `${value.slice(0, max)}...` : value;
}

const aiIngredientPreview = computed(() => {
  if (!aiParsedRecipe.value) {
    return [];
  }

  return aiParsedRecipe.value.recipeIngredient
    .map(ingredient => previewText(ingredient.note))
    .filter(Boolean)
    .slice(0, 4);
});

const aiInstructionPreview = computed(() => {
  if (!aiParsedRecipe.value) {
    return [];
  }

  return aiParsedRecipe.value.recipeInstructions
    .map(step => previewText(step.text))
    .filter(Boolean)
    .slice(0, 4);
});

const aiLowConfidenceCount = computed(() => {
  const confidenceThreshold = 0.85;
  return aiParsedIngredientsForReview.value.filter((ing) => {
    if (ing.confidence && ing.confidence.average < confidenceThreshold) {
      return true;
    }
    if (ing.ingredient.food && !("id" in ing.ingredient.food && ing.ingredient.food.id)) {
      return true;
    }
    if (ing.ingredient.unit && !("id" in ing.ingredient.unit && ing.ingredient.unit.id)) {
      return true;
    }
    return false;
  }).length;
});

invoke(async () => {
  await until(recipe.value).not.toBeNull();
  originalRecipe.value = deepCopy(recipe.value);
});

function hasUnsavedChanges(): boolean {
  if (originalRecipe.value === null) {
    return false;
  }
  return JSON.stringify(recipe.value) !== JSON.stringify(originalRecipe.value);
}

function restoreOriginalRecipe() {
  if (originalRecipe.value) {
    recipe.value = deepCopy(originalRecipe.value) as NoUndefinedField<Recipe>;
  }
}

function closeEditor() {
  if (hasUnsavedChanges()) {
    pendingRoute.value = null;
    discardDialog.value = true;
  }
  else {
    setMode(PageMode.VIEW);
  }
}

function confirmDiscard() {
  restoreOriginalRecipe();
  discardDialog.value = false;

  if (pendingRoute.value) {
    const destination = pendingRoute.value;
    pendingRoute.value = null;
    router.push(destination);
  }
  else {
    setMode(PageMode.VIEW);
  }
}

function cancelDiscard() {
  discardDialog.value = false;
  pendingRoute.value = null;
}

onBeforeRouteLeave((to) => {
  if (isEditMode.value && hasUnsavedChanges()) {
    pendingRoute.value = to;
    discardDialog.value = true;
    return false;
  }
});

onUnmounted(() => {
  deactivateNavigationWarning();
  toggleCookMode();
  clearPageState(recipe.value.slug || "");
});
const hasLinkedIngredients = computed(() => {
  return recipe.value.recipeInstructions.some(
    step => step.ingredientReferences && step.ingredientReferences.length > 0,
  );
});
/** =============================================================
 * Set State onMounted
 */

type BooleanString = "true" | "false" | "";

const paramsEdit = useRouteQuery<BooleanString>("edit", "");
const paramsParse = useRouteQuery<BooleanString>("parse", "");
const paramsParseAI = useRouteQuery<BooleanString>("parse_ai", "");
const paramsCookMode = useRouteQuery<BooleanString>("isCookMode", "");
const paramsServings = useRouteQuery<BooleanString>("servings", "");
const hasAutoParsedWithAI = ref(false);
const importParseAIMode = ref(paramsParseAI.value === "true");
const isImportParseAIMode = computed(() => importParseAIMode.value);

onMounted(() => {
  if (paramsEdit.value === "true" && isOwnGroup.value) {
    setMode(PageMode.EDIT);
  }

  if (paramsCookMode.value === "true") {
    setMode(PageMode.COOK);
  }

  if (paramsParse.value === "true" && isOwnGroup.value) {
    toggleIsParsing(true);
  }

  if (paramsParseAI.value === "true" && isOwnGroup.value && recipe.value.slug && !hasAutoParsedWithAI.value) {
    setMode(PageMode.EDIT);
    hasAutoParsedWithAI.value = true;
    importParseAIMode.value = true;
    void parseRecipeWithAI();
  }

  if (paramsServings.value) {
    scale.value = paramsServings.value;
  }
});

// When set, the isEditMode watcher skips its URL cleanup because saveRecipe
// is navigating to a new slug that naturally omits ?edit=true.
const isNavigatingAfterRename = ref(false);

watch(isEditMode, (newVal) => {
  if (!newVal) {
    if (isNavigatingAfterRename.value) {
      isNavigatingAfterRename.value = false;
      return;
    }
    paramsEdit.value = undefined;
  }
});

watch(isParsing, () => {
  if (!isParsing.value) {
    paramsParse.value = undefined;
  }
});

watch(
  () => [paramsParseAI.value, isOwnGroup.value, recipe.value.slug] as const,
  ([parseAI, ownGroup, slug]) => {
    if (parseAI === "true" && ownGroup && slug && !hasAutoParsedWithAI.value) {
      setMode(PageMode.EDIT);
      hasAutoParsedWithAI.value = true;
      importParseAIMode.value = true;
      void parseRecipeWithAI();
    }
  },
  { immediate: true },
);

/** =============================================================
 * Recipe Save Delete
 */

async function saveRecipe(stayInEditMode: boolean = false) {
  const { data, error } = await api.recipes.updateOne(recipe.value.slug, recipe.value);
  if (!error && !stayInEditMode) {
    if (data?.slug && data.slug !== route.params.slug) {
      isNavigatingAfterRename.value = true;
    }
    setMode(PageMode.VIEW);
  }
  if (data?.slug) {
    recipe.value = data as NoUndefinedField<Recipe>;
    originalRecipe.value = deepCopy(recipe.value);
    if (data.slug !== route.params.slug) {
      router.replace(`/g/${groupSlug.value}/r/` + data.slug);
    }
  }
}

async function saveParsedIngredients(ingredients: NoUndefinedField<RecipeIngredient[]>, linkIngredientsAfter: boolean = false) {
  recipe.value.recipeIngredient = ingredients;

  // If these ingredients came from an AI parse, also apply the AI instructions and metadata.
  if (aiParsedRecipe.value) {
    recipe.value.recipeInstructions = aiParsedRecipe.value.recipeInstructions;
    recipe.value.orgURL = aiParsedRecipe.value.orgURL ?? recipe.value.orgURL;
    aiParsedRecipe.value = null;
    aiParsedIngredientsForReview.value = [];
  }

  await saveRecipe(true);
  toggleIsParsing(false);
  if (linkIngredientsAfter) {
    linkIngredients();
  }
}

function onParseDialogClose(open: boolean) {
  if (!open && aiParsedIngredientsForReview.value.length) {
    aiParsedRecipe.value = null;
    aiParsedIngredientsForReview.value = [];
  }
  toggleIsParsing(open);
}

function onAIReviewComplete(ingredients: ParsedIngredient[]) {
  // The dialog already boosted confidence for resolved items, so just store the result directly.
  aiParsedIngredientsForReview.value = ingredients;
  toggleIsParsing(false);
  parseWithAIDialog.value = true;
}

async function parseRecipeWithAI() {
  if (!recipe.value.slug || parseWithAILoading.value) {
    return;
  }

  if (paramsParseAI.value === "true") {
    paramsParseAI.value = undefined;
  }

  parseWithAILoading.value = true;

  const payload = {
    recipeIngredient: recipe.value.recipeIngredient.map(ingredient => ({
      display: ingredient.display || null,
      referenceId: ingredient.referenceId || null,
    })),
    recipeInstructions: recipe.value.recipeInstructions.map(step => ({
      id: step.id,
      text: step.text,
      ingredientReferences: step.ingredientReferences || [],
    })),
    orgURL: recipe.value.orgURL || null,
  };

  const { data, error } = await api.recipes.parseWithAI(recipe.value.slug, payload);
  parseWithAILoading.value = false;

  if (error || !data) {
    alert.error(i18n.t("events.something-went-wrong"));
    return;
  }

  aiParsedRecipe.value = data;

  aiParsedIngredientsForReview.value = data.recipeIngredient.map((ing, i) => ({
    input: ing.display ?? recipe.value.recipeIngredient[i]?.display ?? "",
    confidence: ing.confidence ?? undefined,
    ingredient: {
      referenceId: ing.referenceId ?? undefined,
      display: ing.display ?? undefined,
      quantity: ing.quantity ?? undefined,
      unit: ing.unit ?? undefined,
      food: ing.food ?? undefined,
      note: ing.note ?? undefined,
      title: recipe.value.recipeIngredient[i]?.title ?? "",
    },
  }));

  parseWithAIDialog.value = true;
}

function applyAIParsedRecipe() {
  if (!aiParsedRecipe.value) {
    return;
  }

  // Confirm path keeps existing behavior but strips unresolved food/unit objects to avoid save-time errors.
  recipe.value.recipeIngredient = aiParsedIngredientsForReview.value.map(ing => ({
    ...ing.ingredient,
    unit: ing.ingredient.unit && "id" in ing.ingredient.unit && ing.ingredient.unit.id
      ? ing.ingredient.unit
      : undefined,
    food: ing.ingredient.food && "id" in ing.ingredient.food && ing.ingredient.food.id
      ? ing.ingredient.food
      : undefined,
  })) as NoUndefinedField<RecipeIngredient[]>;
  recipe.value.recipeInstructions = aiParsedRecipe.value.recipeInstructions;
  recipe.value.orgURL = aiParsedRecipe.value.orgURL ?? recipe.value.orgURL;
  aiParsedRecipe.value = null;
  aiParsedIngredientsForReview.value = [];
  parseWithAIDialog.value = false;
}

function reviewAIIngredients() {
  parseWithAIDialog.value = false;
  toggleIsParsing(true);
}

async function deleteRecipe() {
  const { data } = await api.recipes.deleteOne(recipe.value.slug);
  if (data?.slug) {
    router.push(`/g/${groupSlug.value}`);
  }
}

/** =============================================================
 * View Preferences
 */
const landscape = computed(() => {
  const preferLandscape = recipe.value.settings?.landscapeView;
  const smallScreen = !display.smAndUp.value;

  if (preferLandscape) {
    return true;
  }
  else if (smallScreen) {
    return true;
  }

  return false;
});

/** =============================================================
 * Bulk Step Editor
 * TODO: Move to RecipePageInstructions component
 */

function addStep(steps: Array<string> | null = null) {
  if (!recipe.value.recipeInstructions) {
    return;
  }

  if (steps) {
    const cleanedSteps = steps.map((step) => {
      return { id: uuid4(), text: step, title: "", summary: "", ingredientReferences: [], timers: [] };
    });

    recipe.value.recipeInstructions.push(...cleanedSteps);
  }
  else {
    recipe.value.recipeInstructions.push({
      id: uuid4(),
      text: "",
      title: "",
      summary: "",
      ingredientReferences: [],
      timers: [],
    });
  }
}

const isParsingTimers = ref(false);

async function parseInstructionsWithAI() {
  if (!recipe.value.slug || !recipe.value.recipeInstructions?.length || isParsingTimers.value) {
    return;
  }

  const payload = {
    primaryUnitSystem: recipe.value.primaryUnitSystem ?? null,
    orgURL: recipe.value.orgURL || null,
    instructions: recipe.value.recipeInstructions.map(step => ({
      id: step.id || null,
      text: step.text?.trim() ?? "",
      timers: [],
    })),
  };

  isParsingTimers.value = true;
  const { data, error } = await api.recipes.parseInstructionsWithAI(recipe.value.slug, payload);
  isParsingTimers.value = false;

  if (error || !data?.instructions?.length || !recipe.value.recipeInstructions) {
    alert.error(i18n.t("events.something-went-wrong"));
    return;
  }

  data.instructions.forEach((parsedStep: ParseInstructionsWithAIStepOut, index: number) => {
    const targetStep = parsedStep.id
      ? recipe.value.recipeInstructions.find(step => step.id === parsedStep.id)
      : recipe.value.recipeInstructions[index];

    if (!targetStep) {
      return;
    }

    targetStep.text = parsedStep.text;
    targetStep.timers = (parsedStep.timers ?? []).map(timer => ({
      id: timer.id || uuid4(),
      duration: timer.duration,
      text: timer.text || "",
      timersActive: [],
    })) as typeof targetStep.timers;
  });
}

/** =============================================================
 * RecipeChip Clicked
 */

function chipClicked(item: RecipeTag | RecipeCategory | RecipeTool, itemType: string) {
  if (!item.id) {
    return;
  }
  router.push(`/g/${groupSlug.value}?${itemType}=${item.id}`);
}

const recipePageInstructions: Ref<any> = ref(null);
function linkIngredients() {
  if (recipe.value.recipeInstructions && recipe.value.recipeInstructions[0]?.text) {
    recipePageInstructions.value.openDialog(0, recipe.value.recipeInstructions[0].text, recipe.value.recipeInstructions[0].ingredientReferences);
  }
}

const scale = ref(1);

// expose to template
// (all variables used in template are top-level in <script setup>)
</script>

<style lang="css">
.flip-list-move {
  transition: transform 0.5s;
}

.no-move {
  transition: transform 0s;
}

.ghost {
  opacity: 0.5;
}

.list-group {
  min-height: 38px;
}

.list-group-item i {
  cursor: pointer;
}
</style>
