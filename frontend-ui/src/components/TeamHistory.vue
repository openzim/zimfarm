<!-- Team history: list of entries, select any two to compare with DiffViewer -->
<template>
  <v-container fluid>
    <template v-if="loading && history.length === 0">
      <div class="d-flex flex-column justify-center align-center pa-8">
        <v-progress-circular indeterminate color="primary" size="64" />
        <span class="mt-4">Loading Team history...</span>
      </div>
    </template>

    <template v-else-if="history.length > 0">
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

              <template v-slot:append>
                <div class="d-flex align-center ga-2">
                  <v-btn
                    v-if="canUpdateTeams"
                    icon="mdi-restore"
                    variant="text"
                    size="small"
                    color="primary"
                    @click.stop="confirmRevert(item, index)"
                    :disabled="index === 0"
                    :title="index === 0 ? 'This is the current version' : 'Revert to this version'"
                  >
                    <v-icon>mdi-restore</v-icon>
                  </v-btn>
                </div>
              </template>
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

            <DiffViewer :differences="teamDifferences" />
          </v-card-text>
        </v-card>
      </template>
    </template>

    <template v-else>
      <v-row>
        <v-col cols="12" class="d-flex flex-column align-center justify-center">
          <v-icon size="x-large" color="grey" class="mb-4">mdi-history</v-icon>
          <div class="text-h6 text-medium-emphasis">No history available for this team</div>
        </v-col>
      </v-row>
    </template>

    <!-- Revert Confirmation Dialog -->
    <ConfirmDialog
      v-model="showRevertDialog"
      title="Revert to Previous Version"
      confirm-text="Revert"
      cancel-text="Cancel"
      confirm-color="info"
      icon="mdi-restore"
      icon-color="info"
      :max-width="600"
      :loading="isReverting"
      @confirm="handleRevertConfirm"
      @cancel="handleCancelRevert"
    >
      <template #content>
        <div v-if="selectedHistoryItem">
          <v-alert type="info" variant="tonal" density="compact" class="mb-4">
            You are about to revert team <strong>{{ teamName }}</strong> to a previous version.
            Review the changes below:
          </v-alert>

          <DiffViewer :differences="teamDifferences" />

          <!-- Comment Input -->
          <div class="mt-4">
            <v-textarea
              v-model="revertComment"
              label="Comment (optional)"
              variant="outlined"
              auto-grow
              rows="3"
              placeholder="Add a note about why you're reverting to this version..."
            />
          </div>
        </div>
      </template>
    </ConfirmDialog>
  </v-container>
</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DiffViewer from '@/components/DiffViewer.vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useTeamHistoryStore } from '@/stores/teamHistory'
import type { Paginator } from '@/types/base'
import type { Team, TeamHistory } from '@/types/team'
import { formatDt } from '@/utils/format'
import type * as DeepDiff from 'deep-diff'
import { diff } from 'deep-diff'
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps<{
  history: TeamHistory[]
  hasMore: boolean
  loading: boolean
  paginator: Paginator
  teamName: string
}>()

const emit = defineEmits<{
  load: [{ limit: number; skip: number }]
  revert: [team: Team]
}>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const teamHistoryStore = useTeamHistoryStore()

// New state for multi-selection
const selectedItems = ref<Set<number>>(new Set())
const showDiffViewer = ref(false)
const showRevertDialog = ref(false)
const selectedHistoryItem = ref<TeamHistory | null>(null)
const isReverting = ref(false)
const isRevertMode = ref(false)
const revertComment = ref('')

const canUpdateTeams = computed(() => authStore.hasPermission('teams', 'update'))

const selectedItemsArray = computed(() => {
  const items = Array.from(selectedItems.value)
    .map((index) => props.history[index])
    .filter(Boolean)

  // In revert mode, sort current->previous (descending)
  // In normal compare mode, sort previous->current (ascending)
  if (isRevertMode.value) {
    return items.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  }

  return items.sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime())
})

const teamDifferences = computed(
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

const toggleHistoryItemSelection = async (item: TeamHistory, index: number) => {
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

  updateUrlQueryParams()
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
    return
  }

  const missingIds = []
  if (index1 === -1) missingIds.push(id1)
  if (index2 === -1) missingIds.push(id2)

  if (missingIds.length > 0) {
    try {
      // Fetch missing entries in parallel
      const fetchPromises = missingIds.map((id) =>
        teamHistoryStore.fetchHistoryEntry(props.teamName, id),
      )

      await Promise.all(fetchPromises)

      // After fetching, find the indices again
      const newIndex1 = teamHistoryStore.history.findIndex((item: TeamHistory) => item.id === id1)
      const newIndex2 = teamHistoryStore.history.findIndex((item: TeamHistory) => item.id === id2)

      if (newIndex1 !== -1 && newIndex2 !== -1) {
        selectedItems.value = new Set([newIndex1, newIndex2])
        showDiffViewer.value = true
      }
    } catch (error) {
      console.error('Failed to fetch history entries from URL', error)
    }
  }
}

const backToHistoryList = () => {
  showDiffViewer.value = false
  selectedItems.value.clear()
  updateUrlQueryParams()
}

const confirmRevert = (item: TeamHistory, index: number) => {
  selectedHistoryItem.value = item
  isRevertMode.value = true

  // Select current (0) and target (index) to trigger diff computation
  selectedItems.value = new Set([0, index])

  // Check if there are any differences
  if (!teamDifferences.value || teamDifferences.value.length === 0) {
    selectedHistoryItem.value = null
    isRevertMode.value = false
    selectedItems.value.clear()
    notificationStore.showInfo(
      'No differences found between current and selected version. Nothing to revert.',
    )
    return
  }

  showRevertDialog.value = true
}

const handleCancelRevert = () => {
  showRevertDialog.value = false
  isRevertMode.value = false
  revertComment.value = ''
  selectedItems.value.clear()
}

const handleRevertConfirm = async () => {
  if (!selectedHistoryItem.value) {
    return
  }

  isReverting.value = true
  const comment = revertComment.value.trim() || undefined
  const reverted = await teamHistoryStore.revertToHistory(
    props.teamName,
    selectedHistoryItem.value.id,
    comment,
  )

  if (reverted) {
    notificationStore.showSuccess(
      `Successfully reverted to version ${selectedHistoryItem.value.id.substring(0, 8)}`,
    )
    showRevertDialog.value = false
    selectedHistoryItem.value = null
    isRevertMode.value = false
    revertComment.value = ''
    selectedItems.value.clear()
    updateUrlQueryParams()
    emit('revert', reverted)
  } else {
    for (const error of teamHistoryStore.errors) {
      notificationStore.showError(error)
    }
  }
  isReverting.value = false
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
