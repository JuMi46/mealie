import { useRecipeCreatePreferences } from "~/composables/use-users/preferences";
import type { MaybeRefOrGetter } from "vue";
import { toValue } from "vue";

export interface UseNewRecipeOptionsProps {
  enableImportKeywords?: MaybeRefOrGetter<boolean>;
  enableImportCategories?: MaybeRefOrGetter<boolean>;
  enableStayInEditMode?: MaybeRefOrGetter<boolean>;
  enableParseRecipe?: MaybeRefOrGetter<boolean>;
  enableParseRecipeWithAI?: MaybeRefOrGetter<boolean>;
}

export function useNewRecipeOptions(props: UseNewRecipeOptionsProps = {}) {
  const router = useRouter();
  const recipeCreatePreferences = useRecipeCreatePreferences();

  function isEnabled(flag: MaybeRefOrGetter<boolean> | undefined, defaultValue = true) {
    const value = flag === undefined ? undefined : toValue(flag);
    return value ?? defaultValue;
  }

  const importKeywordsAsTags = computed({
    get() {
      if (!isEnabled(props.enableImportKeywords)) return false;
      return recipeCreatePreferences.value.importKeywordsAsTags;
    },
    set(v: boolean) {
      if (!isEnabled(props.enableImportKeywords)) return;
      recipeCreatePreferences.value.importKeywordsAsTags = v;
    },
  });

  const importCategories = computed({
    get() {
      if (!isEnabled(props.enableImportCategories)) return false;
      return recipeCreatePreferences.value.importCategories;
    },
    set(v: boolean) {
      if (!isEnabled(props.enableImportCategories)) return;
      recipeCreatePreferences.value.importCategories = v;
    },
  });

  const stayInEditMode = computed({
    get() {
      if (!isEnabled(props.enableStayInEditMode)) return false;
      return recipeCreatePreferences.value.stayInEditMode;
    },
    set(v: boolean) {
      if (!isEnabled(props.enableStayInEditMode)) return;
      recipeCreatePreferences.value.stayInEditMode = v;
    },
  });

  const parseRecipe = computed({
    get() {
      if (!isEnabled(props.enableParseRecipe)) return false;
      return recipeCreatePreferences.value.parseRecipe;
    },
    set(v: boolean) {
      if (!isEnabled(props.enableParseRecipe)) return;
      recipeCreatePreferences.value.parseRecipe = v;
    },
  });

  const parseRecipeWithAI = computed({
    get() {
      if (!isEnabled(props.enableParseRecipeWithAI)) return false;
      return recipeCreatePreferences.value.parseRecipeWithAI;
    },
    set(v: boolean) {
      if (!isEnabled(props.enableParseRecipeWithAI)) return;
      recipeCreatePreferences.value.parseRecipeWithAI = v;
    },
  });

  function navigateToRecipe(recipeSlug: string, groupSlug: string, createPagePath: string) {
    const editParam = isEnabled(props.enableStayInEditMode) ? stayInEditMode.value : false;
    const parseParam = isEnabled(props.enableParseRecipe) ? parseRecipe.value : false;
    const parseAIParam = isEnabled(props.enableParseRecipeWithAI) ? parseRecipeWithAI.value : false;

    const queryParams = new URLSearchParams();
    if (editParam || parseAIParam) {
      queryParams.set("edit", "true");
    }
    if (parseParam) {
      queryParams.set("parse", "true");
    }
    if (parseAIParam) {
      queryParams.set("parse_ai", "true");
    }

    const queryString = queryParams.toString();
    const recipeUrl = `/g/${groupSlug}/r/${recipeSlug}${queryString ? `?${queryString}` : ""}`;

    // Replace current entry to prevent re-import on back navigation
    router.replace(createPagePath).then(() => router.push(recipeUrl));
  }

  return {
    // Computed properties for the checkboxes
    importKeywordsAsTags,
    importCategories,
    stayInEditMode,
    parseRecipe,
    parseRecipeWithAI,

    // Helper functions
    navigateToRecipe,

    // Props for conditional rendering
    enableImportKeywords: isEnabled(props.enableImportKeywords),
    enableImportCategories: isEnabled(props.enableImportCategories),
    enableStayInEditMode: isEnabled(props.enableStayInEditMode),
    enableParseRecipe: isEnabled(props.enableParseRecipe),
    enableParseRecipeWithAI: isEnabled(props.enableParseRecipeWithAI),
  };
}
