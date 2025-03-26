<template>
  <div v-if="value && value.length > 0">
    <div v-if="!isCookMode" class="d-flex justify-start" >
      <h2 class="mb-2 mt-1">{{ $t("recipe.ingredients") }}</h2>
      <!-- TODO: Change label to translation $t;
           Style label better with better placement -->
      <v-checkbox v-model="sortIngredientsByLabelName" class="my-auto ml-auto" color="secondary" label="Sort by label"/>
      <AppButtonCopy btn-class="ml-auto" :copy-text="ingredientCopyText" />
    </div>
    <div>
      <div v-for="(ingredient, index) in !isCookMode && sortIngredientsByLabelName ? sortedIngredientsByLabel : groupedIngredients" :key="'ingredient' + index">
        <template v-if="!isCookMode">
          <h3 v-if="showTitleEditor[index]" class="mt-2">{{ ingredient.title }}</h3>
          <v-divider v-if="showTitleEditor[index]"></v-divider>
        </template>
        <v-list-item dense @click.stop="toggleChecked(index)">
          <v-checkbox hide-details :value="checked[index]" class="pt-0 my-auto py-auto" color="secondary" />
          <v-list-item-content :key="ingredient.quantity">
            <RecipeIngredientListItem :ingredient="ingredient" :disable-amount="disableAmount" :scale="scale" />
          </v-list-item-content>
        </v-list-item>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
import { computed, defineComponent, reactive, toRefs } from "@nuxtjs/composition-api";
import RecipeIngredientListItem from "./RecipeIngredientListItem.vue";
import { parseIngredientText } from "~/composables/recipes";
import { RecipeIngredient } from "~/lib/api/types/recipe";
import { volumeUnitValues } from "~/composables/recipes/use-recipe-ingredients";

export default defineComponent({
  components: { RecipeIngredientListItem },
  props: {
    value: {
      type: Array as () => RecipeIngredient[],
      default: () => [],
    },
    disableAmount: {
      type: Boolean,
      default: false,
    },
    scale: {
      type: Number,
      default: 1,
    },
    isCookMode: {
      type: Boolean,
      default: false,
    }
  },
  setup(props) {
    function validateTitle(title?: string) {
      return !(title === undefined || title === "" || title === null);
    }

    const state = reactive({
      checked: props.value.map(() => false),
      showTitleEditor: computed(() => props.value.map((x) => validateTitle(x.title))),
      sortIngredientsByLabelName: true // TODO: Save default value as a household setting
    });

    const ingredientCopyText = computed(() => {
      const components: string[] = [];
      props.value.forEach((ingredient) => {
        if (ingredient.title) {
          if (components.length) {
            components.push("");
          }

          components.push(`[${ingredient.title}]`);
        }

        components.push(parseIngredientText(ingredient, props.disableAmount, props.scale, false));
      });

      return components.join("\n");
    });

    function toggleChecked(index: number) {
      // TODO Find a better way to do this - $set is not available, and
      // direct array modifications are not propagated for some reason
      state.checked.splice(index, 1, !state.checked[index]);
    }

    return {
      ...toRefs(state),
      ingredientCopyText,
      toggleChecked,
    };
  },
  computed: {
    groupedIngredients: function() {
      return this.groupIngredients(this.value);
    },
    sortedIngredientsByLabel: function() {
      // TODO: Add support for food.label.sortOrder in the database instead of sorting by name
      return this.groupIngredients([...this.value]).sort((a,b) =>
        {
          if (a.food?.label?.name < b.food?.label?.name)
            return -1;
          if (a.food?.label?.name > b.food?.label?.name)
            return 1;
          return 0;
        }
      )
    }
  },
  methods: {
    groupIngredients: function(allIngredients: RecipeIngredient[]) {
      const ingredientIds: string[] = [];
      for (const ingredient of allIngredients) {
        if (!ingredient.food?.id) continue;

        if (!ingredientIds.includes(ingredient.food?.id)) {
          ingredientIds.push(ingredient.food?.id);
        } else {
          const indexes: {[key:string]: number} = {};

          return allIngredients.reduce(function(res, ingredient) {
            const id = ingredient.food?.id;
            if (id) {
              if (!indexes[id]) {
                indexes[id] = res.length;
                res.push(JSON.parse(JSON.stringify(ingredient)) as RecipeIngredient);
              } else {
                const index = indexes[id];
                if (ingredient.unit?.name === res[index].unit?.name && res[index].quantity && !isNaN(res[index].quantity)) {
                  res[index].quantity += ingredient.quantity || 0;
                } else if (ingredient.unit && res[index].unit && volumeUnitValues[ingredient.unit.name] && volumeUnitValues[res[index].unit.name]
                  && res[index].quantity && !isNaN(res[index].quantity) && ingredient.quantity && !isNaN(ingredient.quantity)) {
                  res[index].quantity += ingredient.quantity * volumeUnitValues[ingredient.unit.name] / volumeUnitValues[res[index].unit.name];
                }
              }
            } else {
              res.push(JSON.parse(JSON.stringify(ingredient)) as RecipeIngredient);
            }
            return res;
          }, [] as RecipeIngredient[]);
        }
      }

      return allIngredients;
    }
  }
});
</script>

<style>
.dense-markdown p {
  margin: auto !important;
}
</style>
