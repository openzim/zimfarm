<template>
  <v-container fluid class="pa-0">
    <template v-if="history.length > 0">
      <v-row>
        <!-- Left column with commit info -->
        <v-col cols="4">
          <v-list>
            <template v-for="(item, index) in history" :key="item.id">
              <v-list-item
                @click="selectHistoryItem(item, index)"
                :class="{ 'v-list-item--active': selectedItemIndex === index }"
              >
                <v-list-item-content>
                  <v-list-item-title class="text-subtitle-1">
                    <template v-if="item.comment">
                      <v-tooltip
                        v-if="item.comment.length > 50"
                        :text="item.comment"
                        location="top"
                        activator="parent"
                        max-width="400"
                      >
                        <template v-slot:activator="{ props: tooltipProps }">
                          <span v-bind="tooltipProps" style="cursor: pointer">
                            {{ item.comment.substring(0, 50) }}...
                          </span>
                        </template>
                      </v-tooltip>
                      <span v-else>{{ item.comment }}</span>
                    </template>
                    <span v-else class="font-italic text-medium-emphasis">No commit message</span>
                  </v-list-item-title>
                  <div class="d-flex align-center gap-4 justify-space-between">
                    <div class="text-caption">
                      <v-icon size="small" class="me-1">mdi-identifier</v-icon>
                      {{ item.id.substring(0, 8) }}
                    </div>
                    <div class="text-body-2 font-weight-medium">
                      <v-icon size="small" class="me-1">mdi-account</v-icon>
                      {{ item.author }}
                    </div>
                  </div>
                  <div class="text-caption mt-1">
                    <v-icon size="small" class="me-1">mdi-clock-outline</v-icon>
                    {{ new Date(item.created_at).toLocaleString() }}
                  </div>
                </v-list-item-content>
              </v-list-item>
              <v-divider v-if="index < history.length - 1" />
            </template>
          </v-list>
          <v-card-actions v-if="hasMore" class="justify-center">
            <v-btn variant="text" :loading="loading" @click="loadMore"> Load More </v-btn>
          </v-card-actions>
        </v-col>

        <!-- Right column with diff/raw data viewer -->
        <v-col cols="8">
          <v-card v-if="selectedConfig" flat>
            <v-card-text>
              <!-- Toggle between diff and raw config view -->
              <v-tabs v-model="viewMode" class="mb-4">
                <v-tab value="diff" :disabled="!canShowDiff">
                  <v-icon class="mr-2">mdi-compare-horizontal</v-icon>
                  Diff
                </v-tab>
                <v-tab value="config">
                  <v-icon class="mr-2">mdi-code-braces</v-icon>
                  JSON View
                </v-tab>
              </v-tabs>

              <v-window v-model="viewMode">
                <v-window-item value="diff">
                  <div v-if="canShowDiff">
                    <div class="mb-3">
                      <v-chip size="small" color="info" variant="tonal" class="mr-2">
                        Comparing {{ selectedItem?.id.substring(0, 8) }} with
                        {{ previousItem?.id.substring(0, 8) }}
                      </v-chip>
                    </div>
                    <DiffViewer :differences="scheduleDifferences" />
                  </div>
                  <div v-else class="text-center py-8">
                    <v-icon size="large" color="grey" class="mb-2">mdi-information-outline</v-icon>
                    <div class="text-body-1 text-medium-emphasis">
                      Select a history item (except the oldest) to compare with the previous version
                    </div>
                  </div>
                </v-window-item>

                <v-window-item value="config">
                  <v-textarea
                    v-model="selectedConfigStr"
                    readonly
                    auto-grow
                    variant="outlined"
                    class="font-monospace"
                    :rows="20"
                  />
                </v-window-item>
              </v-window>
            </v-card-text>
          </v-card>
          <v-card v-else flat class="d-flex align-center justify-center" height="100%">
            <v-card-text class="text-center text-medium-emphasis">
              Select a history item to view its configuration
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
    <template v-else>
      <v-row>
        <v-col cols="12" class="d-flex flex-column align-center justify-center">
          <v-icon size="x-large" color="grey" class="mb-4">mdi-history</v-icon>
          <div class="text-h6 text-medium-emphasis">No history available for this schedule</div>
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<script setup lang="ts">
import DiffViewer from '@/components/DiffViewer.vue'
import type { Paginator } from '@/types/base'
import type { BaseScheduleHistorySchema, ScheduleHistorySchema } from '@/types/schedule'
import type * as DeepDiff from 'deep-diff'
import { diff } from 'deep-diff'
import { computed, ref, watch } from 'vue'

const props = defineProps<{
  history: ScheduleHistorySchema[]
  hasMore: boolean
  loading: boolean
  paginator: Paginator
}>()

const emit = defineEmits<{
  load: [{ limit: number; skip: number }]
}>()

const selectedConfig = ref<BaseScheduleHistorySchema | null>(null)
const selectedItemIndex = ref<number | null>(null)
const selectedItem = ref<ScheduleHistorySchema | null>(null)
const viewMode = ref<'diff' | 'config'>('diff')

const selectedConfigStr = computed(() => {
  if (!selectedConfig.value) return ''
  return JSON.stringify(selectedConfig.value, null, 2)
})

const previousItem = computed(() => {
  if (selectedItemIndex.value === null || selectedItemIndex.value >= props.history.length - 1) {
    return null
  }
  return props.history[selectedItemIndex.value + 1]
})

const canShowDiff = computed(() => {
  return selectedItem.value !== null && previousItem.value !== null
})

const scheduleDifferences = computed(
  (): DeepDiff.Diff<Record<string, unknown>, Record<string, unknown>>[] | undefined => {
    if (!canShowDiff.value || !selectedItem.value || !previousItem.value) {
      return undefined
    }

    // Extract the subset from both items (excluding id, author, comment, created_at)
    const { id, author, comment, created_at, ...previousSubset } = previousItem.value
    const {
      id: _id,
      author: _author,
      comment: _comment,
      created_at: _created_at,
      ...currentSubset
    } = selectedItem.value

    // Suppress unused variable warnings for destructured variables
    void id
    void author
    void comment
    void created_at
    void _id
    void _author
    void _comment
    void _created_at

    return diff(previousSubset, currentSubset)
  },
)

const selectHistoryItem = (item: ScheduleHistorySchema, index: number) => {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const { id, author, comment, created_at, ...scheduleSubset } = item
  selectedConfig.value = scheduleSubset
  selectedItemIndex.value = index
  selectedItem.value = item

  // Auto-switch to diff view if we can show a diff, otherwise show JSON view
  if (canShowDiff.value) {
    viewMode.value = 'diff'
  } else {
    viewMode.value = 'config'
  }
}

const loadMore = () => {
  emit('load', { limit: props.paginator.limit, skip: props.history.length })
}

// Watch history changes and select first item
watch(
  () => props.history,
  (newHistory: ScheduleHistorySchema[]) => {
    if (newHistory.length > 0) {
      selectHistoryItem(newHistory[0], 0)
    }
  },
  { immediate: true },
)
</script>
