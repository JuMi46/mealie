/* tslint:disable */
/* eslint-disable */
/**
/* This file was automatically generated from pydantic models by running pydantic2ts.
/* Do not modify it by hand - just update the pydantic models and then re-run the script
*/

export interface OpenAIIngredient {
  quantity?: number | null;
  unit?: string | null;
  food?: string | null;
  note?: string | null;
}
export interface OpenAIIngredients {
  ingredients?: OpenAIIngredient[];
}
export interface OpenAIRecipe {
  name: string;
  description?: string | null;
  recipe_yield?: string | null;
  total_time?: string | null;
  prep_time?: string | null;
  perform_time?: string | null;
  primary_unit_system?: string | null;
  ingredients?: OpenAIRecipeIngredient[];
  instructions?: OpenAIRecipeInstruction[];
  notes?: OpenAIRecipeNotes[];
}
export interface OpenAIRecipeIngredient {
  title?: string | null;
  text: string;
  reference_id?: string | null;
  quantity?: number | null;
  unit_name?: string | null;
  food_name?: string | null;
  note?: string | null;
  quantity_in_ml?: number | null;
}
export interface OpenAIRecipeInstruction {
  title?: string | null;
  text: string;
  id?: string | null;
  preparation_instruction_id?: string | null;
  ingredient_references?: OpenAIRecipeIngredientReference[];
  ingredients_with_quantity?: OpenAIRecipeIngredientWithQuantity[];
  timers?: OpenAIRecipeTimer[];
}
export interface OpenAIRecipeIngredientReference {
  reference_id?: string | null;
}
export interface OpenAIRecipeIngredientWithQuantity {
  reference_id?: string | null;
  quantity?: number | null;
  quantity_in_ml?: number | null;
  unit_name?: string | null;
  comment?: string | null;
}
export interface OpenAIRecipeTimer {
  duration: number;
  text?: string | null;
}
export interface OpenAIRecipeNotes {
  title?: string | null;
  text: string;
}
export interface OpenAIText {
  text: string;
}
export interface OpenAIBase {}
export interface OpenAIFoodTranslationItem {
  en: string;
  jp: string;
  jpKanji?: string;
}
export interface OpenAIFoodTranslations {
  translations?: OpenAIFoodTranslationItem[];
}
export interface OpenAIRecipeInstructionTimerResult {
  instructions?: OpenAIRecipeInstructionTimerStep[];
}
export interface OpenAIRecipeInstructionTimerStep {
  id?: string | null;
  text: string;
  timers?: OpenAIRecipeTimer[];
}
