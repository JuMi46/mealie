import type { RecipeIngredient } from "~/lib/api/types/recipe";
import { useIngredientTextParser } from "~/composables/recipes";

function normalize(word: string): string {
  let normalizing = word;
  normalizing = removeTrailingPunctuation(normalizing);
  normalizing = removeStartingPunctuation(normalizing);
  return normalizing;
}

function removeTrailingPunctuation(word: string): string {
  const punctuationAtEnding = /\p{P}+$/u;
  return word.replace(punctuationAtEnding, "");
}

function removeStartingPunctuation(word: string): string {
  const punctuationAtBeginning = /^\p{P}+/u;
  return word.replace(punctuationAtBeginning, "");
}

function isBlackListedWord(word: string) {
  // Ignore matching blacklisted words when auto-linking - This is kind of a cludgey implementation. We're blacklisting common words but
  // other common phrases trigger false positives and I'm not sure how else to approach this. In the future I maybe look at looking directly
  // at the food variable and seeing if the food is in the instructions, but I still need to support those who don't want to provide the value
  // and only use the "notes" feature.
  const blackListedText: string[] = [
    "and",
    "the",
    "for",
    "with",
    "without",
  ];
  const blackListedRegexMatch = /\d/; // Match Any Number
  return blackListedText.includes(word) || blackListedRegexMatch.test(word);
}

function tokenize(text: string): string[] {
  return text
    .toLowerCase()
    .split(/\s+/)
    .map(normalize)
    .filter(word => word.length > 2)
    .filter(word => !isBlackListedWord(word));
}

function toMatchKey(token: string): string {
  if (token.endsWith("ies") && token.length > 3) {
    return `${token.slice(0, -3)}y`;
  }

  if (token.endsWith("es") && /(ches|shes|sses|xes|zes)$/.test(token)) {
    return token.slice(0, -2);
  }

  if (token.endsWith("s") && !token.endsWith("ss") && token.length > 3) {
    return token.slice(0, -1);
  }

  return token;
}

function toMatchKeys(text: string): string[] {
  return tokenize(text).map(toMatchKey);
}

function canUseSingleTokenFallback(ingredientTokens: string[]): boolean {
  const [lastToken] = ingredientTokens.slice(-1);

  if (lastToken === undefined) {
    return false;
  }

  // Some ingredients are commonly referenced by just the final noun in instructions.
  return ["stock", "broth", "pepper"].includes(lastToken);
}

export function useExtractIngredientReferences() {
  const { ingredientToParserString } = useIngredientTextParser();

  function extractIngredientReferences(recipeIngredients: RecipeIngredient[], activeRefs: string[], text: string): Set<string> {
    function ingredientMatchesText(ingredient: RecipeIngredient, textTokens: string[], textTokenSet: Set<string>) {
      const searchText = ingredient.food?.name || ingredientToParserString(ingredient);
      const ingredientTokens = toMatchKeys(searchText);

      if (ingredientTokens.length === 0) {
        return false;
      }

      const normalizedText = ` ${textTokens.join(" ")} `;
      const ingredientPhrase = ingredientTokens.join(" ");

      if (normalizedText.includes(` ${ingredientPhrase} `)) {
        return true;
      }

      if (ingredientTokens.length === 1) {
        const [singleToken] = ingredientTokens;
        return singleToken !== undefined && textTokenSet.has(singleToken);
      }

      if (canUseSingleTokenFallback(ingredientTokens)) {
        const [lastToken] = ingredientTokens.slice(-1);
        if (lastToken !== undefined && textTokenSet.has(lastToken)) {
          return true;
        }
      }

      const matchedTokenCount = ingredientTokens.filter(token => textTokenSet.has(token)).length;
      return matchedTokenCount >= 2;
    }

    const availableIngredients = recipeIngredients
      .filter(ingredient => ingredient.referenceId !== undefined)
      .filter(ingredient => !activeRefs.includes(ingredient.referenceId as string));

    const textTokens = toMatchKeys(text);
    const textTokenSet = new Set<string>(textTokens);

    if (textTokenSet.size === 0) {
      return new Set<string>();
    }

    const allMatchedIngredientIds: string[] = availableIngredients
      .filter(ingredient => ingredientMatchesText(ingredient, textTokens, textTokenSet))
      .map(ingredient => ingredient.referenceId as string);

    return new Set<string>(allMatchedIngredientIds);
  }

  return {
    extractIngredientReferences,
  };
}
