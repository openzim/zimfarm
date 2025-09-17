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

            <DiffViewer :differences="scheduleDifferences" />
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
import type { Paginator } from '@/types/base'
import type { ScheduleHistorySchema } from '@/types/schedule'
import { formatDt } from '@/utils/format'
import type * as DeepDiff from 'deep-diff'
import { diff } from 'deep-diff'
import { computed, ref } from 'vue'

const props = defineProps<{
  history: ScheduleHistorySchema[]
  hasMore: boolean
  loading: boolean
  paginator: Paginator
}>()

const emit = defineEmits<{
  load: [{ limit: number; skip: number }]
}>()

// New state for multi-selection
const selectedItems = ref<Set<number>>(new Set())
const showDiffViewer = ref(false)

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

const toggleHistoryItemSelection = (item: ScheduleHistorySchema, index: number) => {
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
    }
  }
}

const backToHistoryList = () => {
  showDiffViewer.value = false
  selectedItems.value.clear()
}

// Load more history items
const loadMore = () => {
  emit('load', { limit: props.paginator.limit, skip: props.history.length })
}
</script>
