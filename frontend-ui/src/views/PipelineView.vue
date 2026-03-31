<!-- Pipeline View showing a list of tasks -->

<template>
  <TasksListTab
    :filter="currentFilter"
    :filterOptions="filterOptions"
    @filter-changed="handleFilterChange"
  />
  <PipelineTable
    :headers="headers"
    :tasks="tasks"
    :paginator="paginator"
    :loading="loadingStore.isLoading"
    :loading-text="loadingStore.loadingText"
    :errors="errors"
    :canRequestTasks="canRequestTasks"
    :canUnRequestTasks="canUnRequestTasks"
    :canCancelTasks="canCancelTasks"
    @limit-changed="handleLimitChange"
    @load-data="loadData"
  />
</template>

<script setup lang="ts">
import PipelineTable from '@/components/PipelineTable.vue'
import TasksListTab from '@/components/TasksListTab.vue'
import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'
import { useRequestedTasksStore } from '@/stores/requestedTasks'
import { useTasksStore } from '@/stores/tasks'
import type { Paginator } from '@/types/base'
import type { RequestedTaskLight } from '@/types/requestedTasks'
import type { TaskLight } from '@/types/tasks'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const requestedTasksStore = useRequestedTasksStore()
const tasksStore = useTasksStore()
const authStore = useAuthStore()
const loadingStore = useLoadingStore()

// Filter options
const filterOptions = [
  { value: 'todo', label: 'TODO' },
  { value: 'doing', label: 'DOING' },
  { value: 'done', label: 'DONE' },
  { value: 'failed', label: 'FAILED' },
]
// determine the headers based on the selected table
const headers = computed(() => {
  switch (currentFilter.value) {
    case 'todo':
      return [
        { title: 'Recipe', value: 'recipe_name', sortable: false },
        { title: 'Requested', value: 'requested', sortable: false },
        { title: 'By', value: 'requested_by', sortable: false },
        { title: 'Resources', value: 'resources', sortable: false },
        { title: 'Worker', value: 'worker', sortable: false },
        canRequestTasks.value ? { title: 'Diagnose', value: 'diagnose', sortable: false } : null,
        canUnRequestTasks.value ? { title: 'Remove', value: 'remove', sortable: false } : null,
      ].filter(Boolean) as { title: string; value: string }[]
    case 'doing':
      return [
        { title: 'Recipe', value: 'recipe_name', sortable: false },
        { title: 'Started', value: 'started', sortable: false },
        { title: 'By', value: 'requested_by', sortable: false },
        { title: 'Resources', value: 'resources', sortable: false },
        { title: 'Worker', value: 'worker', sortable: false },
        canUnRequestTasks.value ? { title: 'Cancel', value: 'cancel', sortable: false } : null,
      ].filter(Boolean) as { title: string; value: string }[]
    case 'done':
      return [
        { title: 'Recipe', value: 'recipe_name', sortable: false },
        { title: 'Completed', value: 'completed', sortable: false },
        { title: 'Worker', value: 'worker', sortable: false },
        { title: 'Duration', value: 'duration', sortable: false },
      ]
    case 'failed':
      return [
        { title: 'Recipe', value: 'recipe_name', sortable: false },
        { title: 'Stopped', value: 'stopped', sortable: false },
        { title: 'Worker', value: 'worker', sortable: false },
        { title: 'Duration', value: 'duration', sortable: false },
        { title: 'Status', value: 'status', sortable: false },
        { title: 'Last Run', value: 'last_run', sortable: false },
      ]
    default:
      return []
  }
})

const currentFilter = computed(() => {
  const filter = route.query.filter
  return (Array.isArray(filter) ? filter[0] : filter) || 'todo'
})

const tasks = ref<TaskLight[] | RequestedTaskLight[]>([])
const defaultLimit = computed(() =>
  currentFilter.value == 'todo' ? requestedTasksStore.defaultLimit : tasksStore.defaultLimit,
)
const paginator = ref<Paginator>({
  page: Number(route.query.page) || 1,
  page_size: defaultLimit.value,
  skip: 0,
  limit: defaultLimit.value,
  count: 0,
})
const errors = ref<string[]>([])
const intervalId = ref<number | null>(null)

const canRequestTasks = computed(() => authStore.hasPermission('requested_tasks', 'create'))
const canUnRequestTasks = computed(() => authStore.hasPermission('requested_tasks', 'delete'))
const canCancelTasks = computed(() => authStore.hasPermission('tasks', 'cancel'))

const handleFilterChange = (newFilter: string) => {
  // Navigate to the new filter route
  router.push({
    query: {
      filter: newFilter,
    },
  })
}

async function loadData(
  limit: number,
  skip: number,
  filter?: string,
  hideLoading: boolean = false,
) {
  if (!filter) {
    filter = currentFilter.value
  }
  if (!hideLoading) {
    loadingStore.startLoading('Fetching tasks...')
    tasks.value = []
  }

  switch (filter) {
    case 'todo':
      await requestedTasksStore.fetchRequestedTasks({ limit, skip })
      tasks.value = requestedTasksStore.requestedTasks
      errors.value = requestedTasksStore.errors
      requestedTasksStore.savePaginatorLimit(limit)
      paginator.value = { ...requestedTasksStore.paginator }
      break
    case 'doing':
      await tasksStore.fetchTasks({
        limit,
        skip,
        status: [
          'reserved',
          'started',
          'scraper_started',
          'scraper_completed',
          'cancel_requested',
          'canceling',
        ],
        sort_criteria: 'doing',
      })
      tasks.value = tasksStore.tasks
      errors.value = tasksStore.errors
      tasksStore.savePaginatorLimit(limit)
      paginator.value = { ...tasksStore.paginator }
      break
    case 'done':
      await tasksStore.fetchTasks({ limit, skip, status: ['succeeded'], sort_criteria: 'done' })
      tasks.value = tasksStore.tasks
      errors.value = tasksStore.errors
      tasksStore.savePaginatorLimit(limit)
      paginator.value = { ...tasksStore.paginator }
      break
    case 'failed':
      await tasksStore.fetchTasks({
        limit,
        skip,
        status: ['scraper_killed', 'failed', 'canceled'],
        sort_criteria: 'failed',
        fetchMostRecentTasks: true,
      })
      tasks.value = tasksStore.tasks
      errors.value = tasksStore.errors
      tasksStore.savePaginatorLimit(limit)
      paginator.value = { ...tasksStore.paginator }
      break
    default:
      throw new Error(`Invalid filter: ${filter}`)
  }
  if (loadingStore.isLoading) {
    loadingStore.stopLoading()
  }
}

async function handleLimitChange(newLimit: number) {
  switch (currentFilter.value) {
    case 'todo':
      requestedTasksStore.savePaginatorLimit(newLimit)
      break
    case 'doing':
    case 'done':
    case 'failed':
      tasksStore.savePaginatorLimit(newLimit)
      break
  }

  if (paginator.value.page != 1) {
    paginator.value = {
      ...paginator.value,
      limit: newLimit,
      page: 1,
      skip: 0,
    }
  } else {
    await loadData(newLimit, 0, currentFilter.value)
  }
}

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
onMounted(async () => {
  intervalId.value = window.setInterval(async () => {
    await loadData(paginator.value.limit, paginator.value.skip, currentFilter.value, true)
  }, 60000)
})

onBeforeUnmount(() => {
  if (intervalId.value) {
    clearInterval(intervalId.value)
  }
})
</script>
