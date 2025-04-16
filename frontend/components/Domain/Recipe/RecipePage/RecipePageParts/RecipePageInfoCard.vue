<template>
  <div>
    <div class="d-flex justify-end flex-wrap align-stretch">
      <RecipePageInfoCardImage v-if="landscape" :recipe="recipe" />
      <v-card
        :width="landscape ? '100%' : '50%'"
        flat
        class="d-flex flex-column justify-center align-center"
      >
        <v-card-text>
          <v-card-title class="headline pa-0 flex-column align-center">
            {{ recipe.name }}
            <RecipeRating :key="recipe.slug" :value="recipe.rating" :recipe-id="recipe.id" :slug="recipe.slug" />
          </v-card-title>
          <v-divider class="my-2" />
          <SafeMarkdown :source="recipe.description" />
          <p v-if="ovenTemperature.length !== 0">Oven temperature: {{ ovenTemperature }}</p>
          <router-link v-for="link in ingredientLinks" :key="link.text" :to="link.path" target="_blank"> {{
            link.text }} </router-link>
          <v-divider v-if="recipe.description" />
          <v-container class="d-flex flex-row flex-wrap justify-center">
            <div class="mx-6">
              <v-row no-gutters>
                <v-col v-if="recipe.recipeYieldQuantity || recipe.recipeYield" cols="12" class="d-flex flex-wrap justify-center">
                  <RecipeYield
                    :yield-quantity="recipe.recipeYieldQuantity"
                    :yield="recipe.recipeYield"
                    :scale="recipeScale"
                    class="mb-4"
                  />
                </v-col>
              </v-row>
              <v-row no-gutters>
                <v-col cols="12" class="d-flex flex-wrap justify-center">
                  <RecipeLastMade
                    v-if="isOwnGroup"
                    :recipe="recipe"
                    class="mb-4"
                  />
                </v-col>
              </v-row>
            </div>
            <div class="mx-6">
              <RecipeTimeCard
                container-class="d-flex flex-wrap justify-center"
                :prep-time="recipe.prepTime"
                :total-time="recipe.totalTime"
                :perform-time="recipe.performTime"
                class="mb-4"
              />
            </div>
          </v-container>
        </v-card-text>
      </v-card>
      <RecipePageInfoCardImage v-if="!landscape" :recipe="recipe" max-width="50%" class="my-auto" />
    </div>
  </div>
</template>

<script lang="ts">
import { computed, defineComponent, onMounted, reactive, toRefs, useContext, useRoute } from "@nuxtjs/composition-api";
import { useLoggedInState } from "~/composables/use-logged-in-state";
import RecipeRating from "~/components/Domain/Recipe/RecipeRating.vue";
import RecipeLastMade from "~/components/Domain/Recipe/RecipeLastMade.vue";
import RecipeTimeCard from "~/components/Domain/Recipe/RecipeTimeCard.vue";
import RecipeYield from "~/components/Domain/Recipe/RecipeYield.vue";
import RecipePageInfoCardImage from "~/components/Domain/Recipe/RecipePage/RecipePageParts/RecipePageInfoCardImage.vue";
import { Recipe } from "~/lib/api/types/recipe";
import { NoUndefinedField } from "~/lib/api/types/non-generated";
export default defineComponent({
  components: {
    RecipeRating,
    RecipeLastMade,
    RecipeTimeCard,
    RecipeYield,
    RecipePageInfoCardImage,
  },
  props: {
    recipe: {
      type: Object as () => NoUndefinedField<Recipe>,
      required: true,
    },
    recipeScale: {
      type: Number,
      default: 1,
    },
    landscape: {
      type: Boolean,
      required: true,
    },
  },
  setup(props) {
    const { $vuetify } = useContext();
    const route = useRoute();
    const useMobile = computed(() => $vuetify.breakpoint.smAndDown);

    const { isOwnGroup } = useLoggedInState();

    const state = reactive({
      ingredientLinks: [] as {
        text: string;
        path: string;
      }[],
      ovenTemperature: ""
    });

    onMounted(() => {
      const basePath = route.value.fullPath.substring(0, route.value.fullPath.lastIndexOf("/")+1);
      for (const ingredient of props.recipe.recipeIngredient) {
        if (ingredient.food?.description.includes("@")) {
          state.ingredientLinks.push({
            text: ingredient.food.name,
            path: basePath + ingredient.food.name.toLowerCase().replaceAll(" ", "-")
          });
        }
      }

      for (const step of props.recipe.recipeInstructions) {
        const tempMatch = /\d+°(F|C)/.exec(step.text);
        if (tempMatch) {
          const temp = Number(tempMatch[0].split("°")[0]);
          const tempUnit = tempMatch[0].split("°")[1];
          if (tempUnit === "C") {
            const f = Math.ceil((temp * 9 / 5) + 32);
            state.ovenTemperature = `${f}°F / ${temp}°C`
          } else {
            const c = Math.ceil((temp - 32) * 5 / 9);
            state.ovenTemperature = `${temp}°F / ${c}°C`
          }
          break;
        }
      }
    });

    return {
      isOwnGroup,
      useMobile,
      ...toRefs(state),
    };
  }
});
</script>
