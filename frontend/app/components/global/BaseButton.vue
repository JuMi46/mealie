<template>
  <v-btn
    :color="color || btnAttrs.color"
    :size="small ? 'small' : 'default'"
    :x-small="xSmall"
    :loading="loading"
    :disabled="disabled"
    :variant="disabled ? 'tonal' : btnStyle.outlined ? 'outlined' : btnStyle.text ? 'text' : 'elevated'"
    :to="to"
    v-bind="$attrs"
    @click="download ? downloadFile() : undefined"
  >
    <v-icon v-if="!iconRight && !onlyText" start>
      <slot name="icon">
        {{ icon || btnAttrs.icon }}
      </slot>
    </v-icon>
    <slot :v-if="!onlyIcon" name="default">
      {{ text || btnAttrs.text }}
    </slot>
    <v-icon
      v-if="iconRight"
      end
    >
      <slot name="icon">
        {{ icon || btnAttrs.icon }}
      </slot>
    </v-icon>
  </v-btn>
</template>

<script setup lang="ts">
import { useUserApi } from "~/composables/api";

const props = defineProps({
  cancel: {
    type: Boolean,
    default: false,
  },
  create: {
    type: Boolean,
    default: false,
  },
  update: {
    type: Boolean,
    default: false,
  },
  edit: {
    type: Boolean,
    default: false,
  },
  save: {
    type: Boolean,
    default: false,
  },
  delete: {
    type: Boolean,
    default: false },
  download: {
    type: Boolean,
    default: false,
  },
  downloadUrl: {
    type: String,
    default: "",
  },
  loading: {
    type: Boolean,
    default: false,
  },
  disabled: {
    type: Boolean,
    default: false,
  },
  small: {
    type: Boolean,
    default: false,
  },
  xSmall: {
    type: Boolean,
    default: false,
  },
  secondary: {
    type: Boolean,
    default: false,
  },
  minor: {
    type: Boolean,
    default: false,
  },
  to: {
    type: String,
    default: null,
  },
  color: {
    type: String,
    default: null,
  },
  text: {
    type: String,
    default: null,
  },
  icon: {
    type: String,
    default: null,
  },
  iconRight: {
    type: Boolean,
    default: false,
  },
  onlyIcon: {
    type: Boolean,
    default: false,
  },
  onlyText: {
    type: Boolean,
    default: false,
  },
});

const i18n = useI18n();
const { $globals } = useNuxtApp();

const buttonOptions = {
  create: {
    text: i18n.t("general.create"),
    icon: $globals.icons.createAlt,
    color: "success",
  },
  update: {
    text: i18n.t("general.update"),
    icon: $globals.icons.edit,
    color: "success",
  },
  save: {
    text: i18n.t("general.save"),
    icon: $globals.icons.save,
    color: "success",
  },
  edit: {
    text: i18n.t("general.edit"),
    icon: $globals.icons.edit,
    color: "info",
  },
  delete: {
    text: i18n.t("general.delete"),
    icon: $globals.icons.delete,
    color: "error",
  },
  cancel: {
    text: i18n.t("general.cancel"),
    icon: $globals.icons.close,
    color: "grey",
  },
  download: {
    text: i18n.t("general.download"),
    icon: $globals.icons.download,
    color: "info",
  },
  onlyIcon: {
    text: null,
    icon: null,
    color: "success",
  },
  onlyText: {
    text: null,
    icon: null,
    color: "success",
  },
};

const btnAttrs = computed(() => {
  if (props.delete) {
    return buttonOptions.delete;
  }
  else if (props.update) {
    return buttonOptions.update;
  }
  else if (props.edit) {
    return buttonOptions.edit;
  }
  else if (props.cancel) {
    return buttonOptions.cancel;
  }
  else if (props.save) {
    return buttonOptions.save;
  }
  else if (props.download) {
    return buttonOptions.download;
  }
  else if (props.onlyIcon) {
    return buttonOptions.onlyIcon;
  }
  else if (props.onlyText) {
    return buttonOptions.onlyText;
  }
  return buttonOptions.create;
});

const buttonStyles = {
  defaults: { text: false, outlined: false },
  secondary: { text: false, outlined: true },
  minor: { text: true, outlined: false },
};

const btnStyle = computed(() => {
  if (props.secondary) {
    return buttonStyles.secondary;
  }
  if (props.minor || props.cancel) {
    return buttonStyles.minor;
  }
  return buttonStyles.defaults;
});

const api = useUserApi();
function downloadFile() {
  api.utils.download(props.downloadUrl);
}
</script>
