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
        v-model="userInput"
        :label="label"
        density="compact"
        variant="outlined"
        :hint="description ?? undefined"
        persistent-hint
        :hide-details="hasError ? false : 'auto'"
        :class="{ 'drag-over': isDragging }"
        @paste="handlePaste"
        @blur="handleInputBlur"
        placeholder="Enter URL or drag and drop a file"
      >
        <template #append-inner>
          <v-progress-circular
            v-if="loadingBlobContent"
            indeterminate
            size="20"
            width="2"
            color="primary"
          />
          <v-btn
            v-else-if="modelValue && isImageKind"
            icon="mdi-image-edit"
            size="x-small"
            variant="text"
            color="primary"
            @click="handleEditImage"
            title="Edit Image/Illustration"
          />
          <v-btn
            v-else-if="modelValue && isTextKind"
            icon="mdi-pencil"
            size="x-small"
            variant="text"
            color="primary"
            @click="handleEditText"
            :title="`Edit ${kind === 'txt' ? 'Text' : kind.toUpperCase()}`"
          />
          <v-btn
            v-else-if="!modelValue && isTextKind"
            icon="mdi-pencil-plus"
            size="x-small"
            variant="text"
            color="primary"
            @click="handleCreateText"
            :title="`Create ${kind === 'txt' ? 'Text' : kind.toUpperCase()} File`"
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
      v-if="isImageKind"
      v-model="showBlobEditor"
      :image-data="blobEditorContent"
      v-model:comment="blobComment"
      :loading="loadingBlobContent || isUploading || isLoadingBlob"
      @save="handleImageSave"
      @cancel="handleBlobEditorCancel"
    />

    <!-- Text Editor Dialog -->
    <TextEditorDialog
      v-if="isTextKind"
      v-model="showBlobEditor"
      :text-content="blobEditorContent"
      :file-type="textFileType"
      v-model:comment="blobComment"
      :loading="loadingBlobContent || isUploading || isLoadingBlob"
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
import { computeChecksumFromBase64, computeChecksumFromFile } from '@/utils/checksum'
import { useBlobStore } from '@/stores/blob'

const config = inject<Config>(constants.config)
if (!config) {
  throw new Error('Config is not defined')
}

const TEXT_KINDS = ['css', 'html', 'txt'] as const

const IMAGE_KINDS = ['illustration', 'image'] as const

interface Props {
  modelValue: string | null | undefined
  label?: string
  kind?: 'image' | 'illustration' | 'css' | 'html' | 'txt'
  required?: boolean
  description?: string | null
  scheduleName: string
  flagKey: string
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

const blobStore = useBlobStore()

const fileInputRef = ref<HTMLInputElement | null>(null)
const errorMessage = ref<string>('')
const hasError = ref(false)
const currentFileName = ref<string>('')
const userInput = ref<string>('')
const showBlobEditor = ref(false)
const blobEditorContent = ref('')
const loadingBlobContent = ref(false)
const isDragging = ref(false)
const blobComment = ref<string>('')
const originalBlobComment = ref<string>('')
const currentBlobId = ref<string | undefined>(undefined)
const currentBlobChecksum = ref<string | undefined>(undefined)
const isUploading = ref(false)
const isLoadingBlob = ref(false)

const isTextKind = computed(() => TEXT_KINDS.includes(props.kind as (typeof TEXT_KINDS)[number]))

const isImageKind = computed(() => IMAGE_KINDS.includes(props.kind as (typeof IMAGE_KINDS)[number]))

const textFileType = computed(() => {
  return isTextKind.value ? (props.kind as 'css' | 'html' | 'txt') : 'txt'
})

const acceptedTypes = computed(() => {
  if (isImageKind.value) {
    return 'image/*'
  } else if (props.kind === 'css') {
    return '.css,text/css'
  } else if (props.kind === 'html') {
    return '.html,.htm,text/html'
  } else if (props.kind === 'txt') {
    return '.txt,text/plain'
  }
  return '*'
})

const isValidUrl = (text: string): boolean => {
  try {
    const url = new URL(text)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch {
    return false
  }
}

const triggerFileInput = () => {
  fileInputRef.value?.click()
}

const convertFileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === 'string') {
        // Remove data URL prefix (e.g., "data:image/png;base64,")
        const base64Data = reader.result.includes(',') ? reader.result.split(',')[1] : reader.result
        resolve(base64Data)
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

    currentFileName.value = filename
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
  if (isImageKind.value && !file.type.startsWith('image/')) {
    errorMessage.value = 'File must be an image/illustration'
    hasError.value = true
    return
  }

  // For text files, check MIME type first, fall back to extension
  // (MIME types can be unreliable depending on OS/browser)
  if (props.kind === 'css' && file.type !== 'text/css' && !file.name.endsWith('.css')) {
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

  if (props.kind === 'txt' && file.type !== 'text/plain' && !file.name.endsWith('.txt')) {
    errorMessage.value = 'File must be a TXT file'
    hasError.value = true
    return
  }

  try {
    // For text files (CSS, HTML, TXT), read as text and use processText for consistency
    if (isTextKind.value) {
      const text = await file.text()
      await processText(text, file.name)
      return
    }
    // At this point, we are now dealing with images

    currentFileName.value = file.name
    const base64 = await convertFileToBase64(file)

    // Add data URL prefix for image editor display
    blobEditorContent.value = `data:image/png;base64,${base64}`
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

const handleInputBlur = () => {
  // When user finishes typing/pasting, check if it's a URL
  const trimmedInput = userInput.value.trim()

  if (!trimmedInput) {
    // Empty input, clear everything
    handleRemove()
    return
  }

  if (isValidUrl(trimmedInput)) {
    // It's a valid URL, store it without opening editor
    currentFileName.value = trimmedInput
    emit('update:modelValue', trimmedInput)
    errorMessage.value = ''
    hasError.value = false
  } else if (isTextKind.value) {
    // For text kinds, treat non-URL input as text content to be edited
    // Don't automatically open editor, just keep the input
    errorMessage.value = 'Please use the pencil icon to create content or enter a valid URL'
    hasError.value = true
  } else {
    // For image kind, only URLs are valid for direct input
    errorMessage.value = 'Please enter a valid URL or use file upload'
    hasError.value = true
  }
}

const handlePaste = async (event: ClipboardEvent) => {
  const clipboardData = event.clipboardData
  if (!clipboardData) {
    return
  }

  // Check for files first
  const files = clipboardData.files
  if (files && files.length > 0) {
    event.preventDefault()
    const file = files[0]
    await processFile(file)
    return
  }

  // Get pasted text
  const text = clipboardData.getData('text/plain')
  if (!text) {
    return
  }

  // Check if it's a URL
  if (isValidUrl(text.trim())) {
    // It's a URL, allow default paste behavior
    errorMessage.value = ''
    hasError.value = false
    return
  }

  // For non-URL text content in text kinds, open editor immediately
  if (isTextKind.value) {
    event.preventDefault()
    errorMessage.value = ''
    hasError.value = false
    let extension = 'txt'
    if (props.kind === 'css') extension = 'css'
    else if (props.kind === 'html') extension = 'html'
    await processText(text, `pasted-content.${extension}`)
    return
  }

  // For image kind with non-URL text, prevent paste and show error
  event.preventDefault()
  errorMessage.value = 'Please enter a valid URL or use file upload'
  hasError.value = true
}

const handleRemove = () => {
  currentFileName.value = ''
  userInput.value = ''
  errorMessage.value = ''
  hasError.value = false
  blobComment.value = ''
  originalBlobComment.value = ''
  currentBlobId.value = undefined
  currentBlobChecksum.value = undefined
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
  return btoa(text)
}

const handleEditImage = async () => {
  if (!props.modelValue) return

  loadingBlobContent.value = true
  errorMessage.value = ''
  blobEditorContent.value = ''

  try {
    // Fetch blob metadata if URL
    if (props.modelValue.startsWith('http://') || props.modelValue.startsWith('https://')) {
      const blob = await fetchBlobByUrl(props.modelValue)
      if (!blob) {
        throw new Error('Failed to fetch blob content')
      }
      const reader = new FileReader()
      blobEditorContent.value = await new Promise((resolve, reject) => {
        reader.onload = () => resolve(reader.result as string)
        reader.onerror = reject
        reader.readAsDataURL(blob)
      })
    } else {
      // Raw base64 - add data URL prefix for image editor
      blobEditorContent.value = `data:image/png;base64,${props.modelValue}`
    }

    showBlobEditor.value = true
  } catch (error) {
    console.error('Failed to load image content:', error)
    errorMessage.value = 'Failed to load image/illustration for editing'
    hasError.value = true
  } finally {
    loadingBlobContent.value = false
  }
}

const handleEditText = async () => {
  if (!props.modelValue) return

  loadingBlobContent.value = true
  errorMessage.value = ''
  blobEditorContent.value = ''

  try {
    if (props.modelValue.startsWith('http://') || props.modelValue.startsWith('https://')) {
      // Fetch blob metadata first
      const blob = await fetchBlobByUrl(props.modelValue)
      if (!blob) {
        throw new Error('Failed to fetch blob content')
      }
      blobEditorContent.value = await blob.text()
    } else {
      blobEditorContent.value = base64ToText(props.modelValue)
    }

    showBlobEditor.value = true
  } catch (error) {
    console.error('Failed to load text content:', error)
    errorMessage.value = 'Failed to load text for editing'
    hasError.value = true
  } finally {
    loadingBlobContent.value = false
  }
}

const handleCreateText = () => {
  // Initialize with empty content for creating a new text blob
  blobEditorContent.value = ''
  blobComment.value = ''
  originalBlobComment.value = ''
  errorMessage.value = ''
  showBlobEditor.value = true
}

const uploadBlob = async (base64Data: string) => {
  isUploading.value = true
  errorMessage.value = ''

  try {
    // Compute checksum of new data
    const newChecksum = await computeChecksumFromBase64(base64Data)

    if (newChecksum === currentBlobChecksum.value) {
      if (blobComment.value !== originalBlobComment.value) {
        if (!currentBlobId.value) {
          // No existing blob, create new one
          const newBlob = await blobStore.createBlob(props.scheduleName, {
            flag_name: props.flagKey,
            kind: props.kind,
            data: base64Data,
            comments: blobComment.value || '',
          })

          if (newBlob) {
            currentBlobId.value = newBlob.id
            currentBlobChecksum.value = newBlob.checksum
            originalBlobComment.value = blobComment.value
            currentFileName.value = newBlob.url
            emit('update:modelValue', newBlob.url)
            return true
          } else {
            errorMessage.value = 'Failed to upload blob'
            return false
          }
        }
        // Only comment changed, update it
        const updatedBlob = await blobStore.updateBlob(currentBlobId.value, {
          comments: blobComment.value,
        })

        if (updatedBlob) {
          originalBlobComment.value = blobComment.value
          currentFileName.value = updatedBlob.url
          emit('update:modelValue', updatedBlob.url)
          return true
        } else {
          errorMessage.value = 'Failed to update blob comment'
          return false
        }
      } else {
        // Nothing changed at all, just return success without API call
        return true
      }
    } else {
      // Data changed, create new blob backend will handle duplicate detection
      const blob = await blobStore.createBlob(props.scheduleName, {
        flag_name: props.flagKey,
        kind: props.kind,
        data: base64Data,
        comments: blobComment.value || '',
      })

      if (blob) {
        currentBlobId.value = blob.id
        currentBlobChecksum.value = blob.checksum
        originalBlobComment.value = blobComment.value
        currentFileName.value = blob.url
        emit('update:modelValue', blob.url)
        return true
      } else {
        errorMessage.value = 'Failed to upload blob'
        return false
      }
    }
  } catch (error) {
    console.error('Failed to upload blob:', error)
    errorMessage.value = 'An error occurred while uploading'
    return false
  } finally {
    isUploading.value = false
  }
}

const handleImageSave = async (imageData: string) => {
  // Check if image data is empty
  if (!imageData || imageData.trim() === '' || imageData === 'data:,') {
    handleRemove()
    showBlobEditor.value = false
    return
  }

  const base64Data = imageData.includes(',') ? imageData.split(',')[1] : imageData

  // Check if base64 data is empty after removing prefix
  if (!base64Data || base64Data.trim() === '') {
    handleRemove()
    showBlobEditor.value = false
    return
  }

  const success = await uploadBlob(base64Data)
  if (success) {
    showBlobEditor.value = false
  }
}

const handleTextSave = async (content: string) => {
  // Check if content is empty
  if (!content || content.trim() === '') {
    handleRemove()
    showBlobEditor.value = false
    return
  }

  // Convert edited text content to raw base64
  const base64Content = textToBase64(content)

  const success = await uploadBlob(base64Content)
  if (success) {
    showBlobEditor.value = false
  }
}

const handleBlobEditorCancel = () => {
  showBlobEditor.value = false
}

// Fetch blob details when URL is provided
const fetchBlobByUrl = async (url: string) => {
  isLoadingBlob.value = true
  errorMessage.value = ''

  try {
    // First, download the file and compute checksum locally
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.statusText}`)
    }

    const blob = await response.blob()
    // Convert Blob to File for checksum computation
    const file = new File([blob], 'downloaded-file', { type: blob.type })
    const localChecksum = await computeChecksumFromFile(file)

    // Then fetch blob metadata from backend to see if it exists
    const backendBlob = await blobStore.fetchBlob(props.scheduleName, localChecksum, props.flagKey)

    if (backendBlob) {
      // Blob exists in backend, use its ID and comments but keep local checksum
      currentBlobId.value = backendBlob.id
      currentBlobChecksum.value = localChecksum
      blobComment.value = backendBlob.comments || ''
      originalBlobComment.value = backendBlob.comments || ''
      currentFileName.value = backendBlob.url
    } else {
      // Blob not found in backend, but we still have the local checksum
      currentFileName.value = url
      currentBlobId.value = undefined
      currentBlobChecksum.value = localChecksum
      blobComment.value = ''
      originalBlobComment.value = ''
    }
    return blob
  } catch (error) {
    console.error('Failed to fetch blob details:', error)
    // If fetch fails, just display the URL without blob metadata
    currentFileName.value = url
    currentBlobId.value = undefined
    currentBlobChecksum.value = undefined
    blobComment.value = ''
    originalBlobComment.value = ''
  } finally {
    isLoadingBlob.value = false
  }
}

// Watch for updates from parent (backend URLs or resets)
watch(
  () => props.modelValue,
  async (newValue, oldValue) => {
    if (!newValue && oldValue) {
      // Clear internal state when value is reset to null/undefined
      currentFileName.value = ''
      userInput.value = ''
      errorMessage.value = ''
      hasError.value = false
      blobEditorContent.value = ''
      blobComment.value = ''
      originalBlobComment.value = ''
      currentBlobId.value = undefined
      currentBlobChecksum.value = undefined
    } else if (newValue && newValue !== oldValue) {
      // Update userInput when modelValue changes from parent
      if (newValue.startsWith('http://') || newValue.startsWith('https://')) {
        userInput.value = newValue
        currentFileName.value = newValue
      }
    }
  },
  { immediate: true },
)

// Sync userInput with currentFileName for display
watch(currentFileName, (newValue) => {
  if (newValue && !userInput.value) {
    userInput.value = newValue
  }
})
</script>

<style scoped>
.drag-over :deep(.v-field) {
  border: 2px dashed rgb(var(--v-theme-primary));
  background-color: rgba(var(--v-theme-primary), 0.05);
}
</style>
