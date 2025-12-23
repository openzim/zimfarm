<template>
  <v-dialog v-model="isOpen" max-width="900" persistent scrollable>
    <v-card>
      <v-card-title class="text-h6 bg-primary d-flex align-center">
        <v-icon class="mr-2">mdi-image-edit</v-icon>
        Edit Image

        <template v-if="imageLoaded">
          <v-divider vertical class="mx-3" />

          <!-- Rotation controls -->
          <v-btn
            icon="mdi-rotate-left"
            size="x-small"
            variant="text"
            @click="rotate(-90)"
            title="Rotate Left 90°"
          />
          <v-btn
            icon="mdi-rotate-right"
            size="x-small"
            variant="text"
            @click="rotate(90)"
            title="Rotate Right 90°"
          />

          <v-divider vertical class="mx-2" />

          <!-- Flip controls -->
          <v-btn
            icon="mdi-flip-horizontal"
            size="x-small"
            variant="text"
            @click="flipHorizontal"
            title="Flip Horizontal"
          />
          <v-btn
            icon="mdi-flip-vertical"
            size="x-small"
            variant="text"
            @click="flipVertical"
            title="Flip Vertical"
          />

          <v-divider vertical class="mx-2" />

          <!-- Zoom controls -->
          <v-btn
            icon="mdi-magnify-minus"
            size="x-small"
            variant="text"
            @click="zoomOut"
            title="Zoom Out"
          />
          <v-btn
            icon="mdi-magnify-plus"
            size="x-small"
            variant="text"
            @click="zoomIn"
            title="Zoom In"
          />

          <v-divider vertical class="mx-2" />

          <!-- Reset -->
          <v-btn icon="mdi-restore" size="x-small" variant="text" @click="reset" title="Reset" />

          <!-- Image dimensions info -->
          <div v-if="croppedDimensions" class="text-caption text-white ml-3">
            {{ croppedDimensions.width }} × {{ croppedDimensions.height }} px
          </div>
        </template>

        <v-spacer />
        <v-btn icon="mdi-close" variant="text" @click="handleCancel" size="small" />
      </v-card-title>

      <div class="pa-4 pb-0">
        <v-alert type="info" variant="tonal" density="compact">
          <template #prepend>
            <v-icon>mdi-information</v-icon>
          </template>
          Modifying the image or comment may create a new blob and update the URL.
        </v-alert>
      </div>

      <div class="pa-4">
        <div v-if="imageLoaded" class="cropper-container">
          <Cropper
            ref="cropperRef"
            :src="imageSource"
            :stencil-props="{
              aspectRatio: undefined,
            }"
            :default-size="defaultSize"
            image-restriction="fit-area"
            backgroundClass="cropper-background"
            foregroundClass="cropper-foreground"
            class="cropper"
            @change="handleCropperChange"
          />
        </div>

        <div v-if="!imageLoaded" class="text-center py-8">
          <v-progress-circular indeterminate color="primary" />
          <div class="mt-2">Loading image...</div>
        </div>
      </div>

      <div v-if="errorMessage" class="text-error py-2 px-4">
        <v-icon size="small" class="mr-1">mdi-alert-circle</v-icon>
        {{ errorMessage }}
      </div>

      <div class="pa-4">
        <v-textarea
          :model-value="comment"
          @update:model-value="$emit('update:comment', $event)"
          label="Comment (optional)"
          variant="outlined"
          density="compact"
          rows="2"
        />
      </div>

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn variant="outlined" @click="handleCancel"> Cancel </v-btn>
        <v-btn
          color="primary"
          variant="elevated"
          @click="handleDone"
          :loading="loading || processing"
          :disabled="!imageLoaded"
        >
          Done
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { Cropper } from 'vue-advanced-cropper'
import 'vue-advanced-cropper/dist/style.css'

interface Props {
  modelValue: boolean
  imageData: string
  loading?: boolean
  comment?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  comment: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'update:comment': [value: string]
  save: [imageData: string]
  cancel: []
}>()

const isOpen = ref(props.modelValue)
const imageSource = ref('')
const imageLoaded = ref(false)
const errorMessage = ref('')
const processing = ref(false)
const cropperRef = ref<InstanceType<typeof Cropper> | null>(null)
const croppedDimensions = ref<{ width: number; height: number } | null>(null)
const detectedMimeType = ref<string>('image/png')

// Watch for prop changes
watch(
  () => props.modelValue,
  (newValue) => {
    isOpen.value = newValue
    if (newValue) {
      loadImage()
      errorMessage.value = ''
    }
  },
)

watch(
  () => props.imageData,
  (newValue) => {
    if (isOpen.value && newValue) {
      loadImage()
    }
  },
)

watch(isOpen, (newValue) => {
  emit('update:modelValue', newValue)
  if (!newValue) {
    // Reset state when dialog closes
    imageLoaded.value = false
    imageSource.value = ''
    croppedDimensions.value = null
  }
})

const defaultSize = ({ imageSize }: { imageSize: { width: number; height: number } }) => {
  return {
    width: imageSize.width,
    height: imageSize.height,
  }
}

// vue-advanced-cropper tends to increase the size of the images
// if we do not specify the mime type of the image
// https://github.com/advanced-cropper/vue-advanced-cropper/issues/41
// so, we need to accurately tell it what's the mime type of the file
// in question so it doesn't overscale.
const detectMimeTypeFromDataUrl = (dataUrl: string): string => {
  const base64Data = dataUrl.split(',')[1]
  if (!base64Data) {
    return 'image/png' // fallback
  }

  try {
    // Only need first few bytes
    const binaryString = atob(base64Data.substring(0, 100))
    const bytes = new Uint8Array(binaryString.length)
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i)
    }

    // Check magic bytes (file signature)
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
        // Try to get from data URL prefix
        const match = dataUrl.match(/^data:(image\/[a-z]+);/)
        return match ? match[1] : 'image/png'
    }
  } catch (error) {
    console.error('Error detecting MIME type:', error)
    // Try to get from data URL prefix as fallback
    const match = dataUrl.match(/^data:(image\/[a-z]+);/)
    return match ? match[1] : 'image/png'
  }
}

const loadImage = () => {
  imageLoaded.value = false
  imageSource.value = props.imageData

  detectedMimeType.value = detectMimeTypeFromDataUrl(props.imageData)

  // Give the cropper time to initialize
  setTimeout(() => {
    imageLoaded.value = true
  }, 100)
}

const handleCropperChange = (event: { coordinates?: { width: number; height: number } }) => {
  if (event.coordinates) {
    croppedDimensions.value = {
      width: Math.round(event.coordinates.width),
      height: Math.round(event.coordinates.height),
    }
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

const reset = () => {
  if (cropperRef.value) {
    cropperRef.value.reset()
  }
}

const handleDone = async () => {
  if (!cropperRef.value) {
    errorMessage.value = 'Cropper not initialized'
    return
  }

  processing.value = true
  errorMessage.value = ''

  try {
    const { canvas } = cropperRef.value.getResult()
    if (canvas) {
      // Convert canvas to base64 using the detected MIME type to preserve original format
      const croppedImageData = canvas.toDataURL(detectedMimeType.value)
      emit('save', croppedImageData)
    } else {
      errorMessage.value = 'Failed to process image'
    }
  } catch (error) {
    console.error('Error processing image:', error)
    errorMessage.value = 'Failed to process image. Please try again.'
  } finally {
    processing.value = false
  }
}

const handleCancel = () => {
  errorMessage.value = ''
  emit('cancel')
  isOpen.value = false
}
</script>

<style scoped>
.cropper-container {
  width: 100%;
  height: 600px;
  max-height: 70vh;
  border-radius: 4px;
  overflow: hidden;
}

.cropper {
  height: 100%;
  width: 100%;
}

.cropper :deep(.vue-handler) {
  background: rgb(var(--v-theme-primary));
  border-color: rgb(var(--v-theme-primary));
}

.cropper :deep(.vue-line) {
  border-color: rgb(var(--v-theme-primary));
}

.cropper :deep(.vue-simple-handler) {
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
