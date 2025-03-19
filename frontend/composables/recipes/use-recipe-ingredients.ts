import DOMPurify from "isomorphic-dompurify";
import { useFraction } from "./use-fraction";
import { CreateIngredientFood, CreateIngredientUnit, IngredientFood, IngredientUnit, RecipeIngredient } from "~/lib/api/types/recipe";
const { simpleFrac } = useFraction();

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

export function useParsedIngredientText(ingredient: RecipeIngredient, disableAmount: boolean, scale = 1, includeFormating = true) {
  if (disableAmount) {
    return {
      name: ingredient.note ? sanitizeIngredientHTML(ingredient.note) : undefined,
      quantity: undefined,
      alternativeMeasurment: undefined,
      unit: undefined,
      note: undefined,
    };
  }

  const { quantity, unit, note } = ingredient;
  const food = ingredient.food as IngredientFood;
  let scaledQuantity = (quantity||0) * scale;
  const returnUnit = unit && JSON.parse(JSON.stringify(unit)) as IngredientUnit;

  // TODO: Store unit values in better place?
  const massUnitConverter: {[key: string]: number} = { "ounce": 30, "pound": 500 };
  const volumeUnitConverter: {[key: string]: number} = { teaspoon: 5, tablespoon: 15, "fluid ounce": 30, cup: 236.6, pint: 473.18, gallon: 3785.4 };
  const tablespoonBreakpoint = 14.375;
  const cupBreakpoint = 58.125;

  const quantityInMl = scaledQuantity && returnUnit && volumeUnitConverter[returnUnit.name] && scaledQuantity * volumeUnitConverter[returnUnit.name];

  if (returnUnit && scaledQuantity) {
    // TODO: Better way to change to new unit instead of reassigning all fields one by one
    // TODO: Add settings that dictates which convertions to happen (Imperial to Metric, etc)
    if (Object.keys(massUnitConverter).includes(returnUnit.name)) {
      scaledQuantity *= massUnitConverter[returnUnit.name];
      returnUnit.name = "gram";
      returnUnit.pluralName = "grams";
      returnUnit.abbreviation = "g";
      returnUnit.pluralAbbreviation = undefined;
      returnUnit.fraction = false;
      returnUnit.useAbbreviation = true;
    } else if (returnUnit.name === "deciliter") {
      scaledQuantity /= 100;
      returnUnit.name = "milliliter";
      returnUnit.pluralName = "milliliters";
      returnUnit.abbreviation = "ml";
      returnUnit.pluralAbbreviation = undefined;
      returnUnit.fraction = false;
      returnUnit.useAbbreviation = true;
    } else if (quantityInMl) {
      if (quantityInMl >= cupBreakpoint) {
        if (returnUnit.name !== "cup" && returnUnit.name !== "milliliter") {
          scaledQuantity = quantityInMl / volumeUnitConverter.cup;
          returnUnit.name = "cup";
          returnUnit.pluralName = "cups";
          returnUnit.abbreviation = undefined;
          returnUnit.pluralAbbreviation = undefined;
          returnUnit.fraction = true;
          returnUnit.useAbbreviation = false;
        }
      } else if (quantityInMl >= tablespoonBreakpoint || (quantityInMl >= 6.875 && quantityInMl <= 8.125)) {
        if (returnUnit.name !== "tablespoon") {
          scaledQuantity = quantityInMl / volumeUnitConverter.tablespoon;
          returnUnit.name = "tablespoon";
          returnUnit.pluralName = "tablespoons";
          returnUnit.abbreviation = "tbsp";
          returnUnit.pluralAbbreviation = undefined;
          returnUnit.fraction = true;
          returnUnit.useAbbreviation = true;
        }

        if (quantityInMl >= 6.875 && quantityInMl <= 8.125) {
          // 1 1/2 teaspoons becomes 1/2 tablespoon
          scaledQuantity = 0.5;
        }
      } else
       if (returnUnit.name !== "teaspoon") {
          scaledQuantity = quantityInMl / volumeUnitConverter.teaspoon;
          returnUnit.name = "teaspoon";
          returnUnit.pluralName = "teaspoons";
          returnUnit.abbreviation = "tsp";
          returnUnit.pluralAbbreviation = undefined;
          returnUnit.fraction = true;
          returnUnit.useAbbreviation = true;
        }
    }
  }

  const usePluralUnit = quantity !== undefined && (scaledQuantity > 1 || scaledQuantity === 0);
  const usePluralFood = (!quantity) || scaledQuantity > 1

  let returnQty = "";

  // casting to number is required as sometimes quantity is a string
  if (quantity && Number(quantity) !== 0) {
    if (returnUnit && !returnUnit.fraction) {
      returnQty = Number((scaledQuantity).toPrecision(3)).toString();
    } else {
      let fraction;
      if (unit?.name === "teaspoon" && quantityInMl && quantityInMl < 2.1875) {
        // Finer precision under 3/8 teaspoon
        fraction = quantityInMl < 0.9375 ? [0,1,8] : quantityInMl < 1.5625 ? [0,1,4] : [0,3,8];
      } else {
        fraction = simpleFrac(scaledQuantity, !quantityInMl || quantityInMl >= cupBreakpoint);
      }
      if (fraction[0] !== undefined && fraction[0] > 0) {
        returnQty += fraction[0];
      }

      if (fraction[1] > 0) {
        returnQty += includeFormating ?
          `<sup>${fraction[1]}</sup><span>&frasl;</span><sub>${fraction[2]}</sub>` :
          ` ${fraction[1]}/${fraction[2]}`;
      }
    }
  }

  const unitName = useUnitName(returnUnit || undefined, usePluralUnit);
  const foodName = useFoodName(food || undefined, usePluralFood);

  let alternativeMeasurment;

  if (scaledQuantity && returnUnit && volumeUnitConverter[returnUnit.name]) {
    if (food?.description?.startsWith("[")) {
      // TODO: Save ingredient density in a better way in database, food.density
      const densityMatch = /(?<=\[)\d+(|\.\d+)(?=\])/.exec(food?.description);
      if (densityMatch) {
        // TODO: convert to desired unit based on setting
        alternativeMeasurment = `(${Number(Math.ceil(scaledQuantity * volumeUnitConverter[returnUnit.name] * Number(densityMatch[0]))).toString()} g)`;
      }
    } else if (quantityInMl) {
      // TODO: convert to desired unit based on setting
      alternativeMeasurment = `(${Math.ceil(quantityInMl)} ml)`;
    }
  }

  return {
    quantity: returnQty ? sanitizeIngredientHTML(returnQty) : undefined,
    alternativeMeasurment: alternativeMeasurment ? sanitizeIngredientHTML(alternativeMeasurment) : undefined,
    unit: unitName && quantity ? sanitizeIngredientHTML(unitName) : undefined,
    name: foodName ? sanitizeIngredientHTML(foodName) : undefined,
    note: note ? sanitizeIngredientHTML(note) : undefined,
  };
}

export function parseIngredientText(ingredient: RecipeIngredient, disableAmount: boolean, scale = 1, includeFormating = true): string {
  const { quantity, unit, name, note } = useParsedIngredientText(ingredient, disableAmount, scale, includeFormating);

  const text = `${quantity || ""} ${unit || ""} ${name || ""} ${note || ""}`.replace(/ {2,}/g, " ").trim();
  return sanitizeIngredientHTML(text);
}
