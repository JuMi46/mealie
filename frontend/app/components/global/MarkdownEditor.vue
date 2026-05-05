<template>
  <div>
    <div
      v-if="displayPreview"
      class="d-flex justify-end"
    >
      <BaseButtonGroup
        :buttons="[
          {
            icon: previewState ? $globals.icons.edit : $globals.icons.eye,
            text: previewState ? $t('general.edit') : $t('markdown-editor.preview-markdown-button-label'),
            event: 'toggle',
          },
        ]"
        @toggle="previewState = !previewState"
      />
    </div>
    <v-textarea
      v-if="!previewState"
      ref="textareaRef"
      v-bind="textarea"
      v-model="modelValue"
      :class="label == '' ? '' : 'mt-5'"
      :label="label"
      auto-grow
      density="compact"
      rows="4"
      variant="underlined"
      @focus="emitSelection"
      @keyup="emitSelection"
      @mouseup="emitSelection"
      @select="emitSelection"
    />
    <SafeMarkdown
      v-else
      :source="modelValue"
    />
  </div>
</template>

<script setup lang="ts">
interface TextSelectionState {
  selectedText: string;
  selectionStart: number;
  selectionEnd: number;
}

const props = defineProps({
  label: {
    type: String,
    default: "",
  },
  preview: {
    type: Boolean,
    default: undefined,
  },
  displayPreview: {
    type: Boolean,
    default: true,
  },
  textarea: {
    type: Object as () => unknown,
    default: () => ({}),
  },
});

const emit = defineEmits<{
  (e: "input:preview", value: boolean): void;
  (e: "selection-change", value: TextSelectionState | null): void;
}>();

const modelValue = defineModel<string>("modelValue");
const textareaRef = ref<{ $el?: HTMLElement } | null>(null);

const fallbackPreview = ref(false);
const previewState = computed({
  get: () => props.preview ?? fallbackPreview.value,
  set: (val: boolean) => {
    if (props.preview) {
      emit("input:preview", val);
    }
    else {
      fallbackPreview.value = val;
    }
  },
});

function getTextareaElement() {
  return textareaRef.value?.$el?.querySelector("textarea") ?? null;
}

function emitSelection(event?: Event) {
  const textarea = event?.target instanceof HTMLTextAreaElement
    ? event.target
    : getTextareaElement();

  if (!textarea) {
    emit("selection-change", null);
    return;
  }

  emit("selection-change", {
    selectedText: textarea.value.slice(textarea.selectionStart, textarea.selectionEnd),
    selectionStart: textarea.selectionStart,
    selectionEnd: textarea.selectionEnd,
  });
}
</script>
