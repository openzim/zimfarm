<!-- Filterable list of schedules with filtered-fire button -->

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
      :requesting-text="requestingText"
      :headers="headers"
      :schedules="schedules"
      :paginator="paginator"
      :loading="loadingStore.isLoading"
      :loading-text="loadingStore.loadingText"
      :errors="errors"
      :can-request-tasks="canRequestTasks"
      :filters="filters"
      @limit-changed="handleLimitChange"
      @load-data="loadData"
      @clear-filters="clearFilters"
      @fetch-schedules="handleFetchSchedules"
    />
    <div v-else class="d-flex align-center justify-center" style="height: 60vh">
      <v-progress-circular indeterminate size="70" width="7" color="primary" />
    </div>
  </div>
</template>

<script setup lang="ts">
import SchedulesFilter from '@/components/SchedulesFilter.vue'
import SchedulesTable from '@/components/SchedulesTable.vue'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useLanguageStore } from '@/stores/language'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useRequestedTasksStore } from '@/stores/requestedTasks'
import { useScheduleStore } from '@/stores/schedule'
import { useTagStore } from '@/stores/tag'
import type { ScheduleLight } from '@/types/schedule'
import { isFirefoxOnIOS } from '@/utils/browsers'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

// Define headers for the table
const headers = [
  { title: 'Name', value: 'name' },
  { title: 'Category', value: 'category' },
  { title: 'Language', value: 'language' },
  { title: 'Offliner', value: 'offliner' },
  { title: 'Requested', value: 'requested' },
  { title: 'Last Task', value: 'last_task' },
]

// Reactive state
const schedules = ref<ScheduleLight[]>([])
const paginator = computed(() => scheduleStore.paginator)

const blockUrlUpdates = ref<boolean>(false)
const ready = ref<boolean>(false)

const errors = ref<string[]>([])

const filters = ref({
  name: '',
  categories: [] as string[],
  languages: [] as string[],
  tags: [] as string[],
})
const requestingText = ref<string | null>(null)
const intervalId = ref<number | null>(null)

// Stores
const router = useRouter()
const scheduleStore = useScheduleStore()
const languageStore = useLanguageStore()
const tagStore = useTagStore()
const authStore = useAuthStore()
const loadingStore = useLoadingStore()
const notificationStore = useNotificationStore()
const requestedTasksStore = useRequestedTasksStore()

// Computed properties
const canRequestTasks = computed(() => authStore.hasPermission('tasks', 'request'))
const languages = computed(() => languageStore.languages)
const tags = computed(() => tagStore.tags)
const categories = constants.CATEGORIES

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
  )

  schedules.value = scheduleStore.schedules
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
  filters.value = newFilters
  updateUrl()
  await loadData(paginator.value.limit, 0)
}

async function handleLimitChange(newLimit: number) {
  scheduleStore.savePaginatorLimit(newLimit)
}

async function clearFilters() {
  filters.value = {
    name: '',
    categories: [],
    languages: [],
    tags: [],
  }
  updateUrl()
  await loadData(paginator.value.limit, 0)
}

async function handleFetchSchedules(selectedSchedules: string[]) {
  // Called by the RequestSelectionButton component
  requestingText.value = 'Requesting tasks...'
  if (errors.value.length > 0) {
    notificationStore.showError('Not requested!')
    notificationStore.showError(`Unable to fetch recipe names: ${errors.value.join(', ')}`)
  } else {
    const scheduleNames = selectedSchedules.filter((name) => !!name)
    if (scheduleNames.length > 0) {
      const requestedTasks = await requestedTasksStore.requestTasks({
        scheduleNames: scheduleNames,
      })
      if (requestedTasks) {
        notificationStore.showSuccess(
          `Exactly ${requestedTasks.requested.length} selected recipe${requestedTasks.requested.length !== 1 ? 's' : ''} have been requested`,
        )
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

function updateUrl() {
  if (blockUrlUpdates.value || isFirefoxOnIOS()) {
    return
  }

  // create query object from selected filters
  const query: Record<string, string | string[]> = {}

  if (filters.value.name) {
    query.name = filters.value.name
  }
  if (filters.value.categories.length === 1) {
    query.category = filters.value.categories[0]
  } else if (filters.value.categories.length > 1) {
    query.category = filters.value.categories
  }
  if (filters.value.languages.length === 1) {
    query.lang = filters.value.languages[0]
  } else if (filters.value.languages.length > 1) {
    query.lang = filters.value.languages
  }
  if (filters.value.tags.length === 1) {
    query.tag = filters.value.tags[0]
  } else if (filters.value.tags.length > 1) {
    query.tag = filters.value.tags
  }

  router.push({
    name: 'schedules-list',
    query: Object.keys(query).length > 0 ? query : undefined,
  })
}

function loadFiltersFromUrl() {
  const query = router.currentRoute.value.query

  if (query.name && typeof query.name === 'string') {
    filters.value.name = query.name
  }

  if (query.category) {
    const categoryValue = Array.isArray(query.category) ? query.category : [query.category]
    filters.value.categories = categoryValue.filter((c): c is string => c !== null)
  }

  if (query.lang) {
    const langValue = Array.isArray(query.lang) ? query.lang : [query.lang]
    filters.value.languages = langValue.filter((l): l is string => l !== null)
  }

  if (query.tag) {
    const tagValue = Array.isArray(query.tag) ? query.tag : [query.tag]
    filters.value.tags = tagValue.filter((t): t is string => t !== null)
  }
}

// Lifecycle
onMounted(async () => {
  // Load initial data
  await languageStore.fetchLanguages()
  await tagStore.fetchTags()

  // Load filters from URL
  loadFiltersFromUrl()

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
  () => {
    loadFiltersFromUrl()
  },
  { deep: true, immediate: true },
)
</script>
