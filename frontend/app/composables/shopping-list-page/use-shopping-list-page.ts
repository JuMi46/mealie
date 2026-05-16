import type { ShoppingListItemOut } from "~/lib/api/types/household";
import type { RecipeIngredient } from "~/lib/api/types/recipe";
import { useShoppingListState } from "~/composables/shopping-list-page/sub-composables/use-shopping-list-state";
import { useShoppingListData } from "~/composables/shopping-list-page/sub-composables/use-shopping-list-data";
import { useShoppingListSorting } from "~/composables/shopping-list-page/sub-composables/use-shopping-list-sorting";
import { useShoppingListLabels } from "~/composables/shopping-list-page/sub-composables/use-shopping-list-labels";
import { useShoppingListCopy } from "~/composables/shopping-list-page/sub-composables/use-shopping-list-copy";
import { useShoppingListCrud } from "~/composables/shopping-list-page/sub-composables/use-shopping-list-crud";
import { useShoppingListRecipes } from "~/composables/shopping-list-page/sub-composables/use-shopping-list-recipes";
import { compareLabel } from "~/composables/use-extend-object";
import { printFromNewWindow } from "~/composables/use-utils";
import { useIngredientTextParser } from "~/composables/recipes";

/**
 * Main composable that orchestrates all shopping list page functionality
 */
export function useShoppingListPage(listId: string) {
  // Initialize state
  const state = useShoppingListState();
  const {
    shoppingList,
    loadingCounter,
    recipeReferenceLoading,
    preserveItemOrder,
    listItems,
    sortCheckedItems,
  } = state;

  // Initialize sorting functionality
  const sorting = useShoppingListSorting();
  const { groupAndSortListItemsByFood, sortListItems, updateItemsByLabel } = sorting;

  // Track items organized by label
  const itemsByLabel = ref<{ [key: string]: ShoppingListItemOut[] }>({});

  function updateListItemOrder() {
    if (!shoppingList.value) return;

    if (shoppingList.value?.labelSettings) {
      shoppingList.value.labelSettings.sort((a, b) => compareLabel(a.label, b.label));
    }

    if (!preserveItemOrder.value) {
      groupAndSortListItemsByFood(shoppingList.value);
    }
    else {
      sortListItems(shoppingList.value);
    }

    const labeledItems = updateItemsByLabel(shoppingList.value);
    if (labeledItems) {
      itemsByLabel.value = labeledItems;
    }
  }

  // Initialize data management
  const dataManager = useShoppingListData(listId, shoppingList, loadingCounter);
  const { isOffline, refresh: baseRefresh, startPolling, stopPolling, shoppingListItemActions } = dataManager;

  const refresh = () => baseRefresh(updateListItemOrder);

  // Initialize shopping list labels
  const labels = useShoppingListLabels(shoppingList);

  // Initialize copy functionality
  const copyManager = useShoppingListCopy();

  // Initialize CRUD operations
  const crud = useShoppingListCrud(
    shoppingList,
    loadingCounter,
    listItems,
    shoppingListItemActions,
    refresh,
    sortCheckedItems,
    updateListItemOrder,
  );

  // Initialize recipe management
  const recipes = useShoppingListRecipes(
    shoppingList,
    loadingCounter,
    recipeReferenceLoading,
    refresh,
  );

  // Handle item reordering by label
  function updateIndexUncheckedByLabel(labelName: string, labeledUncheckedItems: ShoppingListItemOut[]) {
    if (!itemsByLabel.value[labelName]) {
      return;
    }

    // update this label's item order
    itemsByLabel.value[labelName] = labeledUncheckedItems;

    // reset list order of all items
    const allUncheckedItems: ShoppingListItemOut[] = [];
    for (const labelKey in itemsByLabel.value) {
      allUncheckedItems.push(...itemsByLabel.value[labelKey]);
    }

    // since the user has manually reordered the list, we should preserve this order
    preserveItemOrder.value = true;

    // save changes
    listItems.unchecked = allUncheckedItems;
    listItems.checked = shoppingList.value?.listItems?.filter(item => item.checked) || [];
    crud.updateUncheckedListItems();
  }

  // Dialog helpers
  function openCheckAll() {
    if (shoppingList.value?.listItems?.some(item => !item.checked)) {
      state.state.checkAllDialog = true;
    }
  }

  function openUncheckAll() {
    if (shoppingList.value?.listItems?.some(item => item.checked)) {
      state.state.uncheckAllDialog = true;
    }
  }

  function openDeleteChecked() {
    if (shoppingList.value?.listItems?.some(item => item.checked)) {
      state.state.deleteCheckedDialog = true;
    }
  }

  function checkAll() {
    state.state.checkAllDialog = false;
    crud.checkAllItems();
  }

  function uncheckAll() {
    state.state.uncheckAllDialog = false;
    crud.uncheckAllItems();
  }

  function deleteChecked() {
    state.state.deleteCheckedDialog = false;
    crud.deleteCheckedItems();
  }

  // Copy functionality wrapper
  function copyListItems(copyType: "plain" | "markdown") {
    copyManager.copyListItems(itemsByLabel.value, copyType);
  }

  // Label reordering helpers
  function toggleReorderLabelsDialog() {
    crud.toggleReorderLabelsDialog(state.reorderLabelsDialog);
  }

  async function saveLabelOrder() {
    await crud.saveLabelOrder(() => {
      const labeledItems = updateItemsByLabel(shoppingList.value!);
      if (labeledItems) {
        itemsByLabel.value = labeledItems;
      }
    });
  }

  const { useParsedIngredientText } = useIngredientTextParser();

  function print() {
    let printableList = shoppingList.value?.name ? `<p class="header">${shoppingList.value?.name}</p>` : "";
    Object.entries(itemsByLabel.value).forEach(([labelName, items]) => {
      printableList += `<p class="label-name">- ${labelName}</p>`;
      for (const item of items) {
        if (item.food) {
          const parsedIng = useParsedIngredientText(item as RecipeIngredient, 1, false);
          printableList += `<p class="ingredient-item">${parseText(parsedIng.quantity)}${parseText(parsedIng.unit)}${parseText(parsedIng.secondaryQuantity)}${parseText(parsedIng.secondaryUnit)}${parseText(parsedIng.name)}</p>`;
        }
        else {
          printableList += `<p class="ingredient-item">${parseNumber(item.quantity)}${parseText(item.note)}</p>`;
        }
      }
    });

    printFromNewWindow(printableList, `
        p {
          font-size: 16px;
        }
        .header {
          margin: 15px 0 0 0;
        }
        .label-name {
          margin: 15px 0 0 0;
        }
        .ingredient-item {
          margin: 5px 0 0 0;
        }`);

    function parseText(t: string | null | undefined) {
      return t ? t.trim() + " " : "";
    }
    function parseNumber(n: number | undefined) {
      return n && n > 0 ? n : "";
    }
  }

  // Lifecycle management
  onMounted(() => {
    startPolling(updateListItemOrder);
  });

  onUnmounted(() => {
    stopPolling();
  });

  return {
    itemsByLabel,
    isOffline,

    // Sub-composables
    ...state,
    ...labels,
    ...crud,
    ...recipes,

    // Specialized functions
    updateIndexUncheckedByLabel,
    copyListItems,

    // Dialog actions
    openCheckAll,
    openUncheckAll,
    openDeleteChecked,
    checkAll,
    uncheckAll,
    deleteChecked,

    // Label management
    toggleReorderLabelsDialog,
    saveLabelOrder,

    // Data refresh
    refresh,

    print,
  };
}
