<template>
  <v-card max-width="600" max-height="400">
    <v-card-title class="text-subtitle-2 pa-3">File Info</v-card-title>
    <v-card-text class="pa-3 overflow-auto">
      <div class="d-flex flex-column">
        <!-- Top level entries -->
        <div v-if="fileInfo.id" class="py-1">
          <v-row dense class="align-start">
            <v-col cols="4" class="text-body-2">ID</v-col>
            <v-col cols="8" class="text-body-2 text-break">
              <code class="text-break text-pink-accent-2">{{ fileInfo.id }}</code>
            </v-col>
          </v-row>
        </div>
        <v-divider v-if="fileInfo.id" class="my-1" />
        <div v-if="fileInfo.article_count !== undefined" class="py-1">
          <v-row dense class="align-start">
            <v-col cols="4" class="text-body-2 font-weight-medium">Article Count</v-col>
            <v-col cols="8" class="text-body-2">{{
              fileInfo.article_count.toLocaleString()
            }}</v-col>
          </v-row>
        </div>
        <v-divider v-if="fileInfo.article_count !== undefined" class="my-1" />
        <div v-if="fileInfo.media_count !== undefined" class="py-1">
          <v-row dense class="align-start">
            <v-col cols="4" class="text-body-2 font-weight-medium">Media Count</v-col>
            <v-col cols="8" class="text-body-2">{{ fileInfo.media_count.toLocaleString() }}</v-col>
          </v-row>
        </div>
        <v-divider v-if="fileInfo.media_count !== undefined" class="my-1" />
        <div v-if="fileInfo.size !== undefined" class="py-1">
          <v-row dense class="align-start">
            <v-col cols="4" class="text-body-2 font-weight-medium">Size</v-col>
            <v-col cols="8" class="text-body-2">{{ formattedBytesSize(fileInfo.size) }}</v-col>
          </v-row>
        </div>
        <v-divider v-if="fileInfo.size !== undefined" class="my-1" />

        <!-- Counter entries -->
        <div v-if="Object.keys(fileInfo.counter || {}).length > 0" class="py-2">
          <v-row dense class="align-start">
            <v-col cols="4" class="text-body-2 font-weight-medium">Counter</v-col>
            <v-col cols="8">
              <div class="bg-grey-lighten-5 rounded pa-2">
                <v-row dense class="text-caption font-weight-medium mb-1">
                  <v-col cols="9">MIME</v-col>
                  <v-col cols="3" class="text-right">Count</v-col>
                </v-row>
                <v-divider class="mb-2" />
                <div
                  v-for="(value, key, index) in fileInfo.counter"
                  :key="key"
                  :class="index % 2 === 0 ? 'bg-grey-lighten-3' : ''"
                >
                  <v-row dense class="py-1 px-2">
                    <v-col cols="9" class="text-body-2 text-break">{{ key }}</v-col>
                    <v-col cols="3" class="text-body-2 text-right">{{
                      value.toLocaleString()
                    }}</v-col>
                  </v-row>
                </div>
              </div>
            </v-col>
          </v-row>
        </div>
        <v-divider v-if="Object.keys(fileInfo.counter || {}).length > 0" class="my-2" />

        <!-- Metadata entries -->
        <div v-if="filteredMetadataEntries.length > 0" class="py-2">
          <v-row dense class="align-start">
            <v-col cols="4" class="text-body-2 font-weight-medium">Metadata</v-col>
            <v-col cols="8">
              <div class="bg-grey-lighten-5 rounded pa-2">
                <div
                  v-for="([key, value], index) in filteredMetadataEntries"
                  :key="key"
                  :class="index % 2 === 0 ? 'bg-grey-lighten-3' : ''"
                >
                  <v-row dense class="align-start py-1 px-2">
                    <v-col cols="4" md="3" class="text-body-2 font-weight-medium">{{ key }}</v-col>
                    <v-col cols="8" md="9" class="text-body-2 text-break">
                      <!-- Handle illustration_ attributes as base64 images -->
                      <div
                        v-if="isIllustrationAttribute(key)"
                        class="d-flex flex-column align-start"
                      >
                        <v-img
                          :src="`data:image/png;base64,${value}`"
                          :alt="key"
                          :width="getIllustrationWidth(key)"
                          :height="getIllustrationHeight(key)"
                          contain
                          @error="handleImageError"
                        />
                        <div
                          v-if="imageError"
                          class="d-flex align-center text-grey pa-2"
                          style="
                            border: 1px dashed rgba(0, 0, 0, 0.3);
                            border-radius: 4px;
                            background-color: rgba(0, 0, 0, 0.02);
                          "
                        >
                          <v-icon>mdi-image-broken</v-icon>
                          <span class="text-caption ml-1">Image failed to load</span>
                        </div>
                      </div>
                      <!-- Regular text values -->
                      <span v-else>{{ value }}</span>
                    </v-col>
                  </v-row>
                </div>
              </div>
            </v-col>
          </v-row>
        </div>
        <v-divider v-if="filteredMetadataEntries.length > 0" class="my-2" />
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import type { TaskFileInfo } from '@/types/tasks'
import { formattedBytesSize } from '@/utils/format'
import { computed, ref } from 'vue'

const props = defineProps<{
  fileInfo: TaskFileInfo
}>()

// Reactive data
const imageError = ref(false)

// Methods
const isIllustrationAttribute = (key: string): boolean => {
  return key.toLowerCase().startsWith('illustration_')
}

const handleImageError = () => {
  imageError.value = true
}

const parseIllustrationSize = (key: string): { width: number; height: number } | null => {
  const lower = key.toLowerCase()
  const match = lower.match(/^illustration_(\d+)x(\d+)$/)
  if (!match) return null
  const width = parseInt(match[1], 10)
  const height = parseInt(match[2], 10)
  if (!Number.isFinite(width) || !Number.isFinite(height)) return null
  return { width, height }
}

const getIllustrationWidth = (key: string): number | undefined => {
  const size = parseIllustrationSize(key)
  return size?.width
}

const getIllustrationHeight = (key: string): number | undefined => {
  const size = parseIllustrationSize(key)
  return size?.height
}

// omit counter from metadata as it is already shown in the counter section
const filteredMetadataEntries = computed(() => {
  const entries = Object.entries(props.fileInfo?.metadata || {})
  return entries.filter(([key]) => key.toLowerCase() !== 'counter')
})
</script>
