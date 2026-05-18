import { useToggle } from "@vueuse/core";
import type { ShoppingListOut } from "~/lib/api/types/household";
import { parseLabelName } from "~/composables/use-extend-object";

/**
 * Composable for managing shopping list label state and operations
 */
export function useShoppingListLabels(shoppingList: Ref<ShoppingListOut | null>) {
  const { t } = useI18n();
  const noLabelText = t("shopping-list.no-label");
  const labelOpenState = ref<{ [key: string]: boolean }>({});
  const [showChecked, toggleShowChecked] = useToggle(false);

  const initializeLabelOpenStates = () => {
    if (!shoppingList.value?.listItems) return;

    const existingLabels = new Set(Object.keys(labelOpenState.value));
    let hasChanges = false;

    for (const item of shoppingList.value.listItems) {
      const labelName = parseLabelName(item.label, false, noLabelText);
      if (!existingLabels.has(labelName) && !(labelName in labelOpenState.value)) {
        labelOpenState.value[labelName] = true;
        hasChanges = true;
      }
    }

    if (hasChanges) {
      labelOpenState.value = { ...labelOpenState.value };
    }
  };

  const labelNames = computed(() => {
    return new Set(
      shoppingList.value?.listItems
        ?.map(item => parseLabelName(item.label, false, noLabelText))
        .filter(Boolean) ?? [],
    );
  });

  const labelColorByName = computed(() => {
    const map: Record<string, string | undefined> = {};
    shoppingList.value?.listItems?.forEach((item) => {
      if (!item.label) return;
      const labelName = parseLabelName(item.label, false, noLabelText);
      map[labelName] = item.label.color;
    });
    return map;
  });

  watch(labelNames, initializeLabelOpenStates, { immediate: true });

  function toggleShowLabel(key: string) {
    labelOpenState.value[key] = !labelOpenState.value[key];
  }

  function getLabelColor(label: string) {
    return labelColorByName.value[label];
  }

  const presentLabels = computed(() => {
    const labels: Array<{ id: string; name: string }> = [];

    shoppingList.value?.listItems?.forEach((item) => {
      if (item.labelId && item.label) {
        labels.push({
          name: parseLabelName(item.label, false, noLabelText),
          id: item.labelId,
        });
      }
    });

    return labels;
  });

  return {
    labelOpenState,
    showChecked,
    toggleShowChecked,
    toggleShowLabel,
    getLabelColor,
    presentLabels,
    initializeLabelOpenStates,
  };
}
