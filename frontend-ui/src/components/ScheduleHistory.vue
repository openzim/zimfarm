<template>
  <v-container fluid>
    <template v-if="history.length > 0">
      <template v-if="!showDiffViewer">
        <v-alert type="info" variant="tonal" :icon="false">
          <template v-slot:prepend>
            <v-icon>mdi-information-outline</v-icon>
          </template>
          Select any two entries to compare their differences
        </v-alert>

        <v-list>
          <template v-for="(item, index) in history" :key="item.id">
            <v-list-item
              @click="toggleHistoryItemSelection(item, index)"
              :class="{
                'v-list-item--active': selectedItems.has(index),
                'bg-primary-lighten-5': selectedItems.has(index),
              }"
              class="cursor-pointer"
            >
              <template v-slot:prepend>
                <v-checkbox-btn
                  :model-value="selectedItems.has(index)"
                  @click.stop="toggleHistoryItemSelection(item, index)"
                  :disabled="selectedItems.size >= 2 && !selectedItems.has(index)"
                />
              </template>

              <v-list-item-content>
                <v-list-item-title class="text-subtitle-2">
                  <template v-if="item.comment">
                    <span class="text-wrap">{{ item.comment }}</span>
                  </template>
                  <span v-else class="font-italic text-medium-emphasis">No comment</span>
                </v-list-item-title>

                <v-list-item-subtitle>
                  <div class="d-flex flex-column-reverse flex-sm-row justify-space-between mt-2">
                    <div class="text-caption">
                      <v-icon size="small" class="me-1">mdi-identifier</v-icon>
                      {{ item.id.substring(0, 8) }}
                    </div>
                    <div class="text-caption">
                      <v-icon size="small" class="me-1">mdi-account</v-icon>
                      {{ item.author }}
                    </div>
                    <div class="text-subtitle-2">
                      <v-icon size="small" class="me-1">mdi-clock-outline</v-icon>
                      {{ formatDt(item.created_at, 'ff') }}
                    </div>
                  </div>
                </v-list-item-subtitle>
              </v-list-item-content>
            </v-list-item>
            <v-divider />
          </template>
        </v-list>

        <!-- Load More button -->
        <v-card-actions v-if="hasMore" class="justify-center">
          <v-btn variant="text" :loading="loading" @click="loadMore"> Load More </v-btn>
        </v-card-actions>
      </template>

      <!-- Diff Viewer -->
      <template v-else>
        <v-card>
          <v-card-title class="d-flex align-center text-wrap text-body-1">
            <v-btn icon="mdi-arrow-left" variant="text" @click="backToHistoryList" class="me-2" />
            Comparing History Items
          </v-card-title>

          <v-card-text>
            <div class="mb-4">
              <v-chip size="small" color="info" variant="tonal" class="me-2">
                {{ selectedItemsArray[0]?.id.substring(0, 8) }}
              </v-chip>
              <v-icon class="mx-2">mdi-arrow-right</v-icon>
              <v-chip size="small" color="info" variant="tonal">
                {{ selectedItemsArray[1]?.id.substring(0, 8) }}
              </v-chip>
            </div>

            <div v-if="loadingOfflinerDef" class="d-flex justify-center align-center pa-8">
              <v-progress-circular indeterminate color="primary" />
              <span class="ml-4">Loading offliner definitions...</span>
            </div>

            <DiffViewer v-else :differences="enhancedDifferences" />
          </v-card-text>
        </v-card>
      </template>
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
import { useNotificationStore } from '@/stores/notification'
import { useScheduleHistoryStore } from '@/stores/scheduleHistory'
import { useOfflinerStore } from '@/stores/offliner'
import type { Paginator } from '@/types/base'
import type { ScheduleHistorySchema } from '@/types/schedule'
import type { OfflinerDefinition } from '@/types/offliner'
import { formatDt } from '@/utils/format'
import type * as DeepDiff from 'deep-diff'
import { diff } from 'deep-diff'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { EnhancedDiff } from '@/utils/diff'

const props = defineProps<{
  history: ScheduleHistorySchema[]
  hasMore: boolean
  loading: boolean
  paginator: Paginator
  scheduleName: string
}>()

const emit = defineEmits<{
  load: [{ limit: number; skip: number }]
}>()

const route = useRoute()
const router = useRouter()
const scheduleHistoryStore = useScheduleHistoryStore()
const notificationStore = useNotificationStore()
const offlinerStore = useOfflinerStore()

// New state for multi-selection
const selectedItems = ref<Set<number>>(new Set())
const showDiffViewer = ref(false)
const oldFlagsDefinition = ref<OfflinerDefinition[]>([])
const newFlagsDefinition = ref<OfflinerDefinition[]>([])
const loadingOfflinerDef = ref(false)

const selectedItemsArray = computed(() => {
  return Array.from(selectedItems.value)
    .map((index) => props.history[index])
    .filter(Boolean)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
})

const scheduleDifferences = computed(
  (): DeepDiff.Diff<Record<string, unknown>, Record<string, unknown>>[] | undefined => {
    if (selectedItemsArray.value.length !== 2) {
      return undefined
    }

    const [item1, item2] = selectedItemsArray.value

    // Extract the subset from both items (excluding id, author, comment, created_at)
    const { id, author, comment, created_at, ...subset1 } = item1
    const {
      id: _id,
      author: _author,
      comment: _comment,
      created_at: _created_at,
      ...subset2
    } = item2

    // Suppress unused variable warnings for destructured variables
    void id
    void author
    void comment
    void created_at
    void _id
    void _author
    void _comment
    void _created_at

    return diff(subset1, subset2)
  },
)

// Enhanced differences with blob metadata
const enhancedDifferences = computed((): EnhancedDiff[] | undefined => {
  if (!scheduleDifferences.value) {
    return undefined
  }

  // Build blob map from both old and new configs
  const blobMap = new Map<string, 'image' | 'css' | 'html' | 'txt'>()
  if (selectedItemsArray.value.length === 2) {
    const oldConfig = selectedItemsArray.value[0].config as { offliner?: Record<string, unknown> }
    const newConfig = selectedItemsArray.value[1].config as { offliner?: Record<string, unknown> }

    const addBlobsToMap = (
      config: { offliner?: Record<string, unknown> },
      definition: OfflinerDefinition[],
    ) => {
      if (!config.offliner || !definition.length) return

      for (const field of definition) {
        if (field.type === 'blob' && field.kind) {
          const value = config.offliner[field.data_key]
          if (value && typeof value === 'string') {
            blobMap.set(value, field.kind)
          }
        }
      }
    }

    addBlobsToMap(oldConfig, oldFlagsDefinition.value)
    addBlobsToMap(newConfig, newFlagsDefinition.value)
  }

  // Enhance each difference with blob metadata
  return scheduleDifferences.value.map((diff) => {
    const enhanced: EnhancedDiff = { ...diff }

    // Check if any value in this diff is a blob
    if (diff.kind === 'E' && (diff.lhs || diff.rhs)) {
      const oldValue = diff.lhs ? String(diff.lhs) : ''
      const newValue = diff.rhs ? String(diff.rhs) : ''
      const oldKind = blobMap.get(oldValue)
      const newKind = blobMap.get(newValue)

      if (oldKind || newKind) {
        enhanced.isBlob = true
        enhanced.blobKind = newKind || oldKind
      }
    } else if (diff.kind === 'N' && diff.rhs) {
      const value = String(diff.rhs)
      const kind = blobMap.get(value)
      if (kind) {
        enhanced.isBlob = true
        enhanced.blobKind = kind
      }
    } else if (diff.kind === 'D' && diff.lhs) {
      const value = String(diff.lhs)
      const kind = blobMap.get(value)
      if (kind) {
        enhanced.isBlob = true
        enhanced.blobKind = kind
      }
    }

    return enhanced
  })
})

const toggleHistoryItemSelection = async (item: ScheduleHistorySchema, index: number) => {
  if (selectedItems.value.has(index)) {
    // Remove from selection
    selectedItems.value.delete(index)
    // If we go below 2 items, hide the diff viewer
    if (selectedItems.value.size < 2) {
      showDiffViewer.value = false
    }
  } else if (selectedItems.value.size < 2) {
    // Add to selection (max 2 items)
    selectedItems.value.add(index)
    // Automatically show diff viewer when exactly 2 items are selected
    if (selectedItems.value.size === 2) {
      showDiffViewer.value = true
      await fetchOfflinerDefinitions()
    }
  }

  updateUrlQueryParams()
}

// Fetch both offliner definitions from the selected schedule history items
const fetchOfflinerDefinitions = async () => {
  if (selectedItemsArray.value.length !== 2) {
    return
  }

  loadingOfflinerDef.value = true
  oldFlagsDefinition.value = []
  newFlagsDefinition.value = []

  try {
    // Get offliner info from both history items
    const oldItem = selectedItemsArray.value[0]
    const newItem = selectedItemsArray.value[1]

    const oldConfig = oldItem.config as { offliner?: { offliner_id?: string } }
    const newConfig = newItem.config as { offliner?: { offliner_id?: string } }

    const oldOfflinerName = oldConfig?.offliner?.offliner_id
    const newOfflinerName = newConfig?.offliner?.offliner_id

    if (!oldOfflinerName && !newOfflinerName) {
      console.warn('No offliner_id found in either history item')
      return
    }

    if (oldOfflinerName && oldItem.offliner_definition_version) {
      const version = oldItem.offliner_definition_version
      const response = await offlinerStore.fetchOfflinerDefinitionByVersion(
        oldOfflinerName,
        version,
      )
      if (response) {
        oldFlagsDefinition.value = response.flags
      }
    }

    if (newOfflinerName && newItem.offliner_definition_version) {
      const version = newItem.offliner_definition_version
      const response = await offlinerStore.fetchOfflinerDefinitionByVersion(
        newOfflinerName,
        version,
      )
      if (response) {
        newFlagsDefinition.value = response.flags
      }
    }
  } catch (err) {
    console.error('Failed to fetch offliner definitions:', err)
    notificationStore.showError('Failed to load offliner definitions for blob comparison')
  } finally {
    loadingOfflinerDef.value = false
  }
}

const updateUrlQueryParams = () => {
  const orderedIds = Array.from(selectedItems.value)
    .map((index) => props.history[index])
    .filter(Boolean)
    .sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
    .map((item) => item.id)

  if (orderedIds.length === 2) {
    router.replace({
      query: {
        ...route.query,
        // Encode as oldest...newest
        compare: orderedIds.join('...'),
      },
    })
  } else {
    // Remove compare parameter if not exactly 2 items selected
    const newQuery = { ...route.query }
    delete (newQuery as Record<string, unknown>).compare
    router.replace({ query: newQuery })
  }
}

const selectHistoryEntriesFromUrl = async () => {
  const compareParam = route.query.compare as string
  if (!compareParam) return

  const historyIds = compareParam.split('...')
  if (historyIds.length !== 2) return

  const [id1, id2] = historyIds

  const index1 = props.history.findIndex((item) => item.id === id1)
  const index2 = props.history.findIndex((item) => item.id === id2)

  // If both entries are found in the current history, select them
  if (index1 !== -1 && index2 !== -1) {
    selectedItems.value = new Set([index1, index2])
    showDiffViewer.value = true
    await fetchOfflinerDefinitions()
    return
  }

  const missingIds = []
  if (index1 === -1) missingIds.push(id1)
  if (index2 === -1) missingIds.push(id2)

  if (missingIds.length > 0) {
    try {
      // Fetch missing entries in parallel
      const fetchPromises = missingIds.map((id) =>
        scheduleHistoryStore.fetchHistoryEntry(props.scheduleName, id),
      )

      await Promise.all(fetchPromises)

      // After fetching, find the indices again
      const newIndex1 = scheduleHistoryStore.history.findIndex(
        (item: ScheduleHistorySchema) => item.id === id1,
      )
      const newIndex2 = scheduleHistoryStore.history.findIndex(
        (item: ScheduleHistorySchema) => item.id === id2,
      )

      if (newIndex1 !== -1 && newIndex2 !== -1) {
        selectedItems.value = new Set([newIndex1, newIndex2])
        showDiffViewer.value = true
        await fetchOfflinerDefinitions()
      } else {
        notificationStore.showError('Failed to find history entries after fetching')
      }
    } catch (error) {
      console.error('Failed to fetch history entries from URL', error)
      notificationStore.showError('Failed to load history entries for comparison')
    }
  }
}

const backToHistoryList = () => {
  showDiffViewer.value = false
  selectedItems.value.clear()
  updateUrlQueryParams()
}

// Load more history items
const loadMore = () => {
  emit('load', { limit: props.paginator.limit, skip: props.history.length })
}

// Watch for changes in history array to re-select entries from URL
watch(
  () => props.history,
  () => {
    selectHistoryEntriesFromUrl()
  },
  { deep: true },
)

// Watch for changes in route query parameters
watch(
  () => route.query.compare,
  () => {
    selectHistoryEntriesFromUrl()
  },
)

// Initialize selection from URL on mount
onMounted(async () => {
  await selectHistoryEntriesFromUrl()
})
</script>
