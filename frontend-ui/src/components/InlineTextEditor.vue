<template>
  <div>
    <div v-if="label" class="text-caption text-grey-darken-1 mb-1">
      {{ label }}
    </div>
    <!-- Drop Zone / Editor Container -->
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
          : isEditing
            ? 'none'
            : '2px dashed rgb(var(--v-border-color))',
        height: '250px',
        cursor: isEditing ? 'default' : 'pointer',
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
        v-if="!showEditor"
        class="d-flex flex-column align-center justify-center pa-8 h-100"
        style="pointer-events: none"
      >
        <v-icon size="48" color="grey-lighten-1">mdi-file-document-outline</v-icon>
        <p class="text-body-1 text-grey-darken-1 mt-3 mb-0 text-center">
          Drag & drop a {{ fileType.toUpperCase() }} file here
        </p>
        <p class="text-body-2 text-grey mt-2 mb-2 text-center">
          or click to browse, or paste text/URL
        </p>
        <v-btn
          size="small"
          variant="outlined"
          color="primary"
          class="mt-2"
          style="pointer-events: auto"
          @click.stop="startEditing"
        >
          Write from scratch
        </v-btn>
      </div>

      <!-- Editor State -->
      <div v-if="showEditor" class="d-flex flex-column h-100 w-100 position-relative">
        <!-- Loading Overlay -->
        <div
          v-if="loading"
          class="d-flex flex-column align-center justify-center h-100 position-absolute w-100 bg-white"
          style="z-index: 20; opacity: 0.8"
        >
          <v-progress-circular indeterminate color="primary" size="48" />
          <p class="text-body-2 mt-3">Loading file...</p>
        </div>

        <div
          v-else-if="previewErrorMessage"
          class="w-100 h-100 d-flex align-center justify-center pa-4 text-error text-caption"
        >
          <v-icon size="small" class="mr-1">mdi-alert-circle</v-icon>
          {{ previewErrorMessage }}
        </div>

        <!-- Action Buttons -->
        <div
          v-if="!loading"
          class="position-absolute d-flex flex-column"
          style="top: 8px; right: 24px; z-index: 100; gap: 8px"
        >
          <template v-if="!previewErrorMessage">
            <v-btn
              v-if="hasChanges"
              icon
              size="small"
              color="success"
              @click.stop="handleSave"
              :loading="loading"
            >
              <v-icon>mdi-content-save</v-icon>
              <v-tooltip activator="parent" location="left">Save file</v-tooltip>
            </v-btn>
          </template>
          <v-btn icon size="small" color="error" @click.stop="handleClear">
            <v-icon>mdi-delete</v-icon>
            <v-tooltip activator="parent" location="left">Delete file</v-tooltip>
          </v-btn>
        </div>

        <div
          v-if="!previewErrorMessage"
          class="w-100 h-100"
          style="border: 1px solid rgb(var(--v-border-color))"
        >
          <CodeEditor
            v-model="internalTextData"
            :file-type="fileType"
            :placeholder="`Enter your ${fileType.toUpperCase()} code here...`"
            height="100%"
            @update:model-value="handleContentChange"
          />
        </div>
      </div>
    </v-sheet>

    <!-- Comment Field -->
    <div v-if="!previewErrorMessage" class="mt-2">
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
      :accept="acceptedFileTypes"
      style="display: none"
      @change="handleFileChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import CodeEditor from '@/components/CodeEditor.vue'
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
  fileType?: 'css' | 'html' | 'txt'
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
  fileType: 'txt',
})

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:comment': [value: string]
  save: [content: string]
  clear: []
  'file-selected': [file: File]
  'url-entered': [url: string]
  'use-original-url': [url: string]
}>()

// Refs
const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragging = ref(false)
const internalErrorMessage = ref('')
const internalTextData = ref('')
const forceEditing = ref(false)
const localChecksum = ref<string | undefined>(undefined)

// Computed
const errorMessage = computed(() => props.errorMessage || internalErrorMessage.value)
const isEditing = computed(() => !!internalTextData.value || forceEditing.value || props.loading)

const showEditor = computed(() => isEditing.value || !!props.previewErrorMessage)

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

  // If there's new content but no original checksum, it's new text
  if (!props.originalChecksum && internalTextData.value) return true

  return false
})

const acceptedFileTypes = computed(() => {
  switch (props.fileType) {
    case 'html':
      return '.html,.htm,text/html'
    case 'css':
      return '.css,text/css'
    case 'txt':
      return '.txt,text/plain'
    default:
      return 'text/*'
  }
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

const resetState = () => {
  internalTextData.value = ''
  internalErrorMessage.value = ''
  forceEditing.value = false
  localChecksum.value = undefined
}

const startEditing = () => {
  forceEditing.value = true
}

const handleContentChange = (val: string) => {
  internalTextData.value = val
}

// Watch for external changes
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue !== null && newValue !== undefined) {
      if (newValue !== internalTextData.value) {
        internalTextData.value = newValue
        internalErrorMessage.value = ''
      }
    } else {
      resetState()
    }
  },
  { immediate: true },
)

// Helper function to convert text to base64
const textToBase64 = (text: string): string => {
  return btoa(text)
}

// Watch for changes in text data to compute checksum
watch(
  internalTextData,
  async (newContent) => {
    if (newContent) {
      const base64Data = textToBase64(newContent)
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
  try {
    const text = await file.text()
    internalTextData.value = text
    forceEditing.value = true
    emit('file-selected', file)
  } catch (error) {
    console.error('Failed to process file:', error)
    internalErrorMessage.value = 'Failed to read text file'
  }
}

const handleContainerClick = (event: MouseEvent) => {
  // Don't trigger file input if clicking on buttons, inputs, or when editor is active
  if (
    isEditing.value ||
    (event.target as HTMLElement).closest('button') ||
    (event.target as HTMLElement).closest('input') ||
    (event.target as HTMLElement).closest('textarea') ||
    (event.target as HTMLElement).closest('.monaco-editor')
  ) {
    return
  }

  fileInputRef.value?.click()
}

const handleDragEnter = () => {
  if (isEditing.value) return
  isDragging.value = true
}

const handleDragOver = () => {
  if (isEditing.value) return
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = async (event: DragEvent) => {
  if (isEditing.value) return
  isDragging.value = false

  const files = event.dataTransfer?.files
  if (!files || files.length === 0) return

  const file = files[0]
  await processFile(file)
}

const handlePaste = async (event: ClipboardEvent) => {
  if (isEditing.value) return
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

  // Check for URL text or plain text
  const text = clipboardData.getData('text/plain')
  if (text) {
    event.preventDefault()
    if (isValidUrl(text.trim())) {
      emit('url-entered', text.trim())
    } else {
      internalTextData.value = text
      forceEditing.value = true
    }
  }
}

const handleClear = () => {
  resetState()
  emit('clear')
}

const handleSave = () => {
  emit('save', internalTextData.value)
}
</script>
