<template>
  <v-chip
    v-bind="$attrs"
    label
    variant="flat"
    :color="label.color || undefined"
    :text-color="textColor"
  >
    <span style="max-width: 100%; overflow: hidden; text-overflow: ellipsis;">
      {{ parseLabelName(label, true, $t("shopping-list.no-label")) }}
    </span>
  </v-chip>
</template>

<script setup lang="ts">
import { getTextColor } from "~/composables/use-text-color";
import type { MultiPurposeLabelSummary } from "~/lib/api/types/recipe";
import { parseLabelName } from "~/composables/use-extend-object";

const props = defineProps<{
  label: MultiPurposeLabelSummary;
}>();

const textColor = computed(() => getTextColor(props.label.color));
</script>
