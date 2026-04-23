<template>
  <div>
    <v-radio-group v-model="contentMode" inline hide-details class="mb-2">
      <v-radio label="Custom Content" value="manual"></v-radio>
      <v-radio label="External URL" value="dynamic"></v-radio>
    </v-radio-group>

    <div v-if="contentMode === 'manual'">
      <InlineImageEditor
        v-if="isImageKind"
        :model-value="blobEditorContent"
        :label="label"
        :required="required"
        :description="description"
        v-model:comment="blobComment"
        :loading="loadingBlobContent || isUploading || isLoadingBlob"
        :error-message="errorMessage"
        :original-checksum="currentBlobChecksum"
        :original-comment="originalBlobComment"
        :original-url="originalUrl"
        @save="handleImageSave"
        @clear="handleRemove"
        @file-selected="handleFileSelected"
        @url-entered="handleUrlEntered"
        @use-original-url="handleUseOriginalUrl"
      />

      <InlineTextEditor
        v-else
        :model-value="blobEditorContent"
        :label="label"
        :required="required"
        :description="description"
        :file-type="textFileType"
        v-model:comment="blobComment"
        :loading="loadingBlobContent || isUploading || isLoadingBlob"
        :error-message="errorMessage"
        :original-checksum="currentBlobChecksum"
        :original-comment="originalBlobComment"
        :original-url="originalUrl"
        @save="handleTextSave"
        @clear="handleRemove"
        @file-selected="handleFileSelected"
        @url-entered="handleUrlEntered"
        @use-original-url="handleUseOriginalUrl"
      />

      <!-- Hidden file input -->
      <input
        ref="fileInputRef"
        type="file"
        :accept="acceptedTypes"
        style="display: none"
        @change="handleFileChange"
      />
    </div>

    <div v-else>
      <v-text-field
        v-model.trim="dynamicUrl"
        :label="label"
        :required="required"
        :rules="urlRules"
        :hint="description || ''"
        variant="outlined"
        density="compact"
        type="url"
        persistent-hint
        placeholder="Enter external URL"
        @update:model-value="handleDynamicUrlUpdate"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { formattedBytesSize } from '@/utils/format'
import constants from '@/constants'
import type { Config } from '@/config'
import { computed, ref, watch, inject } from 'vue'
import InlineTextEditor from '@/components/InlineTextEditor.vue'
import InlineImageEditor from '@/components/InlineImageEditor.vue'
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
  recipeName: string
  flagKey: string
}

const props = withDefaults(defineProps<Props>(), {
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
const userInput = ref<string>('')
const showBlobEditor = ref(false)
const blobEditorContent = ref('')
const loadingBlobContent = ref(false)
const blobComment = ref<string>('')
const originalBlobComment = ref<string>('')
const currentBlobId = ref<string | undefined>(undefined)
const currentBlobChecksum = ref<string | undefined>(undefined)
const isUploading = ref(false)
const isLoadingBlob = ref(false)
const originalUrl = ref<string | null>(props.modelValue || null)

const contentMode = ref<'manual' | 'dynamic'>('manual')
const dynamicUrl = ref<string>('')

const urlRules = [
  (value: unknown) => {
    if (props.required && (!value || value == '')) {
      return 'This field is required.'
    }
    if (value && typeof value === 'string' && value !== '') {
      try {
        new URL(value)
        return true
      } catch {
        return 'Please enter a valid URL.'
      }
    }
    return true
  },
]

const handleDynamicUrlUpdate = (value: string) => {
  emit('update:modelValue', value)
}

watch(contentMode, async (newMode) => {
  if (newMode === 'dynamic') {
    if (!dynamicUrl.value && props.modelValue) {
      dynamicUrl.value = props.modelValue
    }
    emit('update:modelValue', dynamicUrl.value)
  } else {
    emit('update:modelValue', originalUrl.value)

    const newValue = originalUrl.value
    if (!newValue) {
      userInput.value = ''
      errorMessage.value = ''
      hasError.value = false
      blobEditorContent.value = ''
    } else {
      if (newValue.startsWith('http://') || newValue.startsWith('https://')) {
        userInput.value = newValue
      }
      if (isImageKind.value) {
        await loadImageFromUrl(newValue)
      } else if (isTextKind.value) {
        await loadTextFromUrl(newValue)
      }
    }
  }
})

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

const convertFileToBase64 = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      if (typeof reader.result === 'string') {
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

const processText = async (text: string) => {
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

    blobEditorContent.value = text
    showBlobEditor.value = true
  } catch (error) {
    console.error('Failed to process text content:', error)
    errorMessage.value = 'Failed to process content. Please try again.'
    hasError.value = true
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
      await processText(text)
      return
    }
    // At this point, we are now dealing with images

    const base64 = await convertFileToBase64(file)

    // Add data URL prefix for image editor display
    blobEditorContent.value = `data:image/png;base64,${base64}`
    showBlobEditor.value = true
  } catch (error) {
    console.error('Failed to process file:', error)
    errorMessage.value = 'Failed to process file. Please try again.'
    hasError.value = true
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

const handleRemove = () => {
  userInput.value = ''
  blobEditorContent.value = ''
  errorMessage.value = ''
  hasError.value = false

  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
  emit('update:modelValue', null)
}

// InlineImageEditor event handlers
const handleFileSelected = async (file: File) => {
  await processFile(file)
}

const handleUrlEntered = async (url: string) => {
  if (isTextKind.value) {
    await loadTextFromUrl(url)
  } else {
    await loadImageFromUrl(url)
  }
}

const handleUseOriginalUrl = (url: string) => {
  emit('update:modelValue', url)
}

const loadImageFromUrl = async (url: string) => {
  loadingBlobContent.value = true
  errorMessage.value = ''
  hasError.value = false

  try {
    // Fetch blob metadata if URL
    if (url.startsWith('http://') || url.startsWith('https://')) {
      const blob = await fetchBlobByUrl(url)
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
      blobEditorContent.value = `data:image/png;base64,${url}`
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

const loadTextFromUrl = async (url: string) => {
  loadingBlobContent.value = true
  errorMessage.value = ''
  hasError.value = false

  try {
    // Fetch blob metadata if URL
    if (url.startsWith('http://') || url.startsWith('https://')) {
      const text = await fetchBlobByUrl(url, true)
      if (!text) {
        throw new Error('Failed to fetch blob content')
      }
      blobEditorContent.value = text
    } else {
      // Raw text content
      blobEditorContent.value = url
    }

    showBlobEditor.value = true
  } catch (error) {
    console.error('Failed to load text content:', error)
    errorMessage.value = 'Failed to load text file for editing'
    hasError.value = true
  } finally {
    loadingBlobContent.value = false
  }
}

const handleImageSave = async (imageData: string) => {
  if (!imageData || imageData.trim() === '' || imageData === 'data:,') {
    handleRemove()
    return
  }

  const base64Data = imageData.includes(',') ? imageData.split(',')[1] : imageData

  if (!base64Data || base64Data.trim() === '') {
    handleRemove()
    return
  }

  const success = await uploadBlob(base64Data)
  if (success) {
    blobEditorContent.value = imageData
  }
}

// Text editor functions
const textToBase64 = (text: string): string => {
  return btoa(text)
}

const handleTextSave = async (content: string) => {
  if (!content || content.trim() === '') {
    handleRemove()
    return
  }

  const base64Content = textToBase64(content)
  const success = await uploadBlob(base64Content)
  if (success) {
    blobEditorContent.value = content
  }
}

// Upload blob
const uploadBlob = async (base64Data: string) => {
  isUploading.value = true
  errorMessage.value = ''

  try {
    const newChecksum = await computeChecksumFromBase64(base64Data)

    if (newChecksum === currentBlobChecksum.value) {
      if (blobComment.value !== originalBlobComment.value) {
        if (!currentBlobId.value) {
          const newBlob = await blobStore.createBlob(props.recipeName, {
            flag_name: props.flagKey,
            kind: props.kind,
            data: base64Data,
            comments: blobComment.value || '',
          })

          if (newBlob) {
            currentBlobId.value = newBlob.id
            currentBlobChecksum.value = newBlob.checksum
            originalBlobComment.value = blobComment.value
            emit('update:modelValue', newBlob.url)
            return true
          } else {
            errorMessage.value = 'Failed to upload blob'
            return false
          }
        }

        const updatedBlob = await blobStore.updateBlob(currentBlobId.value, {
          comments: blobComment.value,
        })

        if (updatedBlob) {
          originalBlobComment.value = blobComment.value
          emit('update:modelValue', updatedBlob.url)
          return true
        } else {
          errorMessage.value = 'Failed to update blob comment'
          return false
        }
      } else {
        return true
      }
    } else {
      const blob = await blobStore.createBlob(props.recipeName, {
        flag_name: props.flagKey,
        kind: props.kind,
        data: base64Data,
        comments: blobComment.value || '',
      })

      if (blob) {
        currentBlobId.value = blob.id
        currentBlobChecksum.value = blob.checksum
        originalBlobComment.value = blobComment.value
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

async function fetchBlobByUrl(url: string, isText: true): Promise<string | undefined>
async function fetchBlobByUrl(url: string, isText?: false): Promise<Blob | undefined>
async function fetchBlobByUrl(url: string, isText = false): Promise<Blob | string | undefined> {
  isLoadingBlob.value = true
  errorMessage.value = ''

  try {
    const response = await fetch(url)
    if (!response.ok) {
      throw new Error(`Failed to fetch file: ${response.statusText}`)
    }

    const blob = await response.blob()
    const file = new File([blob], 'downloaded-file', { type: blob.type })
    const localChecksum = await computeChecksumFromFile(file)

    const backendBlob = await blobStore.fetchBlob(props.recipeName, localChecksum, props.flagKey)

    if (backendBlob) {
      currentBlobId.value = backendBlob.id
      currentBlobChecksum.value = localChecksum
      blobComment.value = backendBlob.comments || ''
      originalBlobComment.value = backendBlob.comments || ''
    } else {
      currentBlobId.value = undefined
      console.log('no file with matching checksum', localChecksum)
    }

    // Return text content for text files, blob for binary files
    if (isText) {
      return await blob.text()
    }
    return blob
  } catch (error) {
    console.error('Failed to fetch blob details:', error)
  } finally {
    isLoadingBlob.value = false
  }
}

// Watch for updates from parent
watch(
  () => props.modelValue,
  async (newValue, oldValue) => {
    if (newValue !== dynamicUrl.value) {
      dynamicUrl.value = newValue || ''
    }
    if (newValue !== originalUrl.value) {
      originalUrl.value = newValue || null
    }

    if (contentMode.value === 'dynamic') {
      return
    }

    if (!newValue && oldValue) {
      userInput.value = ''
      errorMessage.value = ''
      hasError.value = false
      blobEditorContent.value = ''
    } else if (newValue && newValue !== oldValue) {
      if (newValue.startsWith('http://') || newValue.startsWith('https://')) {
        userInput.value = newValue
      }
      if (isImageKind.value) {
        await loadImageFromUrl(newValue)
      } else if (isTextKind.value) {
        await loadTextFromUrl(newValue)
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
