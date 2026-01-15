<template>
  <div>
    <SchedulesFilter
      v-if="ready"
      :filters="filters"
      :categories="categories"
      :languages="languages"
      :tags="tags"
      @filters-changed="handleFiltersChange"
    />
    <SchedulesTable
      v-if="ready"
      :headers="headers"
      :schedules="schedules"
      :paginator="paginator"
      :loading="loadingStore.isLoading"
      :loading-text="loadingStore.loadingText"
      :errors="errors"
      :filters="filters"
      :selected-schedules="selectedSchedules"
      :show-selection="true"
      :show-filters="true"
      @limit-changed="handleLimitChange"
      @load-data="loadData"
      @clear-filters="clearFilters"
      @selection-changed="handleSelectionChanged"
    >
      <template #actions>
        <slot
          name="actions"
          :selected-schedules="selectedSchedules"
          :requesting-text="requestingText"
          :restoring-text="restoringText"
          :handle-fetch-schedules="handleFetchSchedules"
          :handle-restore-schedules="handleRestoreSchedules"
        />
      </template>
    </SchedulesTable>
    <div v-else class="d-flex align-center justify-center" style="height: 60vh">
      <v-progress-circular indeterminate size="70" width="7" color="primary" />
    </div>

    <!-- Comment Dialog for Restore Schedule-->
    <ConfirmDialog
      v-model="showRestoreCommentDialog"
      title="Restore Recipes"
      confirm-text="Restore"
      confirm-color="success"
      :max-width="600"
      icon="mdi-archive-arrow-up"
      icon-color="success"
      :loading="restoringText !== null"
      @confirm="handleRestoreConfirm"
      @cancel="handleRestoreCancel"
    >
      <template #content>
        <div class="mb-4">
          <p class="text-body-2 text-medium-emphasis mb-3">
            You are about to restore the selected recipes. Please add an optional comment to track
            this action.
          </p>
        </div>

        <!-- Comment Input -->
        <div>
          <v-textarea
            v-model="restoreComment"
            label="Comment (optional)"
            hint="Describe the reason for restoring these recipes"
            placeholder="e.g., Restored after review, Maintenance completed, etc."
            variant="outlined"
            auto-grow
            rows="3"
            persistent-hint
          />
        </div>
      </template>
    </ConfirmDialog>
  </div>
</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import SchedulesFilter from '@/components/SchedulesFilter.vue'
import SchedulesTable from '@/components/SchedulesTable.vue'
import type { Paginator } from '@/types/base'
import constants from '@/constants'
import { useLanguageStore } from '@/stores/language'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useRequestedTasksStore } from '@/stores/requestedTasks'
import { useScheduleStore } from '@/stores/schedule'
import { useTagStore } from '@/stores/tag'
import type { ScheduleLight } from '@/types/schedule'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

// Props
interface Props {
  archived: boolean
  routeName: string
  canRequestTasks?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  canRequestTasks: false,
})

// Define headers for the table
const headers = [
  { title: 'Name', value: 'name', sortable: false },
  { title: 'Category', value: 'category', sortable: false },
  { title: 'Language', value: 'language', sortable: false },
  { title: 'Offliner', value: 'offliner', sortable: false },
  { title: 'Requested', value: 'requested', sortable: false },
  { title: 'Last Task', value: 'last_task', sortable: false },
]

// Reactive state
const schedules = ref<ScheduleLight[]>([])

const ready = ref<boolean>(false)

const errors = ref<string[]>([])

const filters = computed(() => {
  const query = router.currentRoute.value.query
  const derived = {
    name: '',
    categories: [] as string[],
    languages: [] as string[],
    tags: [] as string[],
  }

  if (query.name && typeof query.name === 'string') {
    derived.name = query.name
  }

  if (query.category) {
    const categoryValue = Array.isArray(query.category) ? query.category : [query.category]
    derived.categories = categoryValue.filter((c): c is string => c !== null)
  }

  if (query.lang) {
    const langValue = Array.isArray(query.lang) ? query.lang : [query.lang]
    derived.languages = langValue.filter((l): l is string => l !== null)
  }

  if (query.tag) {
    const tagValue = Array.isArray(query.tag) ? query.tag : [query.tag]
    derived.tags = tagValue.filter((t): t is string => t !== null)
  }

  return derived
})

const requestingText = ref<string | null>(null)
const restoringText = ref<string | null>(null)
const intervalId = ref<number | null>(null)
const selectedSchedules = ref<string[]>([])
const showRestoreCommentDialog = ref<boolean>(false)
const restoreComment = ref<string>('')

// Stores
const router = useRouter()
const route = useRoute()
const scheduleStore = useScheduleStore()
const languageStore = useLanguageStore()
const tagStore = useTagStore()
const loadingStore = useLoadingStore()
const notificationStore = useNotificationStore()
const requestedTasksStore = useRequestedTasksStore()

// Computed properties
const languages = computed(() => languageStore.languages)
const tags = computed(() => tagStore.tags)
const categories = constants.CATEGORIES

const paginator = ref<Paginator>({
  page: Number(route.query.page) || 1,
  page_size: scheduleStore.defaultLimit,
  skip: 0,
  limit: scheduleStore.defaultLimit,
  count: 0,
})

// Methods
async function loadData(limit: number, skip: number, hideLoading: boolean = false) {
  if (!hideLoading) {
    loadingStore.startLoading('Fetching recipes...')
  }
  await scheduleStore.fetchSchedules(
    limit,
    skip,
    filters.value.categories.length > 0 ? filters.value.categories : undefined,
    filters.value.languages.length > 0 ? filters.value.languages : undefined,
    filters.value.tags.length > 0 ? filters.value.tags : undefined,
    filters.value.name || undefined,
    props.archived,
  )

  schedules.value = scheduleStore.schedules
  paginator.value = { ...scheduleStore.paginator }
  scheduleStore.savePaginatorLimit(limit)
  errors.value = scheduleStore.errors
  for (const error of errors.value) {
    notificationStore.showError(error)
  }
  if (loadingStore.isLoading) {
    loadingStore.stopLoading()
  }
}

async function handleFiltersChange(newFilters: typeof filters.value) {
  updateUrlFilters(newFilters)
}

async function handleLimitChange(newLimit: number) {
  scheduleStore.savePaginatorLimit(newLimit)
  // When a limit changes, we can update the data in two ways.
  // - resetting the paginator page number to 1. The update would be emitted
  // by the table's onUpdateOptions which updates the route.
  // - explicitly loading the data. This is useful when we are on the same page
  // and the table's onUpdateOptions won't make any change in the route.
  if (paginator.value.page !== 1) {
    paginator.value = {
      ...paginator.value,
      limit: newLimit,
      page: 1,
      skip: 0,
    }
  } else {
    await loadData(newLimit, 0)
  }
}

async function clearFilters() {
  const emptyFilters = {
    name: '',
    categories: [],
    languages: [],
    tags: [],
  }
  updateUrlFilters(emptyFilters)
}

function handleSelectionChanged(newSelection: string[]) {
  selectedSchedules.value = newSelection
}

async function handleFetchSchedules() {
  if (!props.canRequestTasks) {
    return
  }

  // Called by the RequestSelectionButton component
  requestingText.value = 'Requesting tasks...'
  if (errors.value.length > 0) {
    notificationStore.showError('Not requested!')
    notificationStore.showError(`Unable to fetch recipe names: ${errors.value.join(', ')}`)
  } else {
    const scheduleNames = selectedSchedules.value.filter((name) => !!name)
    if (scheduleNames.length > 0) {
      const requestedTasks = await requestedTasksStore.requestTasks({
        scheduleNames: scheduleNames,
      })
      if (requestedTasks) {
        notificationStore.showSuccess(
          `Exactly ${requestedTasks.requested.length} selected recipe${requestedTasks.requested.length !== 1 ? 's' : ''} have been requested`,
        )
        // Clear selections after successful request
        selectedSchedules.value = []
        await loadData(paginator.value.limit, paginator.value.skip)
      } else {
        for (const error of requestedTasksStore.errors) {
          notificationStore.showError(error)
        }
      }
    }
  }
  requestingText.value = null
}

async function handleRestoreSchedules() {
  if (!props.archived) {
    return
  }

  // Show comment dialog first
  showRestoreCommentDialog.value = true
}

async function handleRestoreConfirm() {
  restoringText.value = 'Restoring recipes...'
  if (errors.value.length > 0) {
    notificationStore.showError('Not restored!')
    notificationStore.showError(`Unable to fetch recipe names: ${errors.value.join(', ')}`)
  } else {
    const scheduleNames = selectedSchedules.value.filter((name) => !!name)
    if (scheduleNames.length > 0) {
      const success = await scheduleStore.restoreSchedules(
        scheduleNames,
        restoreComment.value.trim() || undefined,
      )
      if (success) {
        notificationStore.showSuccess(
          `Exactly ${scheduleNames.length} selected recipe${scheduleNames.length !== 1 ? 's' : ''} have been restored`,
        )
        // Clear selections after successful restore
        selectedSchedules.value = []
        await loadData(paginator.value.limit, paginator.value.skip)
      } else {
        for (const error of scheduleStore.errors) {
          notificationStore.showError(error)
        }
      }
    }
  }
  restoringText.value = null
  restoreComment.value = '' // Reset comment for next use
}

function handleRestoreCancel() {
  restoreComment.value = '' // Reset comment when cancelled
}

function updateUrlFilters(sourceFilters: typeof filters.value) {
  // create query object from selected filters
  const query: Record<string, string | string[]> = {}

  if (sourceFilters.name) {
    query.name = sourceFilters.name
  }
  if (sourceFilters.categories.length === 1) {
    query.category = sourceFilters.categories[0]
  } else if (sourceFilters.categories.length > 1) {
    query.category = sourceFilters.categories
  }
  if (sourceFilters.languages.length === 1) {
    query.lang = sourceFilters.languages[0]
  } else if (sourceFilters.languages.length > 1) {
    query.lang = sourceFilters.languages
  }
  if (sourceFilters.tags.length === 1) {
    query.tag = sourceFilters.tags[0]
  } else if (sourceFilters.tags.length > 1) {
    query.tag = sourceFilters.tags
  }

  router.push({
    name: props.routeName,
    query: Object.keys(query).length > 0 ? query : undefined,
  })
}

// Lifecycle
onMounted(async () => {
  // Load initial data
  await languageStore.fetchLanguages()
  await tagStore.fetchTags()

  // Filters are derived from the route; no manual load needed

  // Set up auto-refresh
  intervalId.value = window.setInterval(async () => {
    await loadData(paginator.value.limit, paginator.value.skip, true)
  }, 60000)

  // Mark as ready to show content - the table will handle initial load via updateOptions
  ready.value = true
})

onBeforeUnmount(() => {
  if (intervalId.value) {
    clearInterval(intervalId.value)
  }
})

// Watch for route changes to update filters
watch(
  () => router.currentRoute.value.query,
  async () => {
    const query = router.currentRoute.value.query
    let page = 1
    if (query.page && typeof query.page === 'string') {
      const parsedPage = parseInt(query.page, 10)
      if (!isNaN(parsedPage) && parsedPage > 1) {
        page = parsedPage
      }
    }
    const newSkip = (page - 1) * paginator.value.limit
    await loadData(paginator.value.limit, newSkip)
  },
  { deep: true, immediate: true },
)
</script>
