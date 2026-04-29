import type { MultiPurposeLabelSummary } from "~/lib/api/types/labels";
import type { RecipeTool } from "~/lib/api/types/recipe";

export function compareLabel(a: MultiPurposeLabelSummary | null, b: MultiPurposeLabelSummary | null) {
  if (!a || !b) return 1;
  return (a.position || a.name) < (b.position || b.name) ? -1 : 1;
}

export function parseLabelName(label: MultiPurposeLabelSummary | null | undefined, withPlace: boolean = false) {
  if (!label) {
    const { t } = useI18n();
    return t("shopping-list.no-label");
  }
  return label.labelText ? `${label.labelText}${withPlace && label.place ? `: ${label.place}` : ""}` : label.name;
}

export function parseToolName(tool: RecipeTool) {
  return tool.toolName ? tool.toolName : tool.name;
}
