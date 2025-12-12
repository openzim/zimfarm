<template>
  <div>
    <div class="d-flex align-center">
      <v-text-field
        v-model="displayFileName"
        :label="label"
        density="compact"
        variant="outlined"
        readonly
        :hint="description ?? undefined"
        persistent-hint
        :hide-details="hasError ? false : 'auto'"
      >
        <template #append-inner>
          <v-btn
            v-if="modelValue && kind === 'css'"
            icon="mdi-pencil"
            size="x-small"
            variant="text"
            color="primary"
            @click="handleEditCss"
            title="Edit CSS"
          />
          <v-btn
            v-if="modelValue"
            icon="mdi-close"
            size="x-small"
            variant="text"
            color="error"
            @click="handleRemove"
          />
          <v-btn icon="mdi-paperclip" size="small" variant="text" @click="triggerFileInput" />
        </template>
      </v-text-field>
    </div>

    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      :accept="acceptedTypes"
      style="display: none"
      @change="handleFileChange"
    />

    <!-- Error messages -->
    <div v-if="errorMessage" class="text-error text-caption mt-2">
      {{ errorMessage }}
    </div>

    <!-- CSS Editor Dialog -->
    <CssEditorDialog
      v-if="kind === 'css'"
      v-model="showCssEditor"
      :css-content="cssEditorContent"
      :loading="loadingCssContent"
      @save="handleCssSave"
      @cancel="handleCssCancel"
    />
  </div>
</template>

<script setup lang="ts">
import { formattedBytesSize } from '@/utils/format'
import constants from '@/constants'
import type { Config } from '@/config'
import { computed, ref, watch, inject } from 'vue'
import CssEditorDialog from './CssEditorDialog.vue'

const config = inject<Config>(constants.config)
if (!config) {
  throw new Error('Config is not defined')
}

interface Props {
  modelValue: string | null | undefined
  label?: string
  kind?: 'image' | 'css'
  required?: boolean
  description?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  label: 'File',
  kind: 'image',
  required: false,
  description: null,
})

const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const errorMessage = ref<string>('')
const hasError = ref(false)
const currentFileName = ref<string>('')
const showCssEditor = ref(false)
const cssEditorContent = ref('')
const loadingCssContent = ref(false)

const acceptedTypes = computed(() => {
  if (props.kind === 'image') {
    return 'image/*'
  } else if (props.kind === 'css') {
    return '.css,text/css'
  }
  return '*'
})

const displayFileName = computed(() => {
  if (currentFileName.value) {
    return currentFileName.value
  }
  if (props.modelValue) {
    if (props.modelValue.startsWith('http://') || props.modelValue.startsWith('https://')) {
      return props.modelValue
    }
    if (props.kind === 'css') {
      return 'CSS file (base64)'
    }
    return 'Uploaded file (base64)'
  }
  return ''
})

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const convertFileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        resolve(reader.result)
      } else {
        reject(new Error('Failed to convert file to base64'))
      }
    }
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

const handleFileChange = async (event: Event) => {
  errorMessage.value = ''
  hasError.value = false

  const target = event.target as HTMLInputElement
  const files = target.files

  if (!files || files.length === 0) {
    return
  }

  const file = files[0]

  // Validate file size
  if (file.size > config.BLOB_MAX_SIZE) {
    errorMessage.value = `File size must be less than ${formattedBytesSize(config.BLOB_MAX_SIZE)}`
    hasError.value = true
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
    return
  }

  // Validate file type
  if (props.kind === 'image' && !file.type.startsWith('image/')) {
    errorMessage.value = 'File must be an image'
    hasError.value = true
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
    return
  }

  if (props.kind === 'css' && file.type !== 'text/css' && !file.name.endsWith('.css')) {
    errorMessage.value = 'File must be a CSS file'
    hasError.value = true
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
    return
  }

  try {
    // Store the filename
    currentFileName.value = file.name

    // Convert to base64
    const base64 = await convertFileToBase64(file)
    emit('update:modelValue', base64)

    // For CSS files, automatically open the editor
    if (props.kind === 'css') {
      cssEditorContent.value = base64ToText(base64)
      showCssEditor.value = true
    }
  } catch (error) {
    console.error('Failed to process file:', error)
    errorMessage.value = 'Failed to process file. Please try again.'
    hasError.value = true
    currentFileName.value = ''
    if (fileInputRef.value) {
      fileInputRef.value.value = ''
    }
  }
}

const handleRemove = () => {
  currentFileName.value = ''
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  emit('update:modelValue', null)
}

const base64ToText = (base64String: string): string => {
  // Remove data URL prefix if present
  const base64Data = base64String.includes(',') ? base64String.split(',')[1] : base64String

  try {
    return atob(base64Data)
  } catch (error) {
    console.error('Failed to decode base64:', error)
    return ''
  }
}

const textToBase64 = (text: string): string => {
  const encoded = btoa(text)
  return `data:text/css;base64,${encoded}`
}

const fetchCssFromUrl = async (url: string): Promise<string> => {
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch CSS: ${response.statusText}`)
    }
    return await response.text()
  } catch (error) {
    console.error('Error fetching CSS from URL:', error)
    throw error
  }
}

const handleEditCss = async () => {
  if (!props.modelValue) return

  loadingCssContent.value = true
  errorMessage.value = ''

  try {
    if (props.modelValue.startsWith('http://') || props.modelValue.startsWith('https://')) {
      cssEditorContent.value = await fetchCssFromUrl(props.modelValue)
    } else if (props.modelValue.startsWith('data:')) {
      cssEditorContent.value = base64ToText(props.modelValue)
    } else {
      // Assume it's already base64 without prefix
      cssEditorContent.value = base64ToText(props.modelValue)
    }

    showCssEditor.value = true
  } catch (error) {
    console.error('Failed to load CSS content:', error)
    errorMessage.value = 'Failed to load CSS content for editing'
    hasError.value = true
  } finally {
    loadingCssContent.value = false
  }
}

const handleCssSave = (content: string) => {
  // Convert edited CSS content back to base64
  const base64Content = textToBase64(content)
  emit('update:modelValue', base64Content)
  showCssEditor.value = false
}

const handleCssCancel = () => {
  showCssEditor.value = false
}

// Watch for URL updates from backend (after submission)
watch(
  () => props.modelValue,
  (newValue, oldValue) => {
    // Update display when backend returns a URL
    if (newValue && newValue !== oldValue) {
      if (newValue.startsWith('http://') || newValue.startsWith('https://')) {
        currentFileName.value = newValue
      }
    }
  },
  { immediate: true },
)
</script>
