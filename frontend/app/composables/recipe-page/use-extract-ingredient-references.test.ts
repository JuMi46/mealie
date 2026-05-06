import { describe, expect, test, vi, beforeEach } from "vitest";
import { useExtractIngredientReferences } from "./use-extract-ingredient-references";
import { useLocales } from "../use-locales";

vi.mock("../use-locales");

const punctuationMarks = ["*", "?", "/", "!", "**", "&", "."];

describe("test use extract ingredient references", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useLocales).mockReturnValue({
      locales: [{ value: "en-US", pluralFoodHandling: "without-unit" }],
      locale: { value: "en-US", pluralFoodHandling: "without-unit" },
    } as any);
  });

  test("when text empty return empty", () => {
    const { extractIngredientReferences } = useExtractIngredientReferences();
    const result = extractIngredientReferences([{ note: "Onions", referenceId: "123" }], [], "");
    expect(result).toStrictEqual(new Set());
  });

  test("when and ingredient matches exactly and has a reference id, return the referenceId", () => {
    const { extractIngredientReferences } = useExtractIngredientReferences();
    const result = extractIngredientReferences([{ note: "Onions", referenceId: "123" }], [], "A sentence containing Onion");

    expect(result).toEqual(new Set(["123"]));
  });

  test.each(punctuationMarks)("when ingredient is suffixed by punctuation, return the referenceId", (suffix) => {
    const { extractIngredientReferences } = useExtractIngredientReferences();
    const result = extractIngredientReferences([{ note: "Onions", referenceId: "123" }], [], "A sentence containing Onion" + suffix);

    expect(result).toEqual(new Set(["123"]));
  });

  test.each(punctuationMarks)("when ingredient is prefixed by punctuation, return the referenceId", (prefix) => {
    const { extractIngredientReferences } = useExtractIngredientReferences();
    const result = extractIngredientReferences([{ note: "Onions", referenceId: "123" }], [], "A sentence containing " + prefix + "Onion");
    expect(result).toEqual(new Set(["123"]));
  });

  test("when ingredient is first on a multiline, return the referenceId", () => {
    const multilineSting = "lksjdlk\nOnion";

    const { extractIngredientReferences } = useExtractIngredientReferences();
    const result = extractIngredientReferences([{ note: "Onions", referenceId: "123" }], [], multilineSting);
    expect(result).toEqual(new Set(["123"]));
  });

  test("when the ingredient matches partially exactly and has a reference id, return the referenceId", () => {
    const { extractIngredientReferences } = useExtractIngredientReferences();
    const result = extractIngredientReferences([{ note: "Onions", referenceId: "123" }], [], "A sentence containing Onions");
    expect(result).toEqual(new Set(["123"]));
  });

  test("when the ingredient matches with different casing and has a reference id, return the referenceId", () => {
    const { extractIngredientReferences } = useExtractIngredientReferences();
    const result = extractIngredientReferences([{ note: "Onions", referenceId: "123" }], [], "A sentence containing oNions");
    expect(result).toEqual(new Set(["123"]));
  });

  test("when no ingredients, return empty", () => {
    const { extractIngredientReferences } = useExtractIngredientReferences();
    const result = extractIngredientReferences([], [], "A sentence containing oNions");
    expect(result).toEqual(new Set());
  });

  test("when and ingredient matches but in the existing referenceIds, do not return the referenceId", () => {
    const { extractIngredientReferences } = useExtractIngredientReferences();
    const result = extractIngredientReferences([{ note: "Onion", referenceId: "123" }], ["123"], "A sentence containing Onion");

    expect(result).toEqual(new Set());
  });

  test("when an word is 2 letter of shorter, it is ignored", () => {
    const { extractIngredientReferences } = useExtractIngredientReferences();
    const result = extractIngredientReferences([{ note: "Onion", referenceId: "123" }], [], "A sentence containing On");

    expect(result).toEqual(new Set());
  });

  test("matches only lemon zest and vegetable stock in rosemary oil text", () => {
    const { extractIngredientReferences } = useExtractIngredientReferences();
    const text = "Serve hot. Garnish each serving with a swirl of rosemary oil, a few croutons, and a sprinkle of lemon zest. The soup will thicken as it sits; add more stock as necessary when reheating. Leftover rosemary oil will keep in a sealed container at room temperature for up to 1 week.";

    const result = extractIngredientReferences([
      { food: { name: "lemon zest" } as any, referenceId: "lemon-zest" },
      { food: { name: "olive oil" } as any, referenceId: "olive-oil" },
      { food: { name: "fresh rosemary" } as any, referenceId: "fresh-rosemary" },
      { food: { name: "vegetable stock" } as any, referenceId: "vegetable-stock" },
      { food: { name: "salt" } as any, referenceId: "salt" },
      { food: { name: "black pepper" } as any, referenceId: "black-pepper" },
    ], [], text);

    expect(result).toEqual(new Set(["lemon-zest", "vegetable-stock"]));
  });

  test("matches black pepper when instruction only contains pepper", () => {
    const { extractIngredientReferences } = useExtractIngredientReferences();

    const result = extractIngredientReferences([
      { food: { name: "black pepper" } as any, referenceId: "black-pepper" },
    ], [], "Season with pepper to taste");

    expect(result).toEqual(new Set(["black-pepper"]));
  });
});
