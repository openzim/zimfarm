<template>
  <div>
    <div
      class="d-flex align-center"
      @drop.prevent="handleDrop"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @dragenter.prevent="handleDragEnter"
    >
      <v-text-field
        v-model="displayFileName"
        :label="label"
        density="compact"
        variant="outlined"
        :hint="description ?? undefined"
        persistent-hint
        :hide-details="hasError ? false : 'auto'"
        :class="{ 'drag-over': isDragging }"
        @beforeinput="handleBeforeInput"
        @paste="handlePaste"
      >
        <template #append-inner>
          <v-btn
            v-if="modelValue && kind === 'image'"
            icon="mdi-image-edit"
            size="x-small"
            variant="text"
            color="primary"
            @click="handleEditImage"
            title="Edit Image"
          />
          <v-btn
            v-if="modelValue && (kind === 'css' || kind === 'html')"
            icon="mdi-pencil"
            size="x-small"
            variant="text"
            color="primary"
            @click="handleEditText"
            :title="`Edit ${kind.toUpperCase()}`"
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

    <!-- Image Editor Dialog -->
    <ImageEditorDialog
      v-if="kind === 'image'"
      v-model="showBlobEditor"
      :image-data="blobEditorContent"
      :loading="loadingBlobContent"
      @save="handleImageSave"
      @cancel="handleBlobEditorCancel"
    />

    <!-- Text Editor Dialog -->
    <TextEditorDialog
      v-if="kind === 'css' || kind === 'html'"
      v-model="showBlobEditor"
      :text-content="blobEditorContent"
      :file-type="kind"
      :loading="loadingBlobContent"
      @save="handleTextSave"
      @cancel="handleBlobEditorCancel"
    />
  </div>
</template>

<script setup lang="ts">
import { formattedBytesSize } from '@/utils/format'
import constants from '@/constants'
import type { Config } from '@/config'
import { computed, ref, watch, inject } from 'vue'
import TextEditorDialog from './TextEditorDialog.vue'
import ImageEditorDialog from './ImageEditorDialog.vue'
import { computeChecksumFromBase64 } from '@/utils/checksum'

const config = inject<Config>(constants.config)
if (!config) {
  throw new Error('Config is not defined')
}

interface Props {
  modelValue: string | null | undefined
  label?: string
  kind?: 'image' | 'css' | 'html'
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
  'checksum-computed': [checksum: string | null]
}>()

const fileInputRef = ref<HTMLInputElement | null>(null)
const errorMessage = ref<string>('')
const hasError = ref(false)
const currentFileName = ref<string>('')
const showBlobEditor = ref(false)
const blobEditorContent = ref('')
const loadingBlobContent = ref(false)
const isDragging = ref(false)

const acceptedTypes = computed(() => {
  if (props.kind === 'image') {
    return 'image/*'
  } else if (props.kind === 'css') {
    return '.css,text/css'
  } else if (props.kind === 'html') {
    return '.html,.htm,text/html'
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

const processText = async (text: string, filename: string) => {
  errorMessage.value = ''
  hasError.value = false

  try {
    // Validate size
    const textSize = new Blob([text]).size
    if (textSize > config.BLOB_MAX_SIZE) {
      errorMessage.value = `Content size must be less than ${formattedBytesSize(config.BLOB_MAX_SIZE)}`
      hasError.value = true
      return
    }

    const base64Content = textToBase64(text)
    try {
      const checksum = await computeChecksumFromBase64(base64Content)
      emit('checksum-computed', checksum)
    } catch (error) {
      console.error('Failed to compute checksum:', error)
      emit('checksum-computed', null)
    }

    currentFileName.value = filename
    emit('update:modelValue', base64Content)
    blobEditorContent.value = text
    showBlobEditor.value = true
  } catch (error) {
    console.error('Failed to process text content:', error)
    errorMessage.value = 'Failed to process content. Please try again.'
    hasError.value = true
    currentFileName.value = ''
  }
}

const processFile = async (file: File) => {
  errorMessage.value = ''
  hasError.value = false

  // Validate file size
  if (file.size > config.BLOB_MAX_SIZE) {
    errorMessage.value = `File size must be less than ${formattedBytesSize(config.BLOB_MAX_SIZE)}`
    hasError.value = true
    return
  }

  // Validate file type
  if (props.kind === 'image' && !file.type.startsWith('image/')) {
    errorMessage.value = 'File must be an image'
    hasError.value = true
    return
  }

  if (props.kind === 'css' && file.type !== 'text/css') {
    errorMessage.value = 'File must be a CSS file'
    hasError.value = true
    return
  }

  if (
    props.kind === 'html' &&
    file.type !== 'text/html' &&
    !file.name.endsWith('.html') &&
    !file.name.endsWith('.htm')
  ) {
    errorMessage.value = 'File must be an HTML file'
    hasError.value = true
    return
  }

  try {
    // For CSS files, read as text
    // For text files (CSS, HTML), read as text and use processText for consistency
    if (props.kind === 'css' || props.kind === 'html') {
      const text = await file.text()
      await processText(text, file.name)
      return
    }
    // At this point, we are now dealing with images

    currentFileName.value = file.name
    const base64 = await convertFileToBase64(file)

    try {
      const checksum = await computeChecksumFromBase64(base64)
      emit('checksum-computed', checksum)
    } catch (error) {
      console.error('Failed to compute checksum:', error)
      emit('checksum-computed', null)
    }

    emit('update:modelValue', base64)
    blobEditorContent.value = base64
    showBlobEditor.value = true
  } catch (error) {
    console.error('Failed to process file:', error)
    errorMessage.value = 'Failed to process file. Please try again.'
    hasError.value = true
    currentFileName.value = ''
  }
}

const handleFileChange = async (event: Event) => {
  const target = event.target as HTMLInputElement
  const files = target.files

  if (!files || files.length === 0) {
    return
  }

  const file = files[0]
  await processFile(file)

  // Clear file input
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const handleDragEnter = () => {
  isDragging.value = true
}

const handleDragOver = () => {
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = async (event: DragEvent) => {
  isDragging.value = false

  const files = event.dataTransfer?.files
  if (!files || files.length === 0) {
    return
  }

  const file = files[0]
  await processFile(file)
}

const handleBeforeInput = (event: InputEvent) => {
  // Allow paste operations
  if (event.inputType === 'insertFromPaste') {
    return
  }
  // Prevent all other input (typing, etc.)
  event.preventDefault()
}

const handlePaste = async (event: ClipboardEvent) => {
  event.preventDefault()

  errorMessage.value = ''
  hasError.value = false

  const clipboardData = event.clipboardData
  if (!clipboardData) {
    return
  }

  // Check for files first
  const files = clipboardData.files
  if (files && files.length > 0) {
    const file = files[0]
    await processFile(file)
    return
  }

  // Handle text content for CSS
  // Handle text content for CSS/HTML - use processText directly
  if (props.kind === 'css' || props.kind === 'html') {
    const text = clipboardData.getData('text/plain')
    if (text) {
      const extension = props.kind === 'css' ? 'css' : 'html'
      await processText(text, `pasted-content.${extension}`)
      return
    }
  }
}

const handleRemove = () => {
  currentFileName.value = ''
  errorMessage.value = ''
  hasError.value = false
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  emit('checksum-computed', null)
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
  const mimeType = props.kind === 'html' ? 'text/html' : 'text/css'
  return `data:${mimeType};base64,${encoded}`
}

const fetchTextFromUrl = async (url: string): Promise<string> => {
  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch content: ${response.statusText}`)
    }
    return await response.text()
  } catch (error) {
    console.error('Error fetching text from URL:', error)
    throw error
  }
}

const handleEditImage = async () => {
  if (!props.modelValue) return

  loadingBlobContent.value = true
  errorMessage.value = ''

  try {
    if (props.modelValue.startsWith('http://') || props.modelValue.startsWith('https://')) {
      // For URLs, we need to fetch and convert to base64
      const response = await fetch(props.modelValue)
      const blob = await response.blob()
      const reader = new FileReader()
      blobEditorContent.value = await new Promise((resolve, reject) => {
        reader.onload = () => resolve(reader.result as string)
        reader.onerror = reject
        reader.readAsDataURL(blob)
      })
    } else {
      // Already base64
      blobEditorContent.value = props.modelValue
    }

    showBlobEditor.value = true
  } catch (error) {
    console.error('Failed to load image content:', error)
    errorMessage.value = 'Failed to load image for editing'
    hasError.value = true
  } finally {
    loadingBlobContent.value = false
  }
}

const handleEditText = async () => {
  if (!props.modelValue) return

  loadingBlobContent.value = true
  errorMessage.value = ''

  try {
    if (props.modelValue.startsWith('http://') || props.modelValue.startsWith('https://')) {
      blobEditorContent.value = await fetchTextFromUrl(props.modelValue)
    } else if (props.modelValue.startsWith('data:')) {
      blobEditorContent.value = base64ToText(props.modelValue)
    } else {
      // Assume it's already base64 without prefix
      blobEditorContent.value = base64ToText(props.modelValue)
    }

    showBlobEditor.value = true
  } catch (error) {
    console.error('Failed to load text content:', error)
    errorMessage.value = 'Failed to load content for editing'
    hasError.value = true
  } finally {
    loadingBlobContent.value = false
  }
}

const handleBlobSave = async (base64Data: string) => {
  // Compute checksum and emit
  try {
    const checksum = await computeChecksumFromBase64(base64Data)
    emit('checksum-computed', checksum)
  } catch (error) {
    console.error('Failed to compute checksum:', error)
    emit('checksum-computed', null)
  }

  emit('update:modelValue', base64Data)
}

const handleImageSave = async (imageData: string) => {
  await handleBlobSave(imageData)
  showBlobEditor.value = false
}

const handleTextSave = async (content: string) => {
  // Convert edited text content back to base64
  const base64Content = textToBase64(content)
  await handleBlobSave(base64Content)
  showBlobEditor.value = false
}

const handleBlobEditorCancel = () => {
  showBlobEditor.value = false
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

<style scoped>
.drag-over :deep(.v-field) {
  border: 2px dashed rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
