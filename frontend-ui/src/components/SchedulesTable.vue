<template>
  <div>
    <v-card v-if="!errors.length" :class="{ loading: loading }" flat>
      <v-card-title
        v-if="showSelection || showFilters || $slots.actions"
        class="d-flex flex-column-reverse flex-sm-row align-sm-center justify-sm-end ga-2"
      >
        <slot name="actions" />
        <v-btn
          v-if="showSelection"
          size="small"
          variant="elevated"
          color="warning"
          :disabled="selectedSchedules.length === 0"
          @click="clearSelections"
        >
          <v-icon size="small" class="mr-1">mdi-checkbox-multiple-blank-outline</v-icon>
          clear selections
        </v-btn>
        <v-btn
          v-if="showFilters"
          size="small"
          variant="outlined"
          :disabled="!hasActiveFilters"
          @click="handleClearFilters"
        >
          <v-icon size="small" class="mr-1">mdi-close-circle</v-icon>
          clear filters
        </v-btn>
      </v-card-title>

      <v-data-table-server
        :headers="headers"
        :items="schedules"
        :loading="loading"
        :items-per-page="selectedLimit"
        :items-length="paginator.count"
        :items-per-page-options="limits"
        v-model:page="currentPage"
        class="elevation-1"
        item-value="name"
        :show-select="showSelection"
        :model-value="selectedSchedules"
        @update:model-value="handleSelectionChange"
        @update:options="onUpdateOptions"
        :hide-default-footer="props.paginator.count === 0"
        :hide-default-header="props.paginator.count === 0"
      >
        <template #loading>
          <div class="d-flex flex-column align-center justify-center pa-8">
            <v-progress-circular indeterminate size="64" />
            <div class="mt-4 text-body-1">{{ loadingText || 'Fetching recipes...' }}</div>
          </div>
        </template>

        <template #[`item.name`]="{ item }">
          <router-link :to="{ name: 'schedule-detail', params: { scheduleName: item.name } }">
            <span class="d-flex align-center">
              {{ item.name }}
              <v-icon v-if="!item.enabled" size="small" color="orange" class="ml-1">
                mdi-pause
              </v-icon>
            </span>
          </router-link>
        </template>

        <template #[`item.category`]="{ item }">
          {{ item.category }}
        </template>

        <template #[`item.language`]="{ item }">
          {{ item.language.name }}
        </template>

        <template #[`item.offliner`]="{ item }">
          {{ item.config.offliner || 'Unknown' }}
        </template>

        <template #[`item.requested`]="{ item }">
          <v-icon v-if="item.is_requested" size="small" color="success"> mdi-check </v-icon>
        </template>

        <template #[`item.last_task`]="{ item }">
          <div v-if="item.most_recent_task">
            <code :class="statusClass(item.most_recent_task.status)">
              {{ item.most_recent_task.status }}
            </code>
            <br />
            <TaskLink
              :id="item.most_recent_task.id"
              :updatedAt="item.most_recent_task.updated_at"
              :status="item.most_recent_task.status"
              :timestamp="item.most_recent_task.timestamp"
            />
          </div>
          <span v-else>-</span>
        </template>

        <template #no-data>
          <div class="text-center pa-4">
            <v-icon size="x-large" class="mb-2">mdi-format-list-bulleted</v-icon>
            <div class="text-h6 text-grey-darken-1 mb-2">No recipes found</div>
          </div>
        </template>
      </v-data-table-server>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import TaskLink from '@/components/TaskLink.vue'
import type { Paginator } from '@/types/base'
import type { ScheduleLight } from '@/types/schedule'
import { computed, ref, watch } from 'vue'

// Props
interface Props {
  headers: { title: string; value: string }[]
  schedules: ScheduleLight[]
  paginator: Paginator
  loading: boolean
  errors: string[]
  loadingText: string
  filters?: {
    name: string
    categories: string[]
    languages: string[]
    tags: string[]
  }
  selectedSchedules?: string[]
  showSelection?: boolean
  showFilters?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  filters: () => ({ name: '', categories: [], languages: [], tags: [] }),
  selectedSchedules: () => [],
  showSelection: true,
  showFilters: true,
})

// Define emits
const emit = defineEmits<{
  limitChanged: [limit: number]
  loadData: [limit: number, skip: number]
  clearFilters: []
  selectionChanged: [selectedSchedules: string[]]
}>()

const limits = [10, 20, 50, 100]
const selectedLimit = ref(props.paginator.limit)
const currentPage = ref(1)

const selectedSchedules = computed(() => props.selectedSchedules)

// Calculate current page from paginator (page is 1-indexed)
const computedPage = computed(() => {
  if (props.paginator.skip > 0 && props.paginator.limit > 0) {
    return Math.floor(props.paginator.skip / props.paginator.limit) + 1
  }
  return 1
})

// Check if any filters are active
const hasActiveFilters = computed(() => {
  return (
    props.filters.name.length > 0 ||
    props.filters.categories.length > 0 ||
    props.filters.languages.length > 0 ||
    props.filters.tags.length > 0
  )
})

function onUpdateOptions(options: { page: number; itemsPerPage: number }) {
  // page is 1-indexed, we need to calculate the skip for the request
  const page = options.page > 1 ? options.page - 1 : 0
  emit('loadData', options.itemsPerPage, page * options.itemsPerPage)
}

watch(
  () => props.paginator,
  (newPaginator) => {
    selectedLimit.value = newPaginator.limit
    // Sync current page with paginator
    currentPage.value = computedPage.value
  },
  { immediate: true },
)

// Watch computed page to sync with paginator changes
watch(computedPage, (newPage) => {
  if (currentPage.value !== newPage) {
    currentPage.value = newPage
  }
})

function handleSelectionChange(selection: string[]) {
  emit('selectionChanged', selection)
}

function clearSelections() {
  emit('selectionChanged', [])
}

function handleClearFilters() {
  emit('clearFilters')
}

function statusClass(status: string) {
  if (status === 'succeeded') return 'schedule-succeeded'
  else if (['failed', 'canceled', 'cancel_requested'].includes(status)) return 'schedule-failed'
  else return 'schedule-running'
}
</script>

<style scoped>
.schedule-succeeded {
  color: #4caf50;
}

.schedule-failed {
  color: #f44336;
}

.schedule-running {
  color: #ff9800;
}
</style>
