<template>
  <div class="code-editor-wrapper" :style="{ height: height }">
    <highlightjs
      :language="highlightLanguage"
      :code="highlightedCode"
      class="code-highlight-backdrop"
    />
    <textarea
      v-model="internalValue"
      class="code-textarea"
      :class="{ 'readonly-textarea': readonly }"
      :placeholder="placeholder"
      :readonly="readonly"
      spellcheck="false"
      @scroll="handleScroll"
      @input="handleInput"
    ></textarea>
  </div>
</template>

<script setup lang="ts">
import type { TextKind } from '@/utils/blob'
import { ref, computed, watch } from 'vue'

interface Props {
  modelValue: string
  fileType?: TextKind
  readonly?: boolean
  height?: string
  placeholder?: string
}

const props = withDefaults(defineProps<Props>(), {
  fileType: 'txt',
  readonly: false,
  height: '500px',
  placeholder: 'Enter your code here...',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const internalValue = ref(props.modelValue)

const highlightLanguage = computed(() => {
  switch (props.fileType) {
    case 'html':
      return 'html'
    case 'css':
      return 'css'
    case 'txt':
    default:
      return 'plaintext'
  }
})

// Ensures that trailing newlines are rendered correctly in the highlight backdrop
// to maintain vertical synchronization with the textarea.
const highlightedCode = computed(() => {
  const code = internalValue.value || ' '
  return code.endsWith('\n') ? code + '\n' : code
})

const handleScroll = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  const backdrop = target.previousElementSibling
  if (backdrop) {
    backdrop.scrollTop = target.scrollTop
    backdrop.scrollLeft = target.scrollLeft
  }
}

const handleInput = () => {
  if (!props.readonly) {
    emit('update:modelValue', internalValue.value)
  }
}

watch(
  () => props.modelValue,
  (newValue) => {
    internalValue.value = newValue
  },
)
</script>

<style scoped>
.code-editor-wrapper {
  position: relative;
  width: 100%;
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
  border-radius: 4px;
  overflow: hidden;
}

.code-highlight-backdrop {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  overflow-y: scroll; /* Force vertical scrollbar to ensure layout match with textarea */
  overflow-x: hidden; /* Hide horizontal scrollbar to remove unused bottom space */
  pointer-events: none;
  margin: 0;
  padding: 12px; /* Must match textarea padding */
  background: transparent !important;
  box-sizing: border-box;
  white-space: pre-wrap;
  word-wrap: break-word;
}

/* Ensure any nested pre elements (if any) don't add extra margin/padding */
.code-highlight-backdrop :deep(pre) {
  margin: 0;
  padding: 0;
  height: 100%;
  background: transparent !important;
  border-radius: 0;
}

.code-highlight-backdrop :deep(code) {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  padding: 0 !important; /* Override highlight.js theme padding */
  background: transparent !important;
  font-variant-ligatures: none;
  letter-spacing: normal;
}

.code-textarea {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  padding: 12px; /* Must match backdrop padding */
  margin: 0;
  border: none;
  outline: none;
  background: transparent;
  color: transparent;
  caret-color: rgb(var(--v-theme-on-surface));
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  word-wrap: break-word;
  resize: none;
  overflow-y: scroll; /* Force vertical scrollbar to ensure layout match with backdrop */
  overflow-x: hidden;
  box-sizing: border-box;
  font-variant-ligatures: none;
  letter-spacing: normal;
}

.code-textarea.readonly-textarea {
  cursor: default;
}

.code-textarea::placeholder {
  color: rgba(var(--v-theme-on-surface), 0.38);
}

.code-textarea:focus {
  outline: none;
}

/* Force highlight.js backgrounds to be transparent to avoid white box in dark mode */
.code-highlight-backdrop :deep(.hljs) {
  background: transparent !important;
  padding: 0 !important; /* Ensure no extra padding from theme on .hljs class */
}
</style>
