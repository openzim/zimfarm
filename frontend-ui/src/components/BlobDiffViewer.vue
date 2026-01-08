<template>
  <div class="blob-diff-viewer">
    <v-card flat variant="outlined">
      <v-card-text class="pa-0">
        <div v-if="loading" class="d-flex justify-center align-center pa-8">
          <v-progress-circular indeterminate color="primary" />
          <span class="ml-4">Loading blob content for comparison...</span>
        </div>

        <!-- Fallback to simple URL display on error -->
        <div v-else-if="loadFailed" class="pa-4">
          <div class="text-body-2 text-break">
            <span v-if="oldBlobUrl" class="text-error text-break">{{ oldBlobUrl }}</span>
            <span v-else class="text-medium-emphasis">null</span>
            <span class="mx-2 text-medium-emphasis">→</span>
            <span v-if="newBlobUrl" class="text-success text-break">{{ newBlobUrl }}</span>
            <span v-else class="text-medium-emphasis">null</span>
          </div>
        </div>

        <!-- Image comparison -->
        <div v-else-if="kind === 'image'" class="image-comparison">
          <v-row no-gutters>
            <v-col cols="6" class="pa-4 border-right">
              <div class="text-caption text-medium-emphasis mb-2">Previous</div>
              <div v-if="!oldBlobUrl" class="pa-4 text-center text-medium-emphasis">
                <v-icon size="large" class="mb-2">mdi-image-off</v-icon>
                <div class="text-caption">No previous image</div>
              </div>
              <v-img
                v-else-if="oldBlobContent"
                :src="oldBlobContent"
                max-height="400px"
                contain
                alt="Previous image"
                class="border rounded"
              />
              <div v-else class="text-caption text-error">Failed to load previous image</div>
            </v-col>
            <v-col cols="6" class="pa-4">
              <div class="text-caption text-medium-emphasis mb-2">Current</div>
              <div v-if="!newBlobUrl" class="pa-4 text-center text-medium-emphasis">
                <v-icon size="large" class="mb-2">mdi-image-off</v-icon>
                <div class="text-caption">No current image (removed)</div>
              </div>
              <v-img
                v-else-if="newBlobContent"
                :src="newBlobContent"
                max-height="400px"
                contain
                alt="Current image"
                class="border rounded"
              />
              <div v-else class="text-caption text-error">Failed to load current image</div>
            </v-col>
          </v-row>
        </div>

        <!-- Text/Code diff -->
        <div v-else-if="isText && diffHtml" class="text-diff pa-4">
          <div v-html="diffHtml" class="diff2html-container"></div>
        </div>

        <!-- No differences -->
        <div v-else-if="!diffHtml && !loading && !loadFailed" class="pa-8 text-center">
          <v-icon size="large" color="success" class="mb-2">mdi-check-circle</v-icon>
          <div class="text-h6">No differences found</div>
          <div class="text-body-2 text-medium-emphasis">The blob contents are identical</div>
        </div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { createPatch, createTwoFilesPatch } from 'diff'
import { html } from 'diff2html'
import 'diff2html/bundles/css/diff2html.min.css'
import { useNotificationStore } from '@/stores/notification'
import { isTextKind, type BlobKind } from '@/utils/blob'
import { ColorSchemeType } from 'diff2html/lib/types'

interface Props {
  oldBlobUrl: string | null
  newBlobUrl: string | null
  kind?: BlobKind
  fieldName?: string
}

const props = withDefaults(defineProps<Props>(), {
  kind: 'txt',
  fieldName: 'blob',
})

const notificationStore = useNotificationStore()

const loading = ref(false)
const loadFailed = ref(false)
const oldBlobContent = ref<string>('')
const newBlobContent = ref<string>('')
const diffHtml = ref<string>('')

const isText = computed(() => isTextKind(props.kind))

const fetchBlobByUrl = async (url: string): Promise<Blob | null> => {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`)
  }
  return await response.blob()
}

const fetchImageBlob = async (url: string): Promise<string> => {
  const blob = await fetchBlobByUrl(url)
  if (!blob) {
    throw new Error('Failed to fetch blob content')
  }

  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

const fetchTextBlob = async (url: string): Promise<string> => {
  const blob = await fetchBlobByUrl(url)
  if (!blob) {
    throw new Error('Failed to fetch blob content')
  }
  return await blob.text()
}

const generateTextDiff = (oldContent: string, newContent: string): string => {
  const patch = createPatch(`${props.fieldName}`, oldContent, newContent, '', '', { context: 3 })

  return html(patch, {
    drawFileList: false,
    matching: 'lines',
    outputFormat: 'side-by-side',
    renderNothingWhenEmpty: false,
    colorScheme: ColorSchemeType.AUTO,
  })
}

const loadBlobsAndGenerateDiff = async () => {
  loading.value = true
  loadFailed.value = false
  oldBlobContent.value = ''
  newBlobContent.value = ''
  diffHtml.value = ''

  try {
    if (props.kind === 'image') {
      const promises = []

      if (props.oldBlobUrl) {
        promises.push(fetchImageBlob(props.oldBlobUrl))
      } else {
        promises.push(Promise.resolve(''))
      }

      if (props.newBlobUrl) {
        promises.push(fetchImageBlob(props.newBlobUrl))
      } else {
        promises.push(Promise.resolve(''))
      }

      const [oldImage, newImage] = await Promise.all(promises)

      oldBlobContent.value = oldImage
      newBlobContent.value = newImage
    } else if (isText.value) {
      const promises = []

      if (props.oldBlobUrl) {
        promises.push(fetchTextBlob(props.oldBlobUrl))
      } else {
        promises.push(Promise.resolve(''))
      }

      if (props.newBlobUrl) {
        promises.push(fetchTextBlob(props.newBlobUrl))
      } else {
        promises.push(Promise.resolve(''))
      }

      const [oldText, newText] = await Promise.all(promises)

      oldBlobContent.value = oldText
      newBlobContent.value = newText
      diffHtml.value = generateTextDiff(oldText, newText)
    }
  } catch (err) {
    console.error('Failed to load blob content for comparison:', err)
    notificationStore.showError('Failed to load blob content for comparison')
    loadFailed.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadBlobsAndGenerateDiff()
})
</script>

<style scoped>
.blob-diff-viewer {
  width: 100%;
}

.border-right {
  border-right: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.border {
  border: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}

.image-comparison {
  max-height: 600px;
  overflow-y: auto;
}

.text-diff {
  max-height: 600px;
  overflow: auto;
}
</style>
