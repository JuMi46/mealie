import DOMPurify from "isomorphic-dompurify";
import { useFraction } from "./use-fraction";
import { useLocales } from "../use-locales";
import type { CreateIngredientFood, CreateIngredientUnit, IngredientFood, IngredientUnit, Recipe, RecipeIngredient } from "~/lib/api/types/recipe";
import { UnitNames } from "../use-unit";

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
  unit?: string;
  name?: string;
  note?: string;

  /**
   * If the ingredient is a linked recipe, an HTML link to the referenced recipe, otherwise undefined.
   */
  recipeLink?: string;
  alternativeMeasurement?: string;
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

export function useIngredientTextParser() {
  const { locales, locale } = useLocales();

  function useParsedIngredientText(ingredient: RecipeIngredient, scale = 1, includeFormating = true, groupSlug?: string,
    allUnits?: globalThis.Ref<IngredientUnit[], IngredientUnit[]>, unitsWithRange?: globalThis.Ref<IngredientUnit[], IngredientUnit[]>): ParsedIngredientText {
    const filteredLocales = locales.filter(lc => lc.value === locale.value);
    const pluralFoodHandling = filteredLocales.length ? filteredLocales[0].pluralFoodHandling : "without-unit";

    const { quantity, food, unit, note, referencedRecipe } = ingredient;
    let scaledQuantity = (quantity || 0) * scale;
    let returnUnit = unit;
    let refServings = 0;
    if (ingredient.referencedRecipe?.recipeYield) {
      const refUnit = allUnits?.value.find(unitObj => unitObj.name == ingredient.referencedRecipe?.recipeYield
        || unitObj.abbreviation == ingredient.referencedRecipe?.recipeYield);
      if (refUnit) {
        returnUnit = refUnit;
        if (ingredient.referencedRecipe.recipeYieldQuantity && scaledQuantity > 0) {
          refServings = scaledQuantity / ingredient.referencedRecipe.recipeYieldQuantity;
        }
      }
    }

    const quantityInMl = convertToMilliliter(scaledQuantity, returnUnit);

    if (returnUnit) {
      if (quantityInMl && !returnUnit.range?.some(range => quantityInMl >= range.start && quantityInMl <= range.end) && unitsWithRange?.value) {
        for (const unitObject of unitsWithRange.value) {
          if (unitObject.range?.some(range => quantityInMl >= range.start && quantityInMl <= range.end)) {
            scaledQuantity = quantityInMl / (unitObject.standardQuantity || 1);
            returnUnit = unitObject;
            break;
          }
        }
      }
      else if (returnUnit.standardUnit == UnitNames.gram && returnUnit.name != UnitNames.gram) {
        // TODO: Add settings that dictates which convertions to happen (Imperial to Metric, etc)
        scaledQuantity *= (returnUnit.standardQuantity || 1);
        returnUnit = allUnits?.value.find(unit => unit.name == UnitNames.gram);
      }
    }

    const usePluralUnit = quantity !== undefined && (scaledQuantity > 1 || scaledQuantity === 0);
    const usePluralFood = shouldUsePluralFood(scaledQuantity, !!unit, pluralFoodHandling);

    let returnQty = "";

    // casting to number is required as sometimes quantity is a string
    if (quantity && Number(quantity) !== 0) {
      if (returnUnit && !returnUnit.fraction) {
        const minVal = 10 ** -DECIMAL_PRECISION;
        returnQty = scaledQuantity >= minVal
          ? Number(scaledQuantity.toPrecision(DECIMAL_PRECISION)).toString()
          : `< ${minVal}`;
      }
      else {
        const minVal = 1 / FRAC_MIN_DENOM;
        const isUnderMinVal = !(scaledQuantity >= minVal);

        // const fraction = !isUnderMinVal ? frac(scaledQuantity, FRAC_MIN_DENOM, true) : [0, 1, FRAC_MIN_DENOM];
        let fraction;
        if (unit?.name === UnitNames.teaspoon && quantityInMl && quantityInMl < 2.1875) {
          // Finer precision under 3/8 teaspoon
          fraction = quantityInMl < 0.9375 ? [0, 1, 8] : quantityInMl < 1.5625 ? [0, 1, 4] : [0, 3, 8];
        }
        else {
          fraction = simpleFrac(scaledQuantity, !quantityInMl || quantityInMl >= 58.125);
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
    }

    const unitName = useUnitName(returnUnit || undefined, usePluralUnit);
    const ingName = referencedRecipe ? referencedRecipe.name || "" : useFoodName(food || undefined, usePluralFood);

    let alternativeMeasurement = "";

    if (returnUnit) {
      if (scaledQuantity && returnUnit.standardUnit === UnitNames.milliliter && food?.density) {
      // TODO: convert to desired unit based on setting
        alternativeMeasurement = `(${(Math.ceil(scaledQuantity * (returnUnit.standardQuantity || 1) * food.density)).toString()} g)`;
      }

      if (alternativeMeasurement === "" && quantityInMl && returnUnit.name !== UnitNames.milliliter) {
        // TODO: convert to desired unit based on setting
        alternativeMeasurement = `(${Math.ceil(quantityInMl)} ml)`;
      }
    }

    return {
      quantity: returnQty ? sanitizeIngredientHTML(returnQty) : undefined,
      unit: unitName && quantity ? sanitizeIngredientHTML(unitName) : undefined,
      name: ingName ? sanitizeIngredientHTML(ingName) : undefined,
      note: note ? sanitizeIngredientHTML(note) : undefined,
      recipeLink: useRecipeLink(referencedRecipe || undefined, groupSlug, refServings),
      alternativeMeasurement: alternativeMeasurement ? sanitizeIngredientHTML(alternativeMeasurement) : undefined,
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
  if (unit?.name == UnitNames.milliliter)
    return quantity;
  return quantity && unit && unit.standardUnit == UnitNames.milliliter && quantity * (unit.standardQuantity || 1);
}

export function convertToGram(quantity: number | null | undefined, unit: CreateIngredientUnit | IngredientUnit | null | undefined) {
  if (unit?.name == UnitNames.gram)
    return quantity;
  return quantity && unit && unit.standardUnit == UnitNames.gram && quantity * (unit.standardQuantity || 1);
}

export function convertMilliliterToUnit(quantity: number | null | undefined, unit: CreateIngredientUnit | IngredientUnit | null | undefined) {
  return quantity && unit && unit.standardUnit == UnitNames.milliliter && quantity / (unit.standardQuantity || 1);
}

export function convertGramToUnit(quantity: number | null | undefined, unit: CreateIngredientUnit | IngredientUnit | null | undefined) {
  return quantity && unit && unit.standardUnit == UnitNames.gram && quantity / (unit.standardQuantity || 1);
}
