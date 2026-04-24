<template>
  <div>
    <div v-if="label" class="text-caption text-grey-darken-1 mb-1">
      {{ label }}
    </div>
    <!-- Drop Zone / Preview Container -->
    <v-sheet
      :class="[
        'rounded',
        'overflow-hidden',
        'position-relative',
        {
          'border-primary': isDragging,
          'bg-primary-lighten-5': isDragging,
        },
      ]"
      :style="{
        border: isDragging
          ? '2px dashed rgb(var(--v-theme-primary))'
          : '2px dashed rgb(var(--v-border-color))',
        height: '250px',
        cursor: cropperActive ? 'default' : 'pointer',
      }"
      @click="handleContainerClick"
      @drop.prevent="handleDrop"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @dragenter.prevent="handleDragEnter"
      @paste="handlePaste"
      tabindex="0"
    >
      <!-- Empty State: Drop Zone -->
      <div
        v-if="!showPreview"
        class="d-flex flex-column align-center justify-center pa-8"
        style="pointer-events: none"
      >
        <v-icon size="48" color="grey-lighten-1">mdi-cloud-upload</v-icon>
        <p class="text-body-1 text-grey-darken-1 mt-3 mb-0 text-center">
          Drag & drop an image here
        </p>
        <p class="text-body-2 text-grey mt-2 mb-0 text-center">
          or click to browse, or paste (Ctrl+V)
        </p>
      </div>

      <!-- Preview State -->
      <div v-if="showPreview" class="d-flex flex-column" style="height: 100%">
        <!-- Image Workspace -->
        <v-sheet
          class="flex-1-1 position-relative d-flex align-center justify-center"
          style="overflow: hidden; min-height: 0"
        >
          <!-- Loading Overlay -->
          <div v-if="loading" class="d-flex flex-column align-center justify-center pa-8">
            <v-progress-circular indeterminate color="primary" size="48" />
            <p class="text-body-2 mt-3">Loading image...</p>
          </div>

          <div
            v-else-if="previewErrorMessage"
            class="w-100 h-100 d-flex align-center justify-center pa-4 text-error text-caption"
          >
            <v-icon size="small" class="mr-1">mdi-alert-circle</v-icon>
            {{ previewErrorMessage }}
          </div>

          <!-- Image/Cropper -->
          <div v-else class="w-100 h-100 d-flex align-center justify-center">
            <Cropper
              v-if="cropperActive"
              ref="cropperRef"
              :src="internalImageData"
              :stencil-props="{ aspectRatio: undefined }"
              :default-size="defaultCropperSize"
              image-restriction="fit-area"
              backgroundClass="cropper-background"
              foregroundClass="cropper-foreground"
              style="max-width: 100%; max-height: 100%"
              @change="handleCropperChange"
            />
            <img
              v-else
              :src="internalImageData"
              alt="Preview"
              style="max-width: 100%; max-height: 100%; object-fit: contain"
            />
            <div
              v-if="dimensionsText"
              class="position-absolute text-caption px-2 py-1 rounded"
              style="
                bottom: 8px;
                right: 8px;
                background: rgba(0, 0, 0, 0.6);
                color: white;
                z-index: 10;
                pointer-events: none;
              "
            >
              {{ dimensionsText }}
            </div>
          </div>

          <!-- Action Buttons -->
          <div
            v-if="!loading"
            class="position-absolute d-flex flex-column"
            style="top: 8px; right: 8px; z-index: 100; gap: 8px"
          >
            <template v-if="!previewErrorMessage">
              <v-btn
                v-if="!cropperActive && (hasUnsavedChanges || hasChanges)"
                icon
                size="small"
                color="success"
                @click.stop="handleSave"
                :loading="loading"
              >
                <v-icon>mdi-content-save</v-icon>
                <v-tooltip activator="parent" location="left">Save image</v-tooltip>
              </v-btn>
              <v-btn
                v-if="!cropperActive"
                icon
                size="small"
                color="primary"
                @click.stop="startCrop"
              >
                <v-icon>mdi-crop</v-icon>
                <v-tooltip activator="parent" location="left">Crop image</v-tooltip>
              </v-btn>
              <template v-if="cropperActive">
                <v-btn icon size="small" color="success" @click.stop="applyCrop">
                  <v-icon>mdi-check</v-icon>
                  <v-tooltip activator="parent" location="left">Apply Crop</v-tooltip>
                </v-btn>
                <v-btn icon size="small" color="warning" @click.stop="cancelCrop">
                  <v-icon>mdi-close</v-icon>
                  <v-tooltip activator="parent" location="left">Cancel Crop</v-tooltip>
                </v-btn>
              </template>
            </template>
            <v-btn icon size="small" color="error" @click.stop="handleClear">
              <v-icon>mdi-delete</v-icon>
              <v-tooltip activator="parent" location="left">Delete image</v-tooltip>
            </v-btn>
          </div>

          <!-- Cropper Controls Overlay -->
          <div
            v-if="cropperActive && !loading && !previewErrorMessage"
            class="position-absolute d-flex flex-column pa-1 rounded bg-surface"
            style="top: 8px; left: 8px; z-index: 100; gap: 4px; opacity: 0.9"
          >
            <div class="d-flex" style="gap: 4px">
              <v-btn
                icon="mdi-rotate-left"
                size="x-small"
                variant="text"
                @click.stop="rotate(-90)"
                title="Rotate Left"
              />
              <v-btn
                icon="mdi-rotate-right"
                size="x-small"
                variant="text"
                @click.stop="rotate(90)"
                title="Rotate Right"
              />
            </div>
            <div class="d-flex" style="gap: 4px">
              <v-btn
                icon="mdi-flip-horizontal"
                size="x-small"
                variant="text"
                @click.stop="flipHorizontal"
                title="Flip Horizontal"
              />
              <v-btn
                icon="mdi-flip-vertical"
                size="x-small"
                variant="text"
                @click.stop="flipVertical"
                title="Flip Vertical"
              />
            </div>
            <div class="d-flex" style="gap: 4px">
              <v-btn
                icon="mdi-magnify-plus"
                size="x-small"
                variant="text"
                @click.stop="zoomIn"
                title="Zoom In"
              />
              <v-btn
                icon="mdi-magnify-minus"
                size="x-small"
                variant="text"
                @click.stop="zoomOut"
                title="Zoom Out"
              />
            </div>
            <div class="d-flex justify-center" style="gap: 4px">
              <v-btn
                icon="mdi-restore"
                size="x-small"
                variant="text"
                @click.stop="resetCropper"
                title="Reset"
              />
            </div>
          </div>
        </v-sheet>
      </div>
    </v-sheet>

    <!-- Comment Field -->
    <div v-if="showPreview && !cropperActive && !previewErrorMessage" class="mt-2">
      <v-textarea
        :model-value="comment"
        @update:model-value="$emit('update:comment', $event)"
        label="Comment (optional)"
        variant="outlined"
        density="compact"
        rows="2"
        hide-details
      />
    </div>

    <!-- Description -->
    <div v-if="description" class="text-caption text-grey mt-2">
      {{ description }}
    </div>

    <!-- Error Message -->
    <div v-if="errorMessage" class="text-error text-caption mt-2">
      <v-icon size="small" class="mr-1">mdi-alert-circle</v-icon>
      {{ errorMessage }}
    </div>

    <!-- Hidden File Input -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      style="display: none"
      @change="handleFileChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'
import { computeChecksumFromBase64 } from '@/utils/checksum'

interface Props {
  modelValue?: string | null
  label?: string
  required?: boolean
  description?: string | null
  comment?: string
  loading?: boolean
  disabled?: boolean
  errorMessage?: string
  previewErrorMessage?: string
  originalChecksum?: string
  originalComment?: string
  originalUrl?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  modelValue: null,
  required: false,
  description: null,
  comment: '',
  loading: false,
  disabled: false,
  errorMessage: '',
  previewErrorMessage: '',
  originalChecksum: undefined,
  originalComment: '',
  originalUrl: null,
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:comment': [value: string]
  save: [imageData: string]
  clear: []
  'file-selected': [file: File]
  'url-entered': [url: string]
  'use-original-url': [url: string]
}>()

// Refs
const fileInputRef = ref<HTMLInputElement | null>(null)
const cropperRef = ref<InstanceType<typeof Cropper> | null>(null)
const isDragging = ref(false)
const internalErrorMessage = ref('')
const internalImageData = ref('')
const cropperActive = ref(false)
const imageDimensions = ref<{ width: number; height: number } | null>(null)
const croppedDimensions = ref<{ width: number; height: number } | null>(null)
const detectedMimeType = ref('image/png')
const hasUnsavedChanges = ref(false)
const localChecksum = ref<string | undefined>(undefined)

// Computed
const errorMessage = computed(() => props.errorMessage || internalErrorMessage.value)
const showPreview = computed(
  () => !!internalImageData.value || props.loading || !!props.previewErrorMessage,
)

const hasChanges = computed(() => {
  // Check if comment has changed
  if (props.comment !== props.originalComment) return true

  // Check if checksum has changed
  if (
    localChecksum.value &&
    props.originalChecksum &&
    localChecksum.value !== props.originalChecksum
  )
    return true

  // If there's new content but no original checksum, it's a new image
  if (!props.originalChecksum && internalImageData.value) return true

  return false
})

const dimensionsText = computed(() => {
  if (cropperActive.value && croppedDimensions.value) {
    return `${croppedDimensions.value.width} × ${croppedDimensions.value.height} px`
  } else if (imageDimensions.value) {
    return `${imageDimensions.value.width} × ${imageDimensions.value.height} px`
  }
  return ''
})

// Methods
const isValidUrl = (text: string): boolean => {
  try {
    const url = new URL(text)
    return url.protocol === 'http:' || url.protocol === 'https:'
  } catch {
    return false
  }
}

const detectMimeTypeFromDataUrl = (dataUrl: string): string => {
  const base64Data = dataUrl.split(',')[1]
  if (!base64Data) return 'image/png'

  try {
    const binaryString = atob(base64Data.substring(0, 100))
    const bytes = new Uint8Array(binaryString.length)
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i)
    }

    const header = Array.from(bytes.subarray(0, 4))
      .map((byte) => byte.toString(16).padStart(2, '0'))
      .join('')

    switch (header) {
      case '89504e47':
        return 'image/png'
      case '47494638':
        return 'image/gif'
      case 'ffd8ffe0':
      case 'ffd8ffe1':
      case 'ffd8ffe2':
      case 'ffd8ffe3':
      case 'ffd8ffe8':
        return 'image/jpeg'
      default:
        const match = dataUrl.match(/^data:(image\/[a-z]+);/)
        return match ? match[1] : 'image/png'
    }
  } catch {
    const match = dataUrl.match(/^data:(image\/[a-z]+);/)
    return match ? match[1] : 'image/png'
  }
}

const resetState = () => {
  internalImageData.value = ''
  cropperActive.value = false
  imageDimensions.value = null
  croppedDimensions.value = null
  hasUnsavedChanges.value = false
  internalErrorMessage.value = ''
  localChecksum.value = undefined
}

const loadImage = (dataUrl: string) => {
  internalImageData.value = dataUrl
  detectedMimeType.value = detectMimeTypeFromDataUrl(dataUrl)
  cropperActive.value = false
  hasUnsavedChanges.value = false
  internalErrorMessage.value = ''

  // Get image dimensions
  const img = new Image()
  img.onload = () => {
    imageDimensions.value = { width: img.width, height: img.height }
  }
  img.onerror = () => {
    resetState()
    internalErrorMessage.value = 'Failed to load image. Please try a different image or URL.'
  }
  img.src = dataUrl
}

// Watch for external changes
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue && newValue !== internalImageData.value) {
      loadImage(newValue)
    } else if (!newValue) {
      resetState()
    }
  },
  { immediate: true },
)

// Watch for changes in image data to compute checksum
watch(
  internalImageData,
  async (newContent) => {
    if (newContent) {
      const base64Data = newContent.includes(',') ? newContent.split(',')[1] : newContent
      if (base64Data) {
        localChecksum.value = await computeChecksumFromBase64(base64Data)

        // If checksum matches and comment is the same, emit to use original URL
        if (
          localChecksum.value &&
          props.originalChecksum &&
          localChecksum.value === props.originalChecksum &&
          props.comment === props.originalComment &&
          props.originalUrl
        ) {
          emit('use-original-url', props.originalUrl)
        }
      } else {
        localChecksum.value = undefined
      }
    } else {
      localChecksum.value = undefined
    }
  },
  { immediate: true },
)

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
  const target = event.target as HTMLInputElement
  const files = target.files

  if (!files || files.length === 0) return

  const file = files[0]
  await processFile(file)

  // Clear file input
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

const processFile = async (file: File) => {
  if (!file.type.startsWith('image/')) {
    internalErrorMessage.value = 'Please select an image file'
    return
  }

  try {
    const dataUrl = await convertFileToBase64(file)
    loadImage(dataUrl)
    hasUnsavedChanges.value = true
    emit('file-selected', file)
  } catch (error) {
    console.error('Failed to process file:', error)
    internalErrorMessage.value = 'Failed to process image file'
  }
}

const handleContainerClick = (event: MouseEvent) => {
  // Don't trigger file input if clicking on buttons, inputs, or when cropper is active
  if (
    cropperActive.value ||
    (event.target as HTMLElement).closest('button') ||
    (event.target as HTMLElement).closest('input') ||
    (event.target as HTMLElement).closest('textarea')
  ) {
    return
  }

  fileInputRef.value?.click()
}

const handleDragEnter = () => {
  if (cropperActive.value) return
  isDragging.value = true
}

const handleDragOver = () => {
  if (cropperActive.value) return
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = async (event: DragEvent) => {
  if (cropperActive.value) return
  isDragging.value = false

  const files = event.dataTransfer?.files
  if (!files || files.length === 0) return

  const file = files[0]
  await processFile(file)
}

const handlePaste = async (event: ClipboardEvent) => {
  if (cropperActive.value) return
  const clipboardData = event.clipboardData
  if (!clipboardData) return

  // Check for files first
  const files = clipboardData.files
  if (files && files.length > 0) {
    event.preventDefault()
    const file = files[0]
    await processFile(file)
    return
  }

  // Check for URL text
  const text = clipboardData.getData('text/plain')
  if (text && isValidUrl(text.trim())) {
    event.preventDefault()
    emit('url-entered', text.trim())
  }
}

const handleClear = () => {
  resetState()
  emit('clear')
}

const handleSave = () => {
  if (internalImageData.value) {
    emit('save', internalImageData.value)
    hasUnsavedChanges.value = false
  }
}

// Cropper functions
const defaultCropperSize = ({ imageSize }: { imageSize: { width: number; height: number } }) => {
  return {
    width: imageSize.width,
    height: imageSize.height,
  }
}

const handleCropperChange = (event: { coordinates?: { width: number; height: number } }) => {
  if (event.coordinates) {
    croppedDimensions.value = {
      width: Math.round(event.coordinates.width),
      height: Math.round(event.coordinates.height),
    }
  }
}

const startCrop = () => {
  cropperActive.value = true
}

const cancelCrop = () => {
  cropperActive.value = false
  croppedDimensions.value = null
  if (cropperRef.value) {
    cropperRef.value.reset()
  }
}

const applyCrop = async () => {
  if (!cropperRef.value) return

  try {
    const { canvas } = cropperRef.value.getResult()
    if (!canvas) {
      internalErrorMessage.value = 'Failed to process image'
      return
    }

    const croppedImageData = canvas.toDataURL(detectedMimeType.value)
    internalImageData.value = croppedImageData
    cropperActive.value = false
    hasUnsavedChanges.value = true

    // Update dimensions
    imageDimensions.value = { width: canvas.width, height: canvas.height }
    croppedDimensions.value = null
  } catch (error) {
    console.error('Error cropping image:', error)
    internalErrorMessage.value = 'Failed to crop image'
  }
}

const rotate = (angle: number) => {
  if (cropperRef.value) {
    cropperRef.value.rotate(angle)
  }
}

const flipHorizontal = () => {
  if (cropperRef.value) {
    cropperRef.value.flip(true, false)
  }
}

const flipVertical = () => {
  if (cropperRef.value) {
    cropperRef.value.flip(false, true)
  }
}

const zoomIn = () => {
  if (cropperRef.value) {
    cropperRef.value.zoom(1.2)
  }
}

const zoomOut = () => {
  if (cropperRef.value) {
    cropperRef.value.zoom(0.8)
  }
}

const resetCropper = () => {
  if (cropperRef.value) {
    cropperRef.value.reset()
  }
}
</script>

<style scoped>
/* Cropper styling */
:deep(.vue-handler) {
  background: rgb(var(--v-theme-primary));
  border-color: rgb(var(--v-theme-primary));
}

:deep(.vue-line) {
  border-color: rgb(var(--v-theme-primary));
}

:deep(.vue-simple-handler) {
  background: rgb(var(--v-theme-primary));
  border-color: rgb(var(--v-theme-primary));
}

:deep(.cropper-background) {
  background: white;
}

:deep(.cropper-foreground) {
  background: white;
}
</style>
