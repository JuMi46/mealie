import DOMPurify from "isomorphic-dompurify";
import { useFraction } from "./use-fraction";
import { useLocales } from "../use-locales";
import { milliliterUnit, gramUnit, useUnitStore } from "../store";
import type { CreateIngredientFood, CreateIngredientUnit, IngredientFood, IngredientUnit, IngredientUnitRange, Recipe, RecipeIngredient } from "~/lib/api/types/recipe";
import { UnitNames } from "../use-unit";
import { useHouseholdSelf } from "~/composables/use-households";

const { simpleFrac } = useFraction();

const FRAC_MIN_DENOM = 10;
const DECIMAL_PRECISION = 3;

export function sanitizeIngredientHTML(rawHtml: string) {
  return DOMPurify.sanitize(rawHtml, {
    USE_PROFILES: { html: true },
    ALLOWED_TAGS: ["b", "q", "i", "strong", "sup"],
  });
}

function useFoodName(food: CreateIngredientFood | IngredientFood | undefined, usePlural: boolean) {
  if (!food) {
    return "";
  }

  return (usePlural ? food.pluralName || food.name : food.name) || "";
}

function useUnitName(unit: CreateIngredientUnit | IngredientUnit | undefined, usePlural: boolean) {
  if (!unit) {
    return "";
  }

  let returnVal = "";
  if (unit.useAbbreviation) {
    returnVal = (usePlural ? unit.pluralAbbreviation || unit.abbreviation : unit.abbreviation) || "";
  }

  if (!returnVal) {
    returnVal = (usePlural ? unit.pluralName || unit.name : unit.name) || "";
  }

  return returnVal;
}

function useRecipeLink(recipe: Recipe | undefined, groupSlug: string | undefined, servings: number | undefined): string | undefined {
  if (!(recipe && recipe.slug && recipe.name && groupSlug)) {
    return undefined;
  }
  const servingsQuery = servings || 0 > 0 ? `?servings=${servings}` : "";
  return `<a href="/g/${groupSlug}/r/${recipe.slug}${servingsQuery}" target="_blank">${recipe.name}</a>`;
}

type ParsedIngredientText = {
  quantity?: string;
  secondaryQuantity?: string;
  unit?: string;
  secondaryUnit?: string;
  name?: string;
  note?: string;
  recipeLink?: string;
};

function shouldUsePluralFood(quantity: number, hasUnit: boolean, pluralFoodHandling: string): boolean {
  if (quantity && quantity <= 1) {
    return false;
  }

  switch (pluralFoodHandling) {
    case "always":
      return true;
    case "without-unit":
      return !(quantity && hasUnit);
    case "never":
      return false;

    default:
      // same as without-unit
      return !(quantity && hasUnit);
  }
}

function inRange(range: IngredientUnitRange[] | null | undefined, quantity: number): boolean {
  return range?.some(range => quantity >= range.start && quantity <= range.end) || false;
}

export function useIngredientTextParser() {
  const { locales, locale } = useLocales();
  const _ = useUnitStore();
  const { household } = useHouseholdSelf();

  function convertToPreferredUnits(
    scaledQuantity: number,
    returnUnit: IngredientUnit,
    quantityInMl: number,
    food: IngredientFood | CreateIngredientFood | null | undefined) {
    if (quantityInMl) {
      return convertVolumeUnit(scaledQuantity, returnUnit, quantityInMl, food);
    }
    else if (returnUnit.standardUnit == UnitNames.gram && returnUnit.standardQuantity) {
      return convertMassUnit(scaledQuantity, returnUnit);
    }
  }

  function convertVolumeUnit(
    scaledQuantity: number,
    returnUnit: IngredientUnit,
    quantityInMl: number,
    food: IngredientFood | CreateIngredientFood | null | undefined,
  ) {
    const primaryVolumeUnits = household.value?.preferences?.primaryVolumeUnits || [];
    if (primaryVolumeUnits.length == 0)
      return null;

    const primaryMassUnits = household.value?.preferences?.primaryMassUnits || [];
    const secondaryVolumeUnits = household.value?.preferences?.secondaryVolumeUnits || [];
    let secondaryUnit: IngredientUnit | CreateIngredientUnit | null | undefined;
    let secondaryUnitQuantity: number | undefined;

    if (!primaryVolumeUnits.some(unit => unit.id === returnUnit?.id) || !inRange(returnUnit?.range, quantityInMl)) {
      for (const unitObject of primaryVolumeUnits) {
        if (unitObject.standardUnit === UnitNames.milliliter && inRange(unitObject.range, quantityInMl)) {
          scaledQuantity = quantityInMl / (unitObject.standardQuantity || 1);
          returnUnit = unitObject;
          break;
        }
      }
    }

    if (food?.density) {
      const quantityInGrams = quantityInMl * food.density;
      const matchingPrimaryMassUnit = primaryMassUnits.find(
        unitObject => unitObject.standardUnit === UnitNames.gram
          && inRange(unitObject.range, quantityInGrams),
      ) || primaryMassUnits.find(unitObject => unitObject.standardUnit === UnitNames.gram);

      if (matchingPrimaryMassUnit) {
        secondaryUnit = matchingPrimaryMassUnit;
        secondaryUnitQuantity = quantityInGrams / (matchingPrimaryMassUnit.standardQuantity || 1);
      }
    }
    else {
      const matchingSecondaryVolumeUnit = secondaryVolumeUnits.find(
        unitObject => unitObject.standardUnit === UnitNames.milliliter
          && inRange(unitObject.range, quantityInMl),
      ) || secondaryVolumeUnits.find(unitObject => unitObject.standardUnit === UnitNames.milliliter);

      if (matchingSecondaryVolumeUnit) {
        secondaryUnit = matchingSecondaryVolumeUnit;
        secondaryUnitQuantity = quantityInMl / (matchingSecondaryVolumeUnit.standardQuantity || 1);
      }
    }

    return { scaledQuantity, returnUnit, secondaryUnit, secondaryUnitQuantity };
  }

  function convertMassUnit(scaledQuantity: number, returnUnit: IngredientUnit) {
    const primaryMassUnits = household.value?.preferences?.primaryMassUnits || [];
    if (primaryMassUnits.length == 0)
      return null;

    const secondaryMassUnits = household.value?.preferences?.secondaryMassUnits || [];
    let secondaryUnit: IngredientUnit | CreateIngredientUnit | null | undefined;
    let secondaryUnitQuantity: number | undefined;

    const quantityInGrams = convertToGram(scaledQuantity, returnUnit) || 0;

    // Check if not in primary mass units or out of range
    if (!primaryMassUnits.some(unit => unit.id === returnUnit.id)
      || !inRange(returnUnit?.range, quantityInGrams)) {
      // Find best matching primary mass unit
      for (const unitObject of primaryMassUnits) {
        if (unitObject.standardUnit === UnitNames.gram && inRange(unitObject.range, quantityInGrams)) {
          scaledQuantity = quantityInGrams / (unitObject.standardQuantity || 1);
          returnUnit = unitObject;
          break;
        }
      }
    }

    // Find best matching secondary mass unit
    const matchingSecondaryMassUnit = secondaryMassUnits.find(
      unitObject => unitObject.standardUnit === UnitNames.gram
        && inRange(unitObject.range, quantityInGrams),
    ) || secondaryMassUnits.find(unitObject => unitObject.standardUnit === UnitNames.gram);

    if (matchingSecondaryMassUnit) {
      secondaryUnit = matchingSecondaryMassUnit;
      secondaryUnitQuantity = quantityInGrams / (matchingSecondaryMassUnit.standardQuantity || 1);
    }

    return { scaledQuantity, returnUnit, secondaryUnit, secondaryUnitQuantity };
  }

  function parseQuantity(quantity: number, quantityInMl: number | null | undefined,
    unit: IngredientUnit | CreateIngredientUnit | null | undefined, includeFormating: boolean): string {
    // casting to number is required as sometimes quantity is a string
    if (!quantity && Number(quantity) === 0) {
      return "";
    }

    let returnQty = "";
    if (!unit || !unit.fraction) {
      const minVal = 10 ** -DECIMAL_PRECISION;
      returnQty = quantity >= minVal
        ? Number(quantity.toPrecision(DECIMAL_PRECISION)).toString()
        : `< ${minVal}`;
    }
    else {
      const minVal = 1 / FRAC_MIN_DENOM;
      const isUnderMinVal = !(quantity >= minVal);

      // const fraction = !isUnderMinVal ? frac(quantity, FRAC_MIN_DENOM, true) : [0, 1, FRAC_MIN_DENOM];
      let fraction;
      if (unit?.name === UnitNames.teaspoon && quantityInMl && quantityInMl < 2.1875) {
        // Finer precision under 3/8 teaspoon
        fraction = quantityInMl < 0.9375 ? [0, 1, 8] : quantityInMl < 1.5625 ? [0, 1, 4] : [0, 3, 8];
      }
      else {
        fraction = simpleFrac(quantity, !quantityInMl || quantityInMl >= 58.125);
      }
      if (fraction[0] !== undefined && fraction[0] > 0) {
        returnQty += fraction[0];
      }

      if (fraction[1] > 0) {
        returnQty += includeFormating
          ? `<sup>${fraction[1]}</sup><span>&frasl;</span><sub>${fraction[2]}</sub>`
          : ` ${fraction[1]}/${fraction[2]}`;
      }

      if (isUnderMinVal) {
        returnQty = `< ${returnQty}`;
      }
    }
    return returnQty;
  }

  function useParsedIngredientText(ingredient: RecipeIngredient, scale = 1, includeFormating = true, groupSlug?: string): ParsedIngredientText {
    const filteredLocales = locales.filter(lc => lc.value === locale.value);
    const pluralFoodHandling = filteredLocales[0]?.pluralFoodHandling || "without-unit";

    const { quantity, food, unit, note, referencedRecipe } = ingredient;
    let scaledQuantity = (quantity || 0) * scale;
    let returnUnit = unit;
    let refServings = 0;
    let secondaryUnit: IngredientUnit | CreateIngredientUnit | null | undefined;
    let secondaryUnitQuantity: number | undefined;

    if (referencedRecipe?.recipeYieldUnit) {
      returnUnit = referencedRecipe.recipeYieldUnit as IngredientUnit;
      if (referencedRecipe.recipeYieldQuantity && scaledQuantity > 0) {
        refServings = scaledQuantity / referencedRecipe.recipeYieldQuantity;
      }
    }

    const quantityInMl = convertToMilliliter(scaledQuantity, returnUnit) || 0;

    if (returnUnit?.id) {
      const preferredUnits = convertToPreferredUnits(scaledQuantity, returnUnit as IngredientUnit, quantityInMl, food);
      if (preferredUnits) {
        scaledQuantity = preferredUnits.scaledQuantity;
        returnUnit = preferredUnits.returnUnit;
        secondaryUnit = preferredUnits.secondaryUnit;
        secondaryUnitQuantity = preferredUnits.secondaryUnitQuantity;
      }
    }

    const usePluralUnit = quantity !== undefined && (scaledQuantity > 1 || scaledQuantity === 0);
    const usePluralSecondaryUnit = secondaryUnitQuantity !== undefined && (secondaryUnitQuantity > 1 || secondaryUnitQuantity === 0);
    const usePluralFood = shouldUsePluralFood(scaledQuantity, !!unit, pluralFoodHandling);
    const returnQty = parseQuantity(scaledQuantity, quantityInMl, returnUnit, includeFormating);
    const returnSecondaryQty = parseQuantity(secondaryUnitQuantity || 0, quantityInMl, secondaryUnit, includeFormating);
    const unitName = useUnitName(returnUnit || undefined, usePluralUnit);
    const secondaryUnitName = useUnitName(secondaryUnit || undefined, usePluralSecondaryUnit);
    const ingName = referencedRecipe ? referencedRecipe.name || "" : useFoodName(food || undefined, usePluralFood);

    return {
      quantity: returnQty ? sanitizeIngredientHTML(returnQty) : undefined,
      secondaryQuantity: returnSecondaryQty ? sanitizeIngredientHTML(returnSecondaryQty) : undefined,
      unit: unitName && quantity ? sanitizeIngredientHTML(unitName) : undefined,
      secondaryUnit: secondaryUnitName ? sanitizeIngredientHTML(secondaryUnitName) : undefined,
      name: ingName ? sanitizeIngredientHTML(ingName) : undefined,
      note: note ? sanitizeIngredientHTML(note) : undefined,
      recipeLink: useRecipeLink(referencedRecipe || undefined, groupSlug, refServings),
    };
  };

  function parseIngredientText(ingredient: RecipeIngredient, scale = 1, includeFormating = true): string {
    const { quantity, unit, name, note } = useParsedIngredientText(ingredient, scale, includeFormating);

    const text = `${quantity || ""} ${unit || ""} ${name || ""} ${note || ""}`.replace(/ {2,}/g, " ").trim();
    return sanitizeIngredientHTML(text);
  };

  function ingredientToParserString(ingredient: RecipeIngredient): string {
    if (ingredient.originalText) {
      return ingredient.originalText;
    }

    // If the ingredient has no unit and no food, it's unparsed — the note
    // contains the full ingredient text. Using parseIngredientText would
    // incorrectly prepend the quantity (e.g. "1 1/2 cup apples").
    if (!ingredient.unit && !ingredient.food) {
      return ingredient.note || "";
    }

    return parseIngredientText(ingredient, 1, false) ?? "";
  }

  return {
    useParsedIngredientText,
    parseIngredientText,
    ingredientToParserString,
  };
}

export function convertToMilliliter(quantity: number | null | undefined, unit: CreateIngredientUnit | IngredientUnit | null | undefined) {
  if (unit?.name == UnitNames.milliliter || unit?.name == milliliterUnit.value?.name) {
    return quantity;
  }
  if (!unit || !quantity || !unit.standardQuantity) {
    return undefined;
  }
  if (unit.standardUnit == UnitNames.milliliter) {
    return quantity * unit.standardQuantity;
  }
  if (unit.standardUnit == milliliterUnit.value?.standardUnit && milliliterUnit.value?.standardQuantity) {
    return quantity * unit.standardQuantity * (milliliterUnit.value.standardQuantity / unit.standardQuantity);
  }
  // Could there be any instance where a users standard unit and milliliter do not have the same anchor unit?
  return undefined;
}

export function convertToGram(quantity: number | null | undefined, unit: CreateIngredientUnit | IngredientUnit | null | undefined) {
  if (unit?.name == UnitNames.gram || unit?.name == gramUnit.value?.name) {
    return quantity;
  }
  if (!unit || !quantity || !unit.standardQuantity) {
    return undefined;
  }
  if (unit.standardUnit == UnitNames.gram) {
    return quantity * unit.standardQuantity;
  }
  if (unit.standardUnit == gramUnit.value?.standardUnit && gramUnit.value?.standardQuantity) {
    return quantity * unit.standardQuantity * (gramUnit.value.standardQuantity / unit.standardQuantity);
  }
  // Could there be any instance where a users standard unit and gram do not have the same anchor unit?
  return undefined;
}
