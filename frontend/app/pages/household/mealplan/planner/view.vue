<template>
  <v-container class="mx-0 my-3 pa">
    <v-row>
      <v-col
        v-for="(day, index) in plan"
        :key="index"
        cols="12"
        sm="12"
        md="6"
        lg="4"
        xl="3"
        xxl="2"
        class="col-borders my-1 d-flex flex-column"
      >
        <v-card class="mb-2 border-left-primary rounded-sm px-2" :color="isSameDay(day.date, todaysDate) ? 'info' : undefined">
          <v-container class="px-0 d-flex align-center" height="56px">
            <v-row no-gutters style="width: 100%;">
              <v-col cols="10" class="d-flex align-center">
                <p class="pl-2 my-1" :class="{ 'text-primary': isToday(day.date) }">
                  {{ isSameDay(day.date, todaysDate) ? $t("general.today") : $d(day.date, "short") }}
                </p>
              </v-col>
              <v-col class="d-flex align-center justify-end ga-1" cols="2">
                <v-btn
                  v-if="day.recipes.length"
                  icon
                  size="x-small"
                  variant="text"
                  :title="$t('recipe.open-in-combined-view')"
                  @click="openCombinedRecipesPicker(day)"
                >
                  <v-icon>{{ $globals.icons.potSteam }}</v-icon>
                </v-btn>
                <GroupMealPlanDayContextMenu v-if="day.recipes.length" :recipes="day.recipes" />
              </v-col>
            </v-row>
          </v-container>
        </v-card>
        <div v-for="section in day.sections" :key="section.title">
          <div class="py-2 d-flex flex-column">
            <div class="primary" style="width: 50px; height: 2.5px" />
            <p class="text-overline my-0">
              {{ section.title }}
            </p>
          </div>

          <RecipeCardMobile
            v-for="mealplan in section.meals"
            :key="mealplan.id"
            :recipe-id="mealplan.recipe ? mealplan.recipe.id! : ''"
            class="mb-2"
            :rating="mealplan.recipe ? mealplan.recipe.rating! : 0"
            :slug="mealplan.recipe ? mealplan.recipe.slug! : mealplan.title!"
            :description="mealplan.recipe ? mealplan.recipe.description! : mealplan.text!"
            :name="mealplan.recipe ? mealplan.recipe.name! : mealplan.title!"
            :tags="mealplan.recipe ? mealplan.recipe.tags! : []"
          />
        </div>
      </v-col>
    </v-row>

    <BaseDialog
      v-model="showCombinedPicker"
      :title="$t('recipe.open-in-combined-view')"
      :icon="$globals.icons.potSteam"
      can-confirm
      @confirm="openSelectedCombinedRecipes"
    >
      <v-card-text>
        <p class="text-body-2 mb-3">
          {{ selectedDayLabel }}
        </p>

        <v-checkbox
          v-for="recipe in selectableCombinedRecipes"
          :key="recipe.slug"
          v-model="selectedCombinedRecipeSlugs"
          density="compact"
          hide-details
          :label="recipe.name"
          :value="recipe.slug"
        />
      </v-card-text>
    </BaseDialog>
  </v-container>
</template>

<script setup lang="ts">
import { isSameDay } from "date-fns";

import type { ReadPlanEntry } from "~/lib/api/types/meal-plan";
import GroupMealPlanDayContextMenu from "~/components/Domain/Household/GroupMealPlanDayContextMenu.vue";
import RecipeCardMobile from "~/components/Domain/Recipe/RecipeCardMobile.vue";
import type { RecipeSummary } from "~/lib/api/types/recipe";

export type MealsByDate = {
  date: Date;
  meals: ReadPlanEntry[];
};

const props = defineProps<{
  mealplans: MealsByDate[];
}>();

const router = useRouter();
const auth = useMealieAuth();
const groupSlug = computed(() => auth.user.value?.groupSlug);

type DaySection = {
  title: string;
  meals: ReadPlanEntry[];
};

type Days = {
  date: Date;
  sections: DaySection[];
  recipes: RecipeSummary[];
};

const i18n = useI18n();

const plan = computed<Days[]>(() => {
  return props.mealplans.reduce((acc, day) => {
    const out: Days = {
      date: day.date,
      sections: [
        { title: i18n.t("meal-plan.breakfast"), meals: [] },
        { title: i18n.t("meal-plan.lunch"), meals: [] },
        { title: i18n.t("meal-plan.dinner"), meals: [] },
        { title: i18n.t("meal-plan.side"), meals: [] },
        { title: i18n.t("meal-plan.snack"), meals: [] },
        { title: i18n.t("meal-plan.drink"), meals: [] },
        { title: i18n.t("meal-plan.dessert"), meals: [] },
        { title: i18n.t("meal-plan.recommended"), meals: [] },
      ],
      recipes: [],
    };

    for (const meal of day.meals) {
      if (meal.entryType === "breakfast") {
        out.sections[0].meals.push(meal);
      }
      else if (meal.entryType === "lunch") {
        out.sections[1].meals.push(meal);
      }
      else if (meal.entryType === "dinner") {
        out.sections[2].meals.push(meal);
      }
      else if (meal.entryType === "side") {
        out.sections[3].meals.push(meal);
      }
      else if (meal.entryType === "snack") {
        out.sections[4].meals.push(meal);
      }
      else if (meal.entryType === "drink") {
        out.sections[5].meals.push(meal);
      }
      else if (meal.entryType === "dessert") {
        out.sections[6].meals.push(meal);
      }
      else if (meal.entryType === "recommended") {
        out.sections[7].meals.push(meal);
      }

      if (meal.recipe) {
        out.recipes.push(meal.recipe);
      }
    }

    // Drop empty sections
    out.sections = out.sections.filter(section => section.meals.length > 0);

    acc.push(out);

    return acc;
  }, [] as Days[]);
});

const isToday = (date: Date) => {
  return isSameDay(date, new Date());
};

const todaysDate = computed(() => new Date());

const showCombinedPicker = ref(false);
const selectableCombinedRecipes = ref<RecipeSummary[]>([]);
const selectedCombinedRecipeSlugs = ref<string[]>([]);
const selectedDayLabel = ref("");

function toCombinedView(slugs: string[]) {
  if (!slugs.length || !groupSlug.value) {
    return;
  }

  const recipes = slugs.join(";");
  router.push(`/g/${groupSlug.value}/recipes/combined?recipes=${recipes}`);
}

function openCombinedRecipesPicker(day: Days) {
  const uniqueRecipes = day.recipes.filter((recipe, index, arr) => {
    if (!recipe.slug) {
      return false;
    }
    return arr.findIndex(item => item.slug === recipe.slug) === index;
  });

  if (uniqueRecipes.length === 1 && uniqueRecipes[0].slug) {
    toCombinedView([uniqueRecipes[0].slug]);
    return;
  }

  selectableCombinedRecipes.value = uniqueRecipes;
  selectedCombinedRecipeSlugs.value = uniqueRecipes.map(recipe => recipe.slug).filter(Boolean) as string[];
  selectedDayLabel.value = i18n.d(day.date, "short");
  showCombinedPicker.value = true;
}

function openSelectedCombinedRecipes() {
  toCombinedView(selectedCombinedRecipeSlugs.value);
  showCombinedPicker.value = false;
}
</script>
