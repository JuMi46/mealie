<template>
  <section @keyup.ctrl.z="undoMerge">
    <!-- Ingredient Link Editor -->
    <BaseDialog
      v-model="dialog"
      :title="$t('recipe.ingredient-linker')"
      :icon="$globals.icons.link"
      width="100%"
      max-width="600px"
      max-height="40%"
    >
      <v-card-text class="pt-4">
        <p>
          {{ activeText }}
        </p>
        <v-divider class="my-4" />
        <template v-if="Object.keys(groupedUnusedIngredients).length > 0">
          <h4 class="ml-1">
            {{ $t("recipe.unlinked") }}
          </h4>
          <template v-for="(ingredients, title) in groupedUnusedIngredients" :key="title">
            <h4 v-if="title" class="py-3 ml-1 pl-4">
              {{ title }}
            </h4>
            <v-checkbox-btn
              v-for="ing in ingredients"
              :key="ing.referenceId"
              v-model="activeRefs"
              :value="ing.referenceId"
              class="ml-4"
            >
              <template #label>
                <RecipeIngredientHtml :ingredient="ing" :scale="scale" />
              </template>
            </v-checkbox-btn>
          </template>
        </template>

        <template v-if="Object.keys(groupedUsedIngredients).length > 0">
          <h4 class="py-3 ml-1">
            {{ $t("recipe.linked-to-other-step") }}
          </h4>
          <template v-for="(ingredients, title) in groupedUsedIngredients" :key="title">
            <h4 v-if="title" class="py-3 ml-1 pl-4">
              {{ title }}
            </h4>
            <v-checkbox-btn
              v-for="ing in ingredients"
              :key="ing.referenceId"
              v-model="activeRefs"
              :value="ing.referenceId"
              class="ml-4"
            >
              <template #label>
                <RecipeIngredientHtml :ingredient="ing" :scale="scale" />
              </template>
            </v-checkbox-btn>
          </template>
        </template>
      </v-card-text>

      <v-divider />

      <template #card-actions>
        <BaseButton
          cancel
          @click="dialog = false"
        />
        <v-spacer />
        <div class="d-flex flex-wrap justify-end">
          <BaseButton
            class="my-1"
            color="info"
            @click="autoSetReferences"
          >
            <template #icon>
              {{ $globals.icons.robot }}
            </template>
            {{ $t("recipe.auto") }}
          </BaseButton>
          <BaseButton
            class="ml-2 my-1"
            save
            @click="setIngredientIds"
          />
          <BaseButton
            v-if="availableNextStep"
            class="ml-2 my-1"
            @click="saveAndOpenNextLinkIngredients"
          >
            <template #icon>
              {{ $globals.icons.forward }}
            </template>
            {{ $t("recipe.nextStep") }}
          </BaseButton>
        </div>
      </template>
    </BaseDialog>

    <div class="d-flex justify-space-between justify-start">
      <h2
        v-if="!isCookMode"
        class="mt-1 text-h5 font-weight-medium opacity-80"
      >
        {{ $t("recipe.instructions") }}
      </h2>
      <BaseButton
        v-if="!isEditForm && !isCookMode"
        minor
        cancel
        color="primary"
        @click="toggleCookMode()"
      >
        <template #icon>
          {{ $globals.icons.primary }}
        </template>
        {{ $t("recipe.cook-mode") }}
      </BaseButton>
    </div>
    <VueDraggable
      v-model="instructionList"
      :disabled="!isEditForm || props.disabled"
      handle=".handle"
      :delay="250"
      :delay-on-touch-only="true"
      v-bind="{
        animation: 200,
        group: 'recipe-instructions',
        ghostClass: 'ghost',
      }"
      @start="drag = true"
      @end="onDragEnd"
    >
      <TransitionGroup
        type="transition"
      >
        <div
          v-for="(step, index) in instructionList"
          :key="step.id!"
          class="list-group-item"
        >
          <v-sheet
            v-if="step.id && showTitleEditor[step.id]"
            color="primary"
            class="mt-6 mb-2 d-flex align-center"
            :class="isEditForm ? 'pa-2' : 'pa-3'"
            style="border-radius: 6px; cursor: pointer; width: 100%;"
            @click="toggleCollapseSection(index)"
          >
            <template v-if="isEditForm">
              <v-text-field
                v-model="step.title"
                class="pa-0"
                density="compact"
                variant="solo"
                flat
                :placeholder="$t('recipe.section-title')"
                bg-color="primary"
                hide-details
              />
            </template>
            <template v-else>
              <v-toolbar-title class="section-title-text">
                {{ step.title }}
              </v-toolbar-title>
            </template>
          </v-sheet>
          <v-hover v-slot="{ isHovering }">
            <v-card
              class="my-3"
              :class="[{ 'on-hover': isHovering }, { 'cursor-default': isEditForm }, isChecked(index)]"
              :elevation="isHovering ? 12 : 2"
              :ripple="false"
            >
              <v-card-title class="recipe-step-title pt-3" :class="!isChecked(index) ? 'pb-0' : 'pb-3'">
                <div class="d-flex align-center w-100">
                  <v-text-field
                    v-if="isEditForm"
                    v-model="step.summary"
                    class="headline"
                    hide-details
                    density="compact"
                    variant="solo"
                    flat
                    :placeholder="$t('recipe.step-index', { step: index + 1 })"
                  >
                    <template #prepend>
                      <v-icon size="26" class="handle">
                        {{ $globals.icons.arrowUpDown }}
                      </v-icon>
                    </template>
                  </v-text-field>
                  <div
                    v-else
                    class="summary-wrapper"
                    @click="toggleDisabled(index)"
                  >
                    <template v-if="step.summary">
                      <SafeMarkdown
                        class="pr-2"
                        :source="step.summary"
                      />
                    </template>
                    <template v-else>
                      <span>
                        {{ $t('recipe.step-index', { step: index + 1 }) }}
                      </span>
                    </template>
                  </div>
                  <template v-if="isEditForm">
                    <div class="ml-auto">
                      <BaseButtonGroup
                        :large="false"
                        :buttons="instructionButtons(index, step.id)"
                        @merge-above="mergeAbove(index - 1, index)"
                        @move-to-top="moveTo('top', index)"
                        @move-to-bottom="moveTo('bottom', index)"
                        @insert-above="insert(index)"
                        @insert-below="insert(index + 1)"
                        @split-below="splitBelow(index, step.id)"
                        @toggle-section="toggleShowTitle(step.id!)"
                        @link-ingredients="openDialog(index, step.text, step.ingredientReferences)"
                        @preview-step="togglePreviewState(index)"
                        @upload-image="openImageUpload(index)"
                        @delete="deleteInstruction(index, step.id)"
                      />
                    </div>
                  </template>
                  <v-fade-transition>
                    <v-icon
                      v-show="isChecked(index)"
                      size="24"
                      class="ml-auto"
                      color="success"
                    >
                      {{ $globals.icons.checkboxMarkedCircle }}
                    </v-icon>
                  </v-fade-transition>
                </div>
              </v-card-title>

              <v-progress-linear
                v-if="isEditForm && loadingStates[index]"
                :active="true"
                :indeterminate="true"
              />

              <!-- Content -->
              <DropZone @drop="(f) => handleImageDrop(index, f)">
                <v-card-text
                  v-if="isEditForm"
                  @click="$emit('click-instruction-field', `${index}.text`)"
                >
                  <MarkdownEditor
                    v-model="instructionList[index]['text']"
                    v-model:preview="previewStates[index]"
                    class="mb-2"
                    :display-preview="false"
                    :textarea="{
                      hint: $t('recipe.attach-images-hint'),
                      persistentHint: true,
                    }"
                    @selection-change="updateSelection(step.id, $event)"
                  />
                  <div
                    v-if="step.ingredientReferences && step.ingredientReferences.length"
                    class="linked-ingredients-editor"
                  >
                    <div
                      v-for="(linkRef, i) in step.ingredientReferences"
                      :key="linkRef.referenceId ?? i"
                      class="mb-1"
                    >
                      <RecipeIngredientHtml
                        v-if="linkRef.referenceId && ingredientLookup[linkRef.referenceId]"
                        :ingredient="ingredientLookup[linkRef.referenceId]"
                        :scale="scale"
                      />
                    </div>
                  </div>
                  <RecipeEditTimers v-model="step.timers" />
                </v-card-text>
              </DropZone>
              <v-expand-transition>
                <div
                  v-if="!isChecked(index) && !isEditForm"
                  class="m-0 p-0"
                >
                  <v-card-text class="markdown">
                    <v-row>
                      <v-col
                        v-if="isCookMode && step.ingredientReferences && step.ingredientReferences.length > 0"
                        cols="12"
                        sm="5"
                      >
                        <div class="ml-n4">
                          <RecipeIngredients
                            :value="recipe.recipeIngredient.filter((ing) => {
                              if (!step.ingredientReferences) return false
                              return step.ingredientReferences.map((ref) => ref.referenceId).includes(ing.referenceId || '')
                            })"
                            :scale="scale"
                            :is-cook-mode="isCookMode"
                          />
                        </div>
                      </v-col>
                      <v-divider
                        v-if="isCookMode && step.ingredientReferences && step.ingredientReferences.length > 0 && $vuetify.display.smAndUp"
                        vertical
                      />
                      <v-col>
                        <SafeMarkdown
                          class="markdown"
                          :source="parseTemperaturesInText(step.text)"
                        />
                      </v-col>
                    </v-row>
                    <div v-if="!isEditForm && step.timers && step.timers.length > 0">
                      <RecipePageInstructionsTimer
                        :timers="step.timers"
                        :is-cook-mode="isCookMode"
                        :step-title="parseStepTitle(step, index)"
                      />
                    </div>
                  </v-card-text>
                </div>
              </v-expand-transition>
            </v-card>
          </v-hover>
        </div>
      </TransitionGroup>
    </VueDraggable>
    <v-divider
      v-if="!isCookMode"
      class="mt-10 d-flex d-md-none"
    />
  </section>
</template>

<script setup lang="ts">
import { VueDraggable } from "vue-draggable-plus";
import { computed, nextTick, onMounted, ref, watch } from "vue";
import type { RecipeStep, IngredientReferences, RecipeIngredient, RecipeAsset, Recipe, RecipeTimer } from "~/lib/api/types/recipe";
import { uuid4, parseTemperaturesInText } from "~/composables/use-utils";
import { useUserApi, useStaticRoutes } from "~/composables/api";
import { usePageState } from "~/composables/recipe-page/shared-state";
import { useExtractIngredientReferences } from "~/composables/recipe-page/use-extract-ingredient-references";
import { useIngredientTextParser } from "~/composables/recipes/use-recipe-ingredients";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import DropZone from "~/components/global/DropZone.vue";
import RecipeIngredients from "~/components/Domain/Recipe/RecipeIngredients.vue";
import RecipeIngredientHtml from "~/components/Domain/Recipe/RecipeIngredientHtml.vue";
import RecipePageInstructionsTimer from "./RecipePageInstructionsTimer.vue";
import RecipeEditTimers from "./RecipeEditTimers.vue";

interface MergerHistory {
  target: number;
  source: number;
  targetText: string;
  sourceText: string;
}

interface InstructionSelectionState {
  selectedText: string;
  selectionStart: number;
  selectionEnd: number;
}

const instructionList = defineModel<RecipeStep[]>("modelValue", { required: true, default: () => [] });
const assets = defineModel<RecipeAsset[]>("assets", { required: true, default: () => [] });

const props = defineProps({
  recipe: {
    type: Object as () => NoUndefinedField<Recipe>,
    required: true,
  },
  scale: {
    type: Number,
    default: 1,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
});

const emit = defineEmits(["click-instruction-field", "update:assets"]);
const i18n = useI18n();
const { $globals } = useNuxtApp();

const { isCookMode, toggleCookMode, isEditForm } = usePageState(props.recipe.slug);
const { extractIngredientReferences } = useExtractIngredientReferences();
const { ingredientToParserString } = useIngredientTextParser();

const dialog = ref(false);
const disabledSteps = ref<number[]>([]);
const unusedIngredients = ref<RecipeIngredient[]>([]);
const usedIngredients = ref<RecipeIngredient[]>([]);

const showTitleEditor = ref<{ [key: string]: boolean }>({});
const instructionSelections = ref<Record<string, InstructionSelectionState | null>>({});

// ===============================================================
// UI State Helpers

function hasSectionTitle(title: string | undefined) {
  return !(title === null || title === "" || title === undefined);
}

watch(instructionList, (v) => {
  disabledSteps.value = [];

  v.forEach((element: RecipeStep) => {
    if (element.id !== undefined) {
      showTitleEditor.value[element.id!] = hasSectionTitle(element.title!);
    }
  });
}, { deep: true });

const showCookMode = ref(false);

onMounted(() => {
  instructionList.value.forEach((element: RecipeStep) => {
    if (element.id !== undefined) {
      showTitleEditor.value[element.id!] = hasSectionTitle(element.title!);
    }

    if (showCookMode.value === false && element.ingredientReferences && element.ingredientReferences.length > 0) {
      showCookMode.value = true;
    }

    showTitleEditor.value = { ...showTitleEditor.value };
  });

  if (assets.value === undefined) {
    emit("update:assets", []);
  }
});

function toggleDisabled(stepIndex: number) {
  if (isEditForm.value) {
    return;
  }
  if (disabledSteps.value.includes(stepIndex)) {
    const index = disabledSteps.value.indexOf(stepIndex);
    if (index !== -1) {
      disabledSteps.value.splice(index, 1);
    }
  }
  else {
    disabledSteps.value.push(stepIndex);
  }
}

function parseStepTitle(step: RecipeStep, stepIndex: number): string {
  return step.summary && step.summary.trim().length > 0 ? step.summary.trim() : i18n.t("recipe.step-index", { step: stepIndex + 1 });
}

function isChecked(stepIndex: number) {
  if (disabledSteps.value.includes(stepIndex) && !isEditForm.value) {
    return "disabled-card";
  }
}

function toggleShowTitle(id?: string) {
  if (!id) {
    return;
  }

  showTitleEditor.value[id] = !showTitleEditor.value[id];

  const temp = { ...showTitleEditor.value };
  showTitleEditor.value = temp;
}

function onDragEnd() {
  drag.value = false;
}

function updateSelection(stepId: string | null | undefined, selection: InstructionSelectionState | null) {
  if (!stepId) {
    return;
  }

  instructionSelections.value = {
    ...instructionSelections.value,
    [stepId]: selection,
  };
}

function hasSplitSelection(stepId: string | null | undefined) {
  if (!stepId) {
    return false;
  }

  const selection = instructionSelections.value[stepId];

  return !!selection && selection.selectionEnd > selection.selectionStart && selection.selectedText.trim().length > 0;
}

function instructionButtons(index: number, stepId: string | null | undefined) {
  return [
    {
      icon: $globals.icons.delete,
      text: i18n.t("general.delete"),
      event: "delete",
    },
    {
      icon: $globals.icons.dotsVertical,
      text: "",
      event: "open",
      children: [
        {
          text: i18n.t("recipe.toggle-section"),
          event: "toggle-section",
        },
        {
          text: i18n.t("recipe.link-ingredients"),
          event: "link-ingredients",
        },
        {
          text: i18n.t("recipe.upload-image"),
          event: "upload-image",
        },
        {
          icon: previewStates.value[index] ? $globals.icons.edit : $globals.icons.eye,
          text: previewStates.value[index] ? i18n.t("recipe.edit-markdown") : i18n.t("markdown-editor.preview-markdown-button-label"),
          event: "preview-step",
          divider: true,
        },
        {
          text: i18n.t("recipe.merge-above"),
          event: "merge-above",
        },
        {
          text: i18n.t("recipe.move-to-top"),
          event: "move-to-top",
        },
        {
          text: i18n.t("recipe.move-to-bottom"),
          event: "move-to-bottom",
        },
        {
          text: i18n.t("recipe.insert-above"),
          event: "insert-above",
        },
        {
          text: i18n.t("recipe.insert-below"),
          event: "insert-below",
        },
        ...(hasSplitSelection(stepId)
          ? [{
              text: i18n.t("recipe.split-below"),
              event: "split-below",
            }]
          : []),
      ],
    },
  ];
}

function clearSelection(stepId: string | null | undefined) {
  if (!stepId) {
    return;
  }

  instructionSelections.value = {
    ...instructionSelections.value,
    [stepId]: null,
  };
}

function deleteInstruction(index: number, stepId: string | null | undefined) {
  instructionList.value.splice(index, 1);
  clearSelection(stepId);
}

// ===============================================================
// Ingredient Linker
const activeRefs = ref<string[]>([]);
const activeIndex = ref(0);
const activeText = ref("");

function openDialog(idx: number, text: string, refs?: IngredientReferences[]) {
  if (!refs) {
    instructionList.value[idx].ingredientReferences = [];
    refs = instructionList.value[idx].ingredientReferences as IngredientReferences[];
  }
  activeIndex.value = idx;
  activeText.value = text;
  setUsedIngredients();
  dialog.value = true;
  activeRefs.value = refs.map(ref => ref.referenceId ?? "");
}

const availableNextStep = computed(() => activeIndex.value < instructionList.value.length - 1);

function setIngredientIds() {
  const instruction = instructionList.value[activeIndex.value];
  instruction.ingredientReferences = activeRefs.value.map((ref) => {
    return {
      referenceId: ref,
    };
  });

  // Update the visibility of the cook mode button
  showCookMode.value = false;
  instructionList.value.forEach((element) => {
    if (showCookMode.value === false && element.ingredientReferences && element.ingredientReferences.length > 0) {
      showCookMode.value = true;
    }
  });
  dialog.value = false;
}

function saveAndOpenNextLinkIngredients() {
  const currentStepIndex = activeIndex.value;

  if (!availableNextStep.value) {
    return; // no next step, the button calling this function should not be shown
  }

  setIngredientIds();
  const nextStep = instructionList.value[currentStepIndex + 1];
  // close dialog before opening to reset the scroll position
  nextTick(() => openDialog(currentStepIndex + 1, nextStep.text, nextStep.ingredientReferences));
}

function setUsedIngredients() {
  const usedRefs: { [key: string]: boolean } = {};

  instructionList.value.forEach((element, idx) => {
    if (idx === activeIndex.value) return;
    element.ingredientReferences?.forEach((ref) => {
      if (ref.referenceId) usedRefs[ref.referenceId] = true;
    });
  });

  usedIngredients.value = props.recipe.recipeIngredient.filter(ing => !!ing.referenceId && ing.referenceId in usedRefs);

  unusedIngredients.value = props.recipe.recipeIngredient.filter(ing => !!ing.referenceId && !(ing.referenceId in usedRefs));
}

watch(activeRefs, () => setUsedIngredients());

function autoSetReferences() {
  extractIngredientReferences(
    props.recipe.recipeIngredient,
    activeRefs.value,
    activeText.value,
  ).forEach(ingredient => activeRefs.value.push(ingredient));
}

const ingredientLookup = computed(() => {
  const results: { [key: string]: RecipeIngredient } = {};
  return props.recipe.recipeIngredient.reduce((prev, ing) => {
    if (ing.referenceId === undefined) {
      return prev;
    }
    prev[ing.referenceId] = ing;
    return prev;
  }, results);
});

// Map each ingredient's referenceId to its section title
const ingredientSectionTitles = computed(() => {
  const titleMap: { [key: string]: string } = {};
  let currentTitle = "";

  // Go through all ingredients in order
  props.recipe.recipeIngredient.forEach((ingredient) => {
    if (ingredient.referenceId === undefined) {
      return;
    }

    // If this ingredient has a title, update the current title
    if (ingredient.title) {
      currentTitle = ingredient.title;
    }

    // Assign the current title to this ingredient
    titleMap[ingredient.referenceId] = currentTitle;
  });

  return titleMap;
});

const groupedUnusedIngredients = computed((): Record<string, RecipeIngredient[]> => {
  const groups: Record<string, RecipeIngredient[]> = {};

  // Group ingredients by section title
  unusedIngredients.value.forEach((ingredient) => {
    if (ingredient.referenceId === undefined) {
      return;
    }

    // Use the section title from the mapping, or fallback to the ingredient's own title
    const title = ingredientSectionTitles.value[ingredient.referenceId] || ingredient.title || "";
    (groups[title] ||= []).push(ingredient);
  });

  return groups;
});

const groupedUsedIngredients = computed((): Record<string, RecipeIngredient[]> => {
  const groups: Record<string, RecipeIngredient[]> = {};
  usedIngredients.value.forEach((ingredient) => {
    if (ingredient.referenceId === undefined) {
      return;
    }

    // Use the section title from the mapping, or fallback to the ingredient's own title
    const title = ingredientSectionTitles.value[ingredient.referenceId] || ingredient.title || "";
    (groups[title] ||= []).push(ingredient);
  });

  return groups;
});

// ===============================================================
// Instruction Merger
const mergeHistory = ref<MergerHistory[]>([]);

function mergeAbove(target: number, source: number) {
  if (target < 0) {
    return;
  }

  mergeHistory.value.push({
    target,
    source,
    targetText: instructionList.value[target].text,
    sourceText: instructionList.value[source].text,
  });

  instructionList.value[target].text += " " + instructionList.value[source].text;
  instructionList.value.splice(source, 1);
}

function undoMerge(event: KeyboardEvent) {
  if (event.ctrlKey && event.code === "KeyZ") {
    if (!(mergeHistory.value?.length > 0)) {
      return;
    }

    const lastMerge = mergeHistory.value.pop();
    if (!lastMerge) {
      return;
    }

    instructionList.value[lastMerge.target].text = lastMerge.targetText;
    instructionList.value.splice(lastMerge.source, 0, {
      id: uuid4(),
      title: "",
      text: lastMerge.sourceText,
      ingredientReferences: [],
    });
  }
}

function moveTo(dest: string, source: number) {
  if (dest === "top") {
    instructionList.value.unshift(instructionList.value.splice(source, 1)[0]);
  }
  else {
    instructionList.value.push(instructionList.value.splice(source, 1)[0]);
  }
}

function insert(dest: number) {
  instructionList.value.splice(dest, 0, { id: uuid4(), text: "", title: "", ingredientReferences: [] });
}

function extractNumberSignals(text: string): Set<number> {
  const matches = text.match(/\b\d+\b/g) ?? [];
  return new Set(matches.map(value => Number.parseInt(value, 10)));
}

function extractNumericRanges(text: string): Array<[number, number]> {
  const normalized = text
    .toLowerCase()
    .replace(/[\u2013\u2014]/g, "-");
  const rangeRegex = /\b(\d+)\s*(?:-|to)\s*(\d+)\b/g;

  const ranges: Array<[number, number]> = [];
  let match = rangeRegex.exec(normalized);
  while (match) {
    const startValue = match[1];
    const endValue = match[2];

    if (startValue === undefined || endValue === undefined) {
      match = rangeRegex.exec(normalized);
      continue;
    }

    const start = Number.parseInt(startValue, 10);
    const end = Number.parseInt(endValue, 10);
    ranges.push(start <= end ? [start, end] : [end, start]);
    match = rangeRegex.exec(normalized);
  }

  return ranges;
}

function timerDurationCandidates(duration: number): number[] {
  if (!Number.isFinite(duration) || duration < 0) {
    return [];
  }

  const candidates = new Set<number>([Math.round(duration)]);

  if (duration % 60 === 0) {
    candidates.add(Math.round(duration / 60));
  }

  return [...candidates];
}

function timerMatchesMovedText(timer: RecipeTimer, movedText: string): boolean {
  const numbers = extractNumberSignals(movedText);
  const ranges = extractNumericRanges(movedText);
  const candidates = timerDurationCandidates(timer.duration);

  return candidates.some((candidate) => {
    if (numbers.has(candidate)) {
      return true;
    }

    return ranges.some(([start, end]) => candidate >= start && candidate <= end);
  });
}

function ingredientMatchTokens(text: string): Set<string> {
  const blackListedText = new Set(["and", "the", "for", "with", "without"]);
  const normalized = text
    .toLowerCase()
    .replace(/[\u2013\u2014]/g, " ")
    .replace(/[^\p{L}\p{N}\s'-]/gu, " ");

  return new Set(
    normalized
      .split(/\s+/)
      .map(token => token.replace(/^['-]+|['-]+$/g, ""))
      .filter(token => token.length > 2)
      .filter(token => !blackListedText.has(token))
      .filter(token => !/\d/.test(token)),
  );
}

function ingredientMatchesMovedText(ingredient: RecipeIngredient, movedTextTokens: Set<string>): boolean {
  const matchSourceText = ingredient.food?.name || ingredientToParserString(ingredient);
  const ingredientTokens = ingredientMatchTokens(matchSourceText);

  return [...ingredientTokens].some(token => movedTextTokens.has(token));
}

function splitBelow(index: number, stepId: string | null | undefined) {
  if (!stepId) {
    return;
  }

  const selection = instructionSelections.value[stepId];
  const sourceInstruction = instructionList.value[index];

  if (!selection || !sourceInstruction || selection.selectedText.trim().length === 0) {
    return;
  }

  const selectedText = sourceInstruction.text.slice(selection.selectionStart, selection.selectionEnd);

  if (selectedText !== selection.selectedText) {
    return;
  }

  sourceInstruction.text = sourceInstruction.text.slice(0, selection.selectionStart) + sourceInstruction.text.slice(selection.selectionEnd);
  insert(index + 1);
  const insertedInstruction = instructionList.value[index + 1];

  if (!insertedInstruction) {
    return;
  }

  insertedInstruction.text = selectedText;

  const sourceRefs = sourceInstruction.ingredientReferences ?? [];
  const movedTextTokens = ingredientMatchTokens(selectedText);
  const movedRefs = sourceRefs.filter((ref) => {
    if (!ref.referenceId) {
      return false;
    }

    const ingredient = ingredientLookup.value[ref.referenceId];
    if (!ingredient) {
      return false;
    }

    return ingredientMatchesMovedText(ingredient, movedTextTokens);
  });
  const movedRefIds = new Set(movedRefs.map(ref => ref.referenceId));
  insertedInstruction.ingredientReferences = movedRefs;
  sourceInstruction.ingredientReferences = sourceRefs.filter(ref => !ref.referenceId || !movedRefIds.has(ref.referenceId));

  const sourceTimers = sourceInstruction.timers ?? [];
  const movedTimers = sourceTimers.filter(timer => timerMatchesMovedText(timer, selectedText));
  const movedTimerSet = new Set(movedTimers);
  insertedInstruction.timers = movedTimers;
  sourceInstruction.timers = sourceTimers.filter(timer => !movedTimerSet.has(timer));

  instructionSelections.value = {
    ...instructionSelections.value,
    [stepId]: null,
  };
}

const previewStates = ref<boolean[]>([]);

function togglePreviewState(index: number) {
  const temp = [...previewStates.value];
  temp[index] = !temp[index];
  previewStates.value = temp;
}

function toggleCollapseSection(index: number) {
  const sectionSteps: number[] = [];

  for (let i = index; i < instructionList.value.length; i++) {
    if (!(i === index) && hasSectionTitle(instructionList.value[i].title!)) {
      break;
    }
    else {
      sectionSteps.push(i);
    }
  }

  const allCollapsed = sectionSteps.every(idx => disabledSteps.value.includes(idx));

  if (allCollapsed) {
    disabledSteps.value = disabledSteps.value.filter(idx => !sectionSteps.includes(idx));
  }
  else {
    disabledSteps.value = [...disabledSteps.value, ...sectionSteps];
  }
}

const drag = ref(false);

// ===============================================================
// Image Uploader
const api = useUserApi();
const { recipeAssetPath } = useStaticRoutes();

const loadingStates = ref<{ [key: number]: boolean }>({});

async function handleImageDrop(index: number, files: File[]) {
  if (!files) {
    return;
  }

  // Check if the file is an image
  const file = files[0];
  if (!file || !file.type.startsWith("image/")) {
    return;
  }

  loadingStates.value[index] = true;

  const { data } = await api.recipes.createAsset(props.recipe.slug, {
    name: file.name,
    icon: "mdi-file-image",
    file,
    extension: file.name.split(".").pop() || "",
  });

  loadingStates.value[index] = false;

  if (!data) {
    return; // TODO: Handle error
  }

  emit("update:assets", [...assets.value, data]);
  const assetUrl = recipeAssetPath(props.recipe.id, data.fileName as string);
  const text = `<img src="${assetUrl}" height="100%" width="100%"/>`;
  instructionList.value[index].text += text;
}

function openImageUpload(index: number) {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = "image/*";
  input.onchange = async () => {
    if (input.files) {
      await handleImageDrop(index, Array.from(input.files));
      input.remove();
    }
  };
  input.click();
}

defineExpose({
  openDialog,
});
</script>

<style lang="css" scoped>
.v-card--link:before {
  background: none;
}

/** Select all li under .markdown class */
.markdown :deep(ul > li) {
  display: list-item;
  list-style-type: disc !important;
}

/** Select all li under .markdown class */
.markdown :deep(ol > li) {
  display: list-item;
}

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

.blur {
  filter: blur(2px);
}

.upload-overlay {
  display: flex;
  justify-content: center;
  align-items: center;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1;
}

.v-text-field :deep(input) {
  font-size: 1.5rem;
}

.v-card-text {
  font-size: 1rem;
}

.recipe-step-title {
  /* Multiline display */
  white-space: normal;
  line-height: 1.25;
  word-break: break-word;
}

.summary-wrapper {
  flex: 1 1 auto;
  min-width: 0;
  /* wrapping in flex container */
  white-space: normal;
  overflow-wrap: anywhere;
  cursor: pointer;
}
</style>
