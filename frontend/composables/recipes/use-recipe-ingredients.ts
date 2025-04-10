import DOMPurify from "isomorphic-dompurify";
import { findPassedBreakpoint } from "../use-utils";
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

export enum Breakpoints {
  halfTablespoon = 6.875,
  upperTeaspoon = 8.125,
  tablespoon = 14.375,
  cup = 58.125,
}

export enum UnitNames {
  milliliter = "milliliter",
  deciliter = "deciliter",
  liter = "liter",
  teaspoon = "teaspoon",
  tablespoon = "tablespoon",
  fluidOunce = "fluid ounce",
  cup = "cup",
  pint = "pint",
  gallon = "gallon",
  gram = "gram",
  kilogram = "kilogram",
  ounce = "ounce",
  pound = "pound"
};

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
  let scaledQuantity = (quantity || 0) * scale;
  let returnUnit = unit;

  const quantityInMl = convertToMilliliter(scaledQuantity, returnUnit?.name);

  if (returnUnit) {
    if (quantityInMl) {
      [scaledQuantity, returnUnit] = findClosestVolumeUnit(quantityInMl);
      if (!scaledQuantity || !returnUnit) {
        console.log(scaledQuantity, returnUnit, food?.name);
      }
    } else if (massUnitValues[returnUnit.name]) {
      // TODO: Add settings that dictates which convertions to happen (Imperial to Metric, etc)
      scaledQuantity *= massUnitValues[returnUnit.name];
      returnUnit = commonUnits[UnitNames.gram];
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
        fraction = quantityInMl < 0.9375 ? [0, 1, 8] : quantityInMl < 1.5625 ? [0, 1, 4] : [0, 3, 8];
      } else {
        fraction = simpleFrac(scaledQuantity, !quantityInMl || quantityInMl >= Breakpoints.cup);
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

  if (scaledQuantity && returnUnit && (returnUnit.name === UnitNames.milliliter || volumeUnitValues[returnUnit.name])) {
    if (food?.description?.startsWith("[")) {
      // TODO: Save ingredient density in a better way in database, food.density
      const densityMatch = /(?<=\[)\d+(|\.\d+)(?=\])/.exec(food?.description);
      if (densityMatch) {
        // TODO: convert to desired unit based on setting
        alternativeMeasurment = `(${Number(Math.ceil(scaledQuantity * (returnUnit.name !== UnitNames.milliliter ? volumeUnitValues[returnUnit.name] : 1)
          * Number(densityMatch[0]))).toString()} g)`;
      }
    } else if (quantityInMl && returnUnit.name !== UnitNames.milliliter) {
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

export const volumeUnitBreakpoints: Array<[number, [unitName: UnitNames, overrideQuantity: any]]> = [
  [0, [UnitNames.teaspoon, undefined]],
  [Breakpoints.halfTablespoon, [UnitNames.tablespoon, 0.5]],
  [Breakpoints.upperTeaspoon, [UnitNames.teaspoon, undefined]],
  [Breakpoints.tablespoon, [UnitNames.tablespoon, undefined]],
  [Breakpoints.cup, [UnitNames.cup, undefined]],
];

export const commonUnits: { [key: string]: IngredientUnit } = {
  gram: {
    id: "",
    name: "gram",
    pluralName: "grams",
    abbreviation: "g",
    pluralAbbreviation: undefined,
    fraction: false,
    useAbbreviation: true,
  },
  milliliter: {
    id: "",
    name: "milliliter",
    pluralName: "milliliters",
    abbreviation: "ml",
    pluralAbbreviation: undefined,
    fraction: false,
    useAbbreviation: true,
  },
  cup: {
    id: "",
    name: "cup",
    pluralName: "cups",
    abbreviation: undefined,
    pluralAbbreviation: undefined,
    fraction: true,
    useAbbreviation: false,
  },
  tablespoon: {
    id: "",
    name: "tablespoon",
    pluralName: "tablespoons",
    abbreviation: "tbsp",
    pluralAbbreviation: undefined,
    fraction: true,
    useAbbreviation: true,
  },
  teaspoon: {
    id: "",
    name: "teaspoon",
    pluralName: "teaspoons",
    abbreviation: "tsp",
    pluralAbbreviation: undefined,
    fraction: true,
    useAbbreviation: true,
  }
}

export const massUnitValues: { [key: string]: number } = { ounce: 31.25, pound: 500 };
export const volumeUnitValues: { [key: string]: number } = { teaspoon: 5, tablespoon: 15, "fluid ounce": 30, cup: 236.6, pint: 473.18, gallon: 3785.4 };

export function convertToMilliliter(quantity: number | null | undefined, unitName: string | undefined) {
  return quantity && unitName && volumeUnitValues[unitName] && quantity * volumeUnitValues[unitName];
}

export function convertToGram(quantity: number | null | undefined, unitName: string | undefined) {
  return quantity && unitName && massUnitValues[unitName] && quantity * massUnitValues[unitName];
}

export function convertMilliliterToUnit(quantity: number | null | undefined, unitName: string | undefined) {
  return quantity && unitName && volumeUnitValues[unitName] && quantity / volumeUnitValues[unitName]
}

export function convertGramToUnit(quantity: number | null | undefined, unitName: string | undefined) {
  return quantity && unitName && massUnitValues[unitName] && quantity / massUnitValues[unitName];
}

export function findClosestVolumeUnit(quantityInMl: number): [number, IngredientUnit] {
  // TODO: Add settings that dictates which convertions to happen (Imperial to Metric, etc)
  const breakpoint = findPassedBreakpoint(quantityInMl, volumeUnitBreakpoints)[1];
  return [
    breakpoint[1] ? Number(breakpoint[1]) : quantityInMl / volumeUnitValues[breakpoint[0]],
    commonUnits[breakpoint[0]]
  ];
}
