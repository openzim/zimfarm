<template>
  <v-btn
    icon="mdi-eye"
    size="x-small"
    variant="text"
    color="primary"
    @click="handleView"
    :title="`View ${kind === 'image' || kind === 'illustration' ? 'Image/Illustration' : kind.toUpperCase()}`"
    :loading="loadingBlobContent"
  />

  <!-- Image Viewer Dialog -->
  <v-dialog v-if="kind === 'image' || kind === 'illustration'" v-model="showViewer" max-width="600">
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span>View Image/Illustration</span>
        <v-btn icon="mdi-close" variant="text" @click="handleClose" />
      </v-card-title>
      <v-card-text>
        <v-progress-circular v-if="loadingBlobContent" indeterminate />
        <v-img
          v-else-if="blobContent"
          :src="blobContent"
          max-height="70vh"
          contain
          alt="Blob image"
        />
        <div v-else class="text-error">Failed to load image</div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn color="primary" variant="text" @click="handleClose">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- Text Viewer Dialog -->
  <v-dialog v-if="isText" v-model="showViewer" max-width="600px">
    <v-card>
      <v-card-title class="d-flex justify-space-between align-center">
        <span>View {{ kind === 'txt' ? 'Text' : kind.toUpperCase() }}</span>
        <v-btn icon="mdi-close" variant="text" @click="handleClose" />
      </v-card-title>
      <v-card-text>
        <v-progress-circular v-if="loadingBlobContent" indeterminate />
        <div v-else-if="blobContent">
          <CodeEditor
            :model-value="blobContent"
            :file-type="kind as TextKind"
            readonly
            height="500px"
          />
        </div>
        <div v-else class="text-error">Failed to load content</div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn color="primary" variant="text" @click="handleClose">Close</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { isTextKind, type BlobKind, type TextKind } from '@/utils/blob'
import CodeEditor from '@/components/CodeEditor.vue'

const notificationStore = useNotificationStore()

interface Props {
  blobValue: string
  kind?: BlobKind
}

const props = withDefaults(defineProps<Props>(), {
  kind: 'txt',
})

const showViewer = ref(false)
const blobContent = ref('')
const loadingBlobContent = ref(false)

const isText = computed(() => isTextKind(props.kind))

const fetchBlobByUrl = async (url: string): Promise<Blob | null> => {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  return await response.blob()
}

const handleViewImage = async () => {
  if (!props.blobValue) return

  loadingBlobContent.value = true
  blobContent.value = ''

  try {
    const blob = await fetchBlobByUrl(props.blobValue)
    if (!blob) {
      throw new Error('Failed to fetch blob content')
    }
    const reader = new FileReader()
    blobContent.value = await new Promise((resolve, reject) => {
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsDataURL(blob)
    })

    showViewer.value = true
  } catch (error) {
    console.error('Failed to load image content:', error)
    notificationStore.showError('There was a network error while loading image')
  } finally {
    loadingBlobContent.value = false
  }
}

const handleViewText = async () => {
  if (!props.blobValue) return

  loadingBlobContent.value = true
  blobContent.value = ''

  try {
    const blob = await fetchBlobByUrl(props.blobValue)
    if (!blob) {
      throw new Error('Failed to fetch blob content')
    }
    blobContent.value = await blob.text()

    showViewer.value = true
  } catch (error) {
    console.error('Failed to load text content:', error)
    notificationStore.showError('There was a network error while loading text content')
  } finally {
    loadingBlobContent.value = false
  }
}

const handleView = () => {
  if (props.kind === 'image' || props.kind === 'illustration') {
    handleViewImage()
  } else if (isText.value) {
    handleViewText()
  }
}

const handleClose = () => {
  showViewer.value = false
}
</script>
