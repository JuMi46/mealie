<template>
  <v-tooltip
    location="bottom"
    nudge-right="50"
    :color="buttonStyle ? 'info' : 'secondary'"
  >
    <template #activator="{ props: tooltipProps }">
      <v-btn
        icon
        :variant="buttonStyle ? 'flat' : undefined"
        :rounded="buttonStyle ? 'circle' : undefined"
        size="small"
        :color="buttonStyle ? 'info' : 'secondary'"
        :fab="buttonStyle"
        v-bind="{ ...tooltipProps, ...$attrs }"
        @click="toCombinedView"
      >
        <v-icon
          :size="!buttonStyle ? undefined : 'x-large'"
          :color="buttonStyle ? 'white' : 'secondary'"
        >
          {{ $globals.icons.potSteam }}
        </v-icon>
      </v-btn>
    </template>
    <span>{{ $t("recipe.open-in-combined-view") }}</span>
  </v-tooltip>
</template>

<script setup lang="ts">
const router = useRouter();
const auth = useMealieAuth();
const groupSlug = computed(() => auth.user.value?.groupSlug);

interface Props {
  recipeSlug?: string;
  showAlways?: boolean;
  buttonStyle?: boolean;
}
const props = withDefaults(defineProps<Props>(), {
  recipeSlug: "",
  showAlways: false,
  buttonStyle: false,
});

function toCombinedView() {
  if (!groupSlug.value || !props.recipeSlug) {
    return;
  }
  router.push(`/g/${groupSlug.value}/recipes/combined?recipes=${props.recipeSlug}`);
}
</script>
