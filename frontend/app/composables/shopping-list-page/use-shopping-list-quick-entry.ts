import type { Ref } from "vue";
import type { ShoppingListItemCreate, ShoppingListItemOut } from "~/lib/api/types/household";
import type { IngredientFood, IngredientUnit } from "~/lib/api/types/recipe";

type FoodInputRef = {
  focusWithSearch: (value: string) => void;
};

interface UseShoppingListQuickEntryOptions {
  listItem: Ref<ShoppingListItemCreate | ShoppingListItemOut>;
  foods: () => IngredientFood[];
  units: () => IngredientUnit[];
  foodInputRef: Ref<FoodInputRef | null>;
}

export function useShoppingListQuickEntry(options: UseShoppingListQuickEntryOptions) {
  const { listItem, foods, units, foodInputRef } = options;
  const quickEntry = ref("");

  function normalizeTerm(value: string) {
    return value.trim().toLowerCase().replace(/\.$/, "");
  }

  function findMatchingUnit(unitText: string) {
    const normalized = normalizeTerm(unitText);

    if (!normalized) {
      return null;
    }

    return units().find((unit) => {
      const terms = [unit.name, unit.pluralName, unit.abbreviation, unit.pluralAbbreviation]
        .filter(Boolean)
        .map(term => normalizeTerm(term!));

      return terms.includes(normalized);
    }) || null;
  }

  async function assignFoodByName(foodName: string) {
    const normalized = normalizeTerm(foodName);

    if (!normalized) {
      listItem.value.food = null;
      listItem.value.foodId = null;
      return true;
    }

    const existingFood = foods().find((food) => {
      if (normalizeTerm(food.name) === normalized) {
        return true;
      }

      const aliasMatch = food.aliases?.some(alias => normalizeTerm(alias.name) === normalized);
      return Boolean(aliasMatch);
    }) || null;

    if (existingFood) {
      listItem.value.food = existingFood as any;
      listItem.value.foodId = existingFood.id;
      return true;
    }

    listItem.value.food = null;
    listItem.value.foodId = null;
    await nextTick();
    setTimeout(() => {
      foodInputRef.value?.focusWithSearch(foodName);
    }, 0);
    return false;
  }

  async function parseQuickEntry() {
    const rawText = quickEntry.value.trim();

    if (!rawText) {
      return;
    }

    const quantityMatch = rawText.match(/^(\d+(?:[.,]\d+)?)(?:\s*)(.+)$/);

    if (!quantityMatch) {
      const hasExistingFood = await assignFoodByName(rawText);
      if (hasExistingFood) {
        quickEntry.value = "";
      }
      return;
    }

    const quantityText = quantityMatch[1];
    const remainderText = quantityMatch[2];

    if (!quantityText || !remainderText) {
      const hasExistingFood = await assignFoodByName(rawText);
      if (hasExistingFood) {
        quickEntry.value = "";
      }
      return;
    }

    const quantity = Number(quantityText.replace(",", "."));
    if (!Number.isNaN(quantity)) {
      listItem.value.quantity = quantity;
    }

    const remainder = remainderText.trim();
    const tokens = remainder.split(/\s+/).filter(Boolean);

    let unitMatch: IngredientUnit | null = null;
    let unitTokenLength = 0;

    // Prefer the longest prefix to support multi-word unit names.
    for (let length = Math.min(3, tokens.length); length >= 1; length--) {
      const candidate = tokens.slice(0, length).join(" ");
      const matchedUnit = findMatchingUnit(candidate);

      if (matchedUnit) {
        unitMatch = matchedUnit;
        unitTokenLength = length;
        break;
      }
    }

    if (unitMatch) {
      listItem.value.unit = unitMatch as any;
      listItem.value.unitId = unitMatch.id;
    }
    else {
      listItem.value.unit = null;
      listItem.value.unitId = null;
    }

    const foodName = tokens.slice(unitTokenLength).join(" ").trim();

    if (foodName) {
      const hasExistingFood = await assignFoodByName(foodName);
      if (hasExistingFood) {
        quickEntry.value = "";
      }
      return;
    }

    quickEntry.value = "";
  }

  return {
    quickEntry,
    parseQuickEntry,
  };
}
