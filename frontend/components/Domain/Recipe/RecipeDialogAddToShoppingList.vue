<template>
  <div v-if="dialog">
    <BaseDialog v-if="shoppingListDialog && ready" v-model="dialog" :title="$t('recipe.add-to-list')" :icon="$globals.icons.cartCheck">
    <v-container v-if="!shoppingListChoices.length">
      <BasePageTitle>
        <template #title>{{ $t('shopping-list.no-shopping-lists-found') }}</template>
      </BasePageTitle>
    </v-container>
      <v-card-text>
        <v-card
          v-for="list in shoppingListChoices"
          :key="list.id"
          hover
          class="my-2 left-border"
          @click="openShoppingListIngredientDialog(list)"
        >
          <v-card-title class="py-2">
            {{ list.name }}
          </v-card-title>
        </v-card>
      </v-card-text>
      <template #card-actions>
        <v-btn
          text
          color="grey"
          @click="dialog = false"
        >
          {{ $t("general.cancel") }}
        </v-btn>
        <div class="d-flex justify-end" style="width: 100%;">
          <v-checkbox v-model="preferences.viewAllLists" hide-details :label="$tc('general.show-all')" class="my-auto mr-4" @click="setShowAllToggled()" />
        </div>
      </template>
    </BaseDialog>
    <BaseDialog
      v-if="shoppingListIngredientDialog"
      v-model="dialog"
      :title="selectedShoppingList ? selectedShoppingList.name : $t('recipe.add-to-list')"
      :icon="$globals.icons.cartCheck"
      width="70%"
      :submit-text="$tc('recipe.add-to-list')"
      @submit="addRecipesToList()"
    >
      <div style="max-height: 70vh;  overflow-y: auto">
        <v-card
          v-for="(recipeSection, recipeSectionIndex) in recipeIngredientSections" :key="recipeSection.recipeId + recipeSectionIndex"
          elevation="0"
          height="fit-content"
          width="100%"
        >
          <v-divider v-if="recipeSectionIndex > 0" class="mt-3" />
          <v-card-title
            v-if="recipeIngredientSections.length > 1"
            class="justify-center text-h5"
            width="100%"
          >
            <v-container style="width: 100%;">
              <v-row no-gutters class="ma-0 pa-0">
                <v-col cols="12" align-self="center" class="text-center">
                  {{ recipeSection.recipeName }}
                </v-col>
              </v-row>
              <v-row v-if="recipeSection.recipeScale > 1" no-gutters class="ma-0 pa-0">
                <!-- TODO: make this editable in the dialog and visible on single-recipe lists -->
                <v-col cols="12" align-self="center" class="text-center">
                  ({{ $tc("recipe.quantity") }}: {{ recipeSection.recipeScale }})
                </v-col>
              </v-row>
            </v-container>
          </v-card-title>
          <div>
            <div
              v-for="(ingredientSection, ingredientSectionIndex) in recipeSection.ingredientSections"
              :key="recipeSection.recipeId + recipeSectionIndex + ingredientSectionIndex"
            >
              <v-card-title v-if="ingredientSection.sectionName" class="ingredient-title mt-2 pb-0 text-h6">
                {{ ingredientSection.sectionName }}
              </v-card-title>
              <div
                :class="$vuetify.breakpoint.smAndDown ? '' : 'ingredient-grid'"
                :style="$vuetify.breakpoint.smAndDown ? '' : { gridTemplateRows: `repeat(${Math.ceil(ingredientSection.ingredients.length / 2)}, min-content)` }"
              >
                <v-list-item
                  v-for="(ingredientData, i) in ingredientSection.ingredients"
                  :key="recipeSection.recipeId + recipeSectionIndex + ingredientSectionIndex + i"
                  dense
                  @click="recipeIngredientSections[recipeSectionIndex]
                    .ingredientSections[ingredientSectionIndex]
                    .ingredients[i].checked = !recipeIngredientSections[recipeSectionIndex]
                    .ingredientSections[ingredientSectionIndex]
                    .ingredients[i]
                    .checked"
                >
                  <v-checkbox
                    hide-details
                    :input-value="ingredientData.checked"
                    class="pt-0 my-auto py-auto"
                    color="secondary"
                  />
                  <v-list-item-content :key="ingredientData.ingredient.quantity">
                    <RecipeIngredientListItem
                      :ingredient="ingredientData.ingredient"
                      :disable-amount="ingredientData.disableAmount"
                      :scale="recipeSection.recipeScale" />
                  </v-list-item-content>
                </v-list-item>
              </div>
            </div>
          </div>
        </v-card>
        <v-card v-for="(listSection, recipeSectionIndex) in recipeGroupedIngredients" :key="recipeSectionIndex" elevation="0" height="fit-content" width="100%">
          <v-divider v-if="recipeSectionIndex > 0" class="mt-3" />
          <v-card-title v-if="listSection.section" class="justify-center text-h5" width="100%">
            {{ listSection.section }}
          </v-card-title>
          <div>
            <div v-for="(label, labelIndex) in listSection.labels" :key="recipeSectionIndex + label.label">
              <v-card-title v-if="label.label" class="ingredient-title mt-2 pb-0 text-h6">
                {{ label.label.split("_")[1] }}
              </v-card-title>
              <div
                :class="$vuetify.breakpoint.smAndDown ? '' : 'ingredient-grid'"
                :style="$vuetify.breakpoint.smAndDown ? '' : { gridTemplateRows: `repeat(${Math.ceil(label.ingredients.length / 2)}, min-content)` }"
              >
                <v-list-item
                  v-for="(ingredientData, ingredientIndex) in label.ingredients"
                  :key="recipeSectionIndex + label.label + ingredientIndex"
                  dense
                  @click="recipeGroupedIngredients[recipeSectionIndex]
                    .labels[labelIndex]
                    .ingredients[ingredientIndex].checked =
                    !recipeGroupedIngredients[recipeSectionIndex]
                    .labels[labelIndex]
                    .ingredients[ingredientIndex].checked"
                >
                  <v-checkbox
                    hide-details
                    :input-value="ingredientData.checked"
                    class="pt-0 my-auto py-auto"
                    color="secondary"
                  />
                  <v-list-item-content :key="ingredientData.ingredientSum.quantity">
                    <RecipeIngredientListItem
                      :ingredient="ingredientData.ingredientSum"
                      :disable-amount="false"
                      :scale="1" />
                  </v-list-item-content>
                </v-list-item>
              </div>
            </div>
          </div>
        </v-card>

      </div>
      <div class="d-flex justify-end mb-4 mt-2">
        <BaseButtonGroup
          :buttons="[
            {
              icon: $globals.icons.checkboxBlankOutline,
              text: $tc('shopping-list.uncheck-all-items'),
              event: 'uncheck',
            },
            {
              icon: $globals.icons.checkboxOutline,
              text: $tc('shopping-list.check-all-items'),
              event: 'check',
            },
          ]"
          @uncheck="bulkCheckIngredients(false)"
          @check="bulkCheckIngredients(true)"
        />
      </div>
    </BaseDialog>
  </div>
</template>

<script lang="ts">
import { computed, defineComponent, reactive, ref, useContext, watchEffect } from "@nuxtjs/composition-api";
import { toRefs } from "@vueuse/core";
import RecipeIngredientListItem from "./RecipeIngredientListItem.vue";
import { useUserApi } from "~/composables/api";
import { alert } from "~/composables/use-toast";
import { useShoppingListPreferences } from "~/composables/use-users/preferences";
import { IngredientUnit, RecipeIngredient, ShoppingListAddRecipeParamsBulk, ShoppingListSummary } from "~/lib/api/types/household";
import { Recipe } from "~/lib/api/types/recipe";
import { convertToGram, convertToMilliliter, massUnitValues, UnitNames, volumeUnitValues } from "~/composables/recipes/use-recipe-ingredients";
import { useUnitStore } from "~/composables/store";


export interface RecipeWithScale extends Recipe {
  scale: number;
}

export interface ShoppingListIngredient {
  checked: boolean;
  ingredient: RecipeIngredient;
  disableAmount: boolean;
}

export interface ShoppingListIngredientSection {
  sectionName: string;
  ingredients: ShoppingListIngredient[];
}

export interface ShoppingListRecipeIngredientSection {
  recipeId: string;
  recipeName: string;
  recipeScale: number;
  ingredientSections: ShoppingListIngredientSection[];
}

export interface ShoppingListRecipe {
  id: string;
  scale: number;
  disableAmount: boolean;
}

export interface ShoppingListGroupedIngredientItem {
  checked: boolean;
  ingredient: RecipeIngredient;
  recipe: ShoppingListRecipe;
}

export interface ShoppingListGroupedIngredient {
  checked: boolean;
  ingredientSum: RecipeIngredient;
  ingredientItems: ShoppingListGroupedIngredientItem[];
}

export interface ShoppingListGroupedIngredientLabel {
  label: string;
  ingredients: ShoppingListGroupedIngredient[];
}

export interface ShoppingListGroupedIngredientLabels {
  section: string;
  labels: ShoppingListGroupedIngredientLabel[];
}

export default defineComponent({
  components: {
    RecipeIngredientListItem,
  },
  props: {
    value: {
      type: Boolean,
      default: false,
    },
    recipes: {
      type: Array as () => RecipeWithScale[],
      default: undefined,
    },
    shoppingLists: {
      type: Array as () => ShoppingListSummary[],
      default: () => [],
    },
    groupIngredients: {
      type: Boolean,
      default: false,
    },
    listForPeriod: {
      type: String,
      default: "",
    }
  },
  setup(props, context) {
    const { $auth, i18n } = useContext();
    const api = useUserApi();
    const preferences = useShoppingListPreferences();
    const ready = ref(false);

    // v-model support
    const dialog = computed({
      get: () => {
        return props.value;
      },
      set: (val) => {
        context.emit("input", val);
        initState();
      },
    });

    const state = reactive({
      shoppingListDialog: true,
      shoppingListIngredientDialog: false,
      shoppingListShowAllToggled: false,
    });

    const userHousehold = computed(() => {
      return $auth.user?.householdSlug || "";
    });

    const shoppingListChoices = computed(() => {
      return props.shoppingLists.filter((list) => preferences.value.viewAllLists || list.userId === $auth.user?.id);
    });

    const recipeIngredientSections = ref<ShoppingListRecipeIngredientSection[]>([]);
    const selectedShoppingList = ref<ShoppingListSummary | null>(null);
    const recipeGroupedIngredients = ref<ShoppingListGroupedIngredientLabels[]>([]);

    watchEffect(
      async () => {
        if (props.listForPeriod) {
          console.log(props.listForPeriod);
          for (const list of shoppingListChoices.value) {
            if (list.name === props.listForPeriod) {
              selectedShoppingList.value = list;
              openShoppingListIngredientDialog(selectedShoppingList.value);
              return;
            }
          }
          const { data } = await api.shopping.lists.createOne({ name: props.listForPeriod });
          selectedShoppingList.value = data as ShoppingListSummary;
          openShoppingListIngredientDialog(selectedShoppingList.value);
        } else if (shoppingListChoices.value.length === 1 && !state.shoppingListShowAllToggled) {
          selectedShoppingList.value = shoppingListChoices.value[0];
          openShoppingListIngredientDialog(selectedShoppingList.value);
        } else {
          ready.value = true;
        }
      },
    );

    async function consolidateRecipesIntoGroups(recipes: RecipeWithScale[]) {
      recipeGroupedIngredients.value = [{ section: "", labels: [] }, { section: "On hand", labels: [] }];
      const recipeMap = new Map<string, ShoppingListRecipe>();
      const recipeGroupedIngredientMap = new Map<string, ShoppingListGroupedIngredient>();

      for (const recipe of recipes) {
        if (!recipe.slug) {
          continue;
        }

        if (recipeMap.has(recipe.slug)) {
          // @ts-ignore not undefined, see above
          recipeMap.get(recipe.slug).scale += recipe.scale;
          continue;
        }

        if (!(recipe.id && recipe.name && recipe.recipeIngredient)) {
          const { data } = await api.recipes.getOne(recipe.slug);
          if (!data?.recipeIngredient?.length) {
            continue;
          }
          recipe.id = data.id || "";
          recipe.name = data.name || "";
          recipe.recipeIngredient = data.recipeIngredient;
        } else if (!recipe.recipeIngredient.length) {
          continue;
        }

        const recipeItem: ShoppingListRecipe = {
          id: recipe.id,
          scale: recipe.scale,
          disableAmount: recipe.settings?.disableAmount || false
        }

        recipeMap.set(recipe.slug, recipeItem);

        recipe.recipeIngredient.forEach((ing) => {
          const checked = ing.food && ing.food.name ? !ing.food?.householdsWithIngredientFood?.includes(userHousehold.value) && true : true;

          if (ing.unit?.name) {
            if (massUnitValues[ing.unit.name]) {
              ing.quantity = Number(convertToGram(ing.quantity, ing.unit.name));
              ing.unit = unitStore.store.value.find(unit => unit.name === UnitNames.gram) as IngredientUnit;
            } else if (volumeUnitValues[ing.unit.name]) {
              ing.quantity = Number(convertToMilliliter(ing.quantity, ing.unit.name));
              ing.unit = unitStore.store.value.find(unit => unit.name === UnitNames.milliliter) as IngredientUnit;
            }
          }

          const groupedIngredientMapKey = (ing.food && ing.food.name ? ing.food.name : ing.referenceId || "") + (ing.unit?.name || "");

          if (recipeGroupedIngredientMap.has(groupedIngredientMapKey)) {
            const mapItem = recipeGroupedIngredientMap.get(groupedIngredientMapKey);
            if (mapItem) {
              if (ing.note) {
                mapItem.ingredientSum.note = mapItem.ingredientSum.note ? `${mapItem.ingredientSum.note} | ${ing.note}` : ing.note;
              }
              mapItem.ingredientItems.push({
                checked,
                ingredient: ing,
                recipe: recipeItem
              });
            }
          } else {
            recipeGroupedIngredientMap.set(groupedIngredientMapKey, {
              checked,
              checkedPartial: false,
              ingredientSum: { ...ing },
              ingredientItems: [{
                checked: true,
                ingredient: ing,
                recipe: recipeItem
              }]
            });
          }
        })
      }

      const recipeGroupedIngredientLabelMap = new Map<string, ShoppingListGroupedIngredientLabel>();
      const recipeGroupedIngredientLabelOnHandMap = new Map<string, ShoppingListGroupedIngredientLabel>();

      recipeGroupedIngredientMap.forEach((ing, key) => {
        ing.ingredientItems.forEach((ingItem, index) => {
          if (index === 0) {
            if (ingItem.ingredient.quantity) {
              ing.ingredientSum.quantity = ingItem.ingredient.quantity * ingItem.recipe.scale;
            }
          } else if (ingItem.ingredient.quantity) {
            ing.ingredientSum.quantity = ing.ingredientSum.quantity || 0  + (ingItem.ingredient.quantity * ingItem.recipe.scale);
          }
        })

        let label: string;
        if (ing.ingredientItems[0].ingredient.food) {
          if (ing.ingredientItems[0].ingredient.food.label) {
            label = ing.ingredientItems[0].ingredient.food.label.name;
          } else {
            label = "998_No label"
          }
        } else {
          label = "999_Note"
        }

        if (ing.checked) {
          if (recipeGroupedIngredientLabelMap.has(label)) {
            recipeGroupedIngredientLabelMap.get(label)?.ingredients.push(ing);
          } else {
            recipeGroupedIngredientLabelMap.set(label, {label, ingredients: [ing]});
          }
        } else if (recipeGroupedIngredientLabelOnHandMap.has(label)) {
          recipeGroupedIngredientLabelOnHandMap.get(label)?.ingredients.push(ing);
        } else {
          recipeGroupedIngredientLabelOnHandMap.set(label, { label, ingredients: [ing] });
        }
      })

      recipeGroupedIngredients.value[0].labels = Array.from(recipeGroupedIngredientLabelMap.values()).sort((a, b) => {
        return a.label < b.label ? -1 : 1;
      });
      recipeGroupedIngredients.value[1].labels = Array.from(recipeGroupedIngredientLabelOnHandMap.values()).sort((a, b) => {
        return a.label < b.label ? -1 : 1;
      });
    }

    async function consolidateRecipesIntoSections(recipes: RecipeWithScale[]) {
      const recipeSectionMap = new Map<string, ShoppingListRecipeIngredientSection>();
      for (const recipe of recipes) {
        if (!recipe.slug) {
          continue;
        }

        if (recipeSectionMap.has(recipe.slug)) {
          // @ts-ignore not undefined, see above
          recipeSectionMap.get(recipe.slug).recipeScale += recipe.scale;
          continue;
        }
        if (!(recipe.id && recipe.name && recipe.recipeIngredient)) {
          const { data } = await api.recipes.getOne(recipe.slug);
          if (!data?.recipeIngredient?.length) {
            continue;
          }
          recipe.id = data.id || "";
          recipe.name = data.name || "";
          recipe.recipeIngredient = data.recipeIngredient;
        } else if (!recipe.recipeIngredient.length) {
          continue;
        }

        const shoppingListIngredients: ShoppingListIngredient[] = recipe.recipeIngredient.map((ing) => {
          const householdsWithFood = (ing.food?.householdsWithIngredientFood || []);
          return {
            checked: !householdsWithFood.includes(userHousehold.value),
            ingredient: ing,
            disableAmount: recipe.settings?.disableAmount || false,
          } as ShoppingListIngredient
        });

        let currentTitle = "";
        const onHandIngs: ShoppingListIngredient[] = [];
        const shoppingListIngredientSections = shoppingListIngredients.reduce((sections, ing) => {
          if (ing.ingredient.title) {
            currentTitle = ing.ingredient.title;
          }

          // If this is the first item in the section, create a new section
          if (sections.length === 0 || currentTitle !== sections[sections.length - 1].sectionName) {
            if (sections.length) {
              // Add the on-hand ingredients to the previous section
              sections[sections.length - 1].ingredients.push(...onHandIngs);
              onHandIngs.length = 0;
            }
            sections.push({
              sectionName: currentTitle,
              ingredients: [],
            });
          }

          // Store the on-hand ingredients for later
          const householdsWithFood = (ing.ingredient.food?.householdsWithIngredientFood || []);
          if (householdsWithFood.includes(userHousehold.value)) {
            onHandIngs.push(ing);
            return sections;
          }

          // Add the ingredient to previous section
          sections[sections.length - 1].ingredients.push(ing);
          return sections;
        }, [] as ShoppingListIngredientSection[]);

        // Add remaining on-hand ingredients to the previous section
        shoppingListIngredientSections[shoppingListIngredientSections.length - 1].ingredients.push(...onHandIngs);

        recipeSectionMap.set(recipe.slug, {
          recipeId: recipe.id,
          recipeName: recipe.name,
          recipeScale: recipe.scale,
          ingredientSections: shoppingListIngredientSections,
        })
      }

      recipeIngredientSections.value = Array.from(recipeSectionMap.values());
    }

    function initState() {
      state.shoppingListDialog = true;
      state.shoppingListIngredientDialog = false;
      state.shoppingListShowAllToggled = false;
      recipeIngredientSections.value = [];
      selectedShoppingList.value = null;
      recipeGroupedIngredients.value = [];
    }

    initState();

    async function openShoppingListIngredientDialog(list: ShoppingListSummary) {
      if (!props.recipes?.length) {
        return;
      }

      selectedShoppingList.value = list;
      if (!props.groupIngredients) {
        await consolidateRecipesIntoSections(props.recipes);
      } else {
        await consolidateRecipesIntoGroups(props.recipes);
      }
      state.shoppingListDialog = false;
      state.shoppingListIngredientDialog = true;
    }

    function setShowAllToggled() {
      state.shoppingListShowAllToggled = true;
    }

    function bulkCheckIngredients(value = true) {
      recipeIngredientSections.value.forEach((recipeSection) => {
        recipeSection.ingredientSections.forEach((ingSection) => {
          ingSection.ingredients.forEach((ing) => {
            ing.checked = value;
          });
        });
      });
    }

    const unitStore = useUnitStore();

    async function addRecipesToList() {
      if (!selectedShoppingList.value) {
        return;
      }

      const recipeData: ShoppingListAddRecipeParamsBulk[] = [];
      if (!props.groupIngredients) {
      recipeIngredientSections.value.forEach((section) => {
        const ingredients: RecipeIngredient[] = [];
        section.ingredientSections.forEach((ingSection) => {
          ingSection.ingredients.forEach((ing) => {
            if (ing.checked) {
              const ingredient: RecipeIngredient = {... ing.ingredient};
              if (ingredient.unit?.name) {
                if (massUnitValues[ingredient.unit.name]) {
                  ingredient.quantity = Number(convertToGram(ingredient.quantity, ingredient.unit.name));
                  ingredient.unit = unitStore.store.value.find(unit => unit.name === UnitNames.gram) as IngredientUnit;
                } else if (volumeUnitValues[ingredient.unit.name]) {
                  ingredient.quantity = Number(convertToMilliliter(ingredient.quantity, ingredient.unit.name));
                  ingredient.unit = unitStore.store.value.find(unit => unit.name === UnitNames.milliliter) as IngredientUnit;
                }
              }
              ingredients.push(ingredient);
            }
          });
        });

        if (!ingredients.length) {
          return;
        }

        recipeData.push(
          {
            recipeId: section.recipeId,
            recipeIncrementQuantity: section.recipeScale,
            recipeIngredients: ingredients,
          }
        );
      });
      } else {
        const recipeDataIndexes: {[key: string]: number} = {};
        recipeGroupedIngredients.value.forEach(section => {
          section.labels.forEach((label) => {
            label.ingredients.forEach((ingObject) => {
              ingObject.ingredientItems.forEach((ing) => {
                if (ing.checked) {
                  if (recipeDataIndexes[ing.recipe.id]) {
                    recipeData[recipeDataIndexes[ing.recipe.id]].recipeIngredients?.push(ing.ingredient);
                  } else {
                    recipeDataIndexes[ing.recipe.id] = recipeData.length;
                    recipeData.push({
                      recipeId: ing.recipe.id,
                      recipeIncrementQuantity: ing.recipe.scale,
                      recipeIngredients: [ing.ingredient],
                    });
                  }
                }
              })
            })
          })
        });
      }

      const { error } = await api.shopping.lists.addRecipes(selectedShoppingList.value.id, recipeData);
      error ? alert.error(i18n.tc("recipe.failed-to-add-recipes-to-list"))
      : alert.success(i18n.tc("recipe.successfully-added-to-list"));

      state.shoppingListDialog = false;
      state.shoppingListIngredientDialog = false;
      dialog.value = false;
    }

    return {
      dialog,
      preferences,
      ready,
      shoppingListChoices,
      ...toRefs(state),
      addRecipesToList,
      bulkCheckIngredients,
      openShoppingListIngredientDialog,
      setShowAllToggled,
      recipeIngredientSections,
      selectedShoppingList,
      recipeGroupedIngredients
    }
  },
})
</script>

<style scoped lang="css">
.ingredient-grid {
  display: grid;
  grid-auto-flow: column;
  grid-template-columns: 1fr 1fr;
  grid-gap: 0.5rem;
}
</style>
