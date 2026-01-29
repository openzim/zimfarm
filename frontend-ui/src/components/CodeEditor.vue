<template>
  <div class="code-editor-wrapper" :style="{ height: height }">
    <highlightjs
      :language="highlightLanguage"
      :code="modelValue || ' '"
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
      ref="textareaRef"
    ></textarea>
  </div>
</template>

<script setup lang="ts">
import type { TextKind } from '@/utils/blob'
import { ref, computed, watch, watchEffect } from 'vue'
import { useTheme } from 'vuetify'

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
const textareaRef = ref<HTMLTextAreaElement | null>(null)

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

const theme = useTheme()
const isDark = computed(() => theme.global.current.value.dark)

function setHljsThemeLink(href: string) {
  const id = 'hljs-theme'
  let link = document.getElementById(id) as HTMLLinkElement | null
  if (!link) {
    link = document.createElement('link')
    link.id = id
    link.rel = 'stylesheet'
    document.head.appendChild(link)
  }
  if (link.href !== href) {
    link.href = href
  }
}

watchEffect(() => {
  const href = isDark.value
    ? 'https://cdn.jsdelivr.net/npm/highlight.js@11.11.1/styles/github-dark.css'
    : 'https://cdn.jsdelivr.net/npm/highlight.js@11.11.1/styles/github.css'
  setHljsThemeLink(href)
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

defineExpose({
  textareaRef,
})
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
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  overflow: auto;
  pointer-events: none;
  margin: 0;
}

.code-highlight-backdrop :deep(pre) {
  margin: 0;
  padding: 12px;
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
}

.code-textarea {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  padding: 12px;
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
  overflow: auto;
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
}
</style>
