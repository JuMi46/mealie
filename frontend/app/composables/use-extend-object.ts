import type { MultiPurposeLabelSummary } from "~/lib/api/types/labels";

export function compareLabel(a: MultiPurposeLabelSummary | null, b: MultiPurposeLabelSummary | null) {
  if (!a || !b) return 1;
  return (a.position || a.name) < (b.position || b.name) ? -1 : 1;
}

export function parseLabelName(
  label: MultiPurposeLabelSummary | null | undefined,
  withPlace: boolean = false,
  noLabelText: string = "",
) {
  if (!label) {
    return noLabelText;
  }
  return `${label.name}${withPlace && label.place ? `: ${label.place}` : ""}`;
}
