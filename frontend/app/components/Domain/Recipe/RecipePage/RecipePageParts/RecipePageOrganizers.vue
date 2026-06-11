<template>
  <div>
    <!-- Recipe Categories -->
    <v-card
      v-if="recipe.recipeCategory.length > 0 || isEditForm"
      :class="{ 'mt-10': !isEditForm }"
    >
      <v-card-title class="py-2">
        {{ $t("recipe.categories") }}
      </v-card-title>
      <v-divider class="mx-2" />
      <v-card-text>
        <RecipeOrganizerSelector
          v-if="isEditForm"
          v-model="recipe.recipeCategory"
          :return-object="true"
          :show-add="true"
          selector-type="categories"
        />
        <RecipeChips
          v-else
          :items="recipe.recipeCategory"
          v-bind="$attrs"
        />
      </v-card-text>
    </v-card>

    <!-- Recipe Tags -->
    <v-card
      v-if="recipe.tags.length > 0 || isEditForm"
      class="mt-4"
    >
      <v-card-title class="py-2">
        {{ $t("tag.tags") }}
      </v-card-title>
      <v-divider class="mx-2" />
      <v-card-text>
        <RecipeOrganizerSelector
          v-if="isEditForm"
          v-model="recipe.tags"
          :return-object="true"
          :show-add="true"
          selector-type="tags"
        />
        <RecipeChips
          v-else
          :items="recipe.tags"
          url-prefix="tags"
          v-bind="$attrs"
        />
      </v-card-text>
    </v-card>

    <!-- Recommended Side Dishes -->
    <v-card
      v-if="(recipe.recommendedSideDishes && recipe.recommendedSideDishes.length > 0) || isEditForm"
      class="mt-4"
    >
      <v-card-title class="py-2">
        {{ $t("recipe.recommended-side-dishes") }}
      </v-card-title>
      <v-divider class="mx-2" />
      <v-card-text>
        <v-autocomplete
          v-if="isEditForm"
          v-model="recipe.recommendedSideDishes"
          v-model:search="recommendedSearch"
          :items="recommendedCandidates"
          item-title="name"
          item-value="slug"
          return-object
          chips
          closable-chips
          multiple
          :label="$t('recipe.recommended-side-dishes')"
          variant="outlined"
          :prepend-inner-icon="$globals.icons.potSteam"
        />
        <div v-else class="d-flex flex-wrap ga-2">
          <NuxtLink
            v-for="recommended in recipe.recommendedSideDishes"
            :key="recommended.slug"
            :to="`/g/${groupSlug}/r/${recommended.slug}`"
          >
            <v-chip color="accent" variant="flat" label>
              {{ recommended.name }}
            </v-chip>
          </NuxtLink>
        </div>
      </v-card-text>
    </v-card>

    <!-- Recipe Tools Edit -->
    <v-card
      v-if="isEditForm"
      class="mt-2"
    >
      <v-card-title class="py-2">
        {{ $t('tool.required-tools') }}
      </v-card-title>
      <v-divider class="mx-2" />
      <v-card-text>
        <RecipeOrganizerSelector
          v-model="recipe.tools"
          selector-type="tools"
          v-bind="$attrs"
        />
      </v-card-text>
    </v-card>

    <RecipeNutrition
      v-if="recipe.settings.showNutrition"
      v-model="recipe.nutrition"
      class="mt-4"
      :edit="isEditForm"
    />
    <RecipeAssets
      v-if="recipe.settings.showAssets"
      v-model="recipe.assets"
      :edit="isEditForm"
      :slug="recipe.slug"
      :recipe-id="recipe.id"
    />
  </div>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";
import { usePageState } from "~/composables/recipe-page/shared-state";
import type { NoUndefinedField } from "~/lib/api/types/non-generated";
import type { Recipe, RecipeRecommendation } from "~/lib/api/types/recipe";
import RecipeOrganizerSelector from "@/components/Domain/Recipe/RecipeOrganizerSelector.vue";
import RecipeNutrition from "~/components/Domain/Recipe/RecipeNutrition.vue";
import RecipeChips from "@/components/Domain/Recipe/RecipeChips.vue";
import RecipeAssets from "@/components/Domain/Recipe/RecipeAssets.vue";

const recipe = defineModel<NoUndefinedField<Recipe>>({ required: true });
const { isEditForm } = usePageState(recipe.value.slug);
const auth = useMealieAuth();
const route = useRoute();
const groupSlug = computed(() => (route.params.groupSlug as string) || auth.user?.value?.groupSlug || "");
const api = useUserApi();

const allRecipes = ref<Recipe[]>([]);
const recommendedSearch = ref("");

const recommendedCandidates = computed<RecipeRecommendation[]>(() => {
  const currentSlug = recipe.value.slug;
  return allRecipes.value
    .filter(candidate => !!candidate.slug && candidate.slug !== currentSlug)
    .map(candidate => ({
      id: candidate.id,
      name: candidate.name,
      slug: candidate.slug,
      image: candidate.image,
      recipeCategory: candidate.recipeCategory,
    }));
});

onMounted(async () => {
  if (!recipe.value.recommendedSideDishes) {
    recipe.value.recommendedSideDishes = [];
  }

  const { data } = await api.recipes.search({
    perPage: -1,
    orderBy: "name",
    orderDirection: "asc",
  });

  allRecipes.value = data.items || [];
});
</script>
