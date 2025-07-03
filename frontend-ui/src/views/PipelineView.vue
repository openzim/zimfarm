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
    :errors="errors"
    :canUnRequestTasks="canUnRequestTasks"
    :lastRunsLoaded="lastRunsLoaded"
    :schedulesLastRuns="schedulesLastRuns"
    @limit-changed="handleLimitChange"
    @load-data="loadData"
  />
</template>

<script setup lang="ts">
import PipelineTable from '@/components/PipelineTable.vue'
import TasksListTab from '@/components/TasksListTab.vue'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useRequestedTasksStore } from '@/stores/requestedTasks'
import { useScheduleStore } from '@/stores/schedule'
import { useTasksStore } from '@/stores/tasks'
import type { MostRecentTask, Paginator } from '@/types/base'
import type { RequestedTaskLight } from '@/types/requestedTasks'
import type { TaskLight } from '@/types/tasks'
import { computed, inject, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { VueCookies } from 'vue-cookies'
import { useRouter } from 'vue-router'

const $cookies = inject<VueCookies>('$cookies')
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
        { title: 'Schedule', value: 'schedule_name' },
        { title: 'Requested', value: 'requested' },
        { title: 'By', value: 'requested_by' },
        { title: 'Resources', value: 'resources' },
        { title: 'Worker', value: 'worker' },
        canUnRequestTasks.value ? { title: 'Remove', value: 'remove' } : null,
      ].filter(Boolean) as { title: string; value: string }[]
    case 'doing':
      return [
        { title: 'Schedule', value: 'schedule_name' },
        { title: 'Started', value: 'started' },
        { title: 'Worker', value: 'worker' },
      ]
    case 'done':
      return [
        { title: 'Schedule', value: 'schedule_name' },
        { title: 'Completed', value: 'completed' },
        { title: 'Worker', value: 'worker' },
        { title: 'Duration', value: 'duration' },
      ]
    case 'failed':
      return [
        { title: 'Schedule', value: 'schedule_name' },
        { title: 'Stopped', value: 'stopped' },
        { title: 'Worker', value: 'worker' },
        { title: 'Duration', value: 'duration' },
        { title: 'Status', value: 'status' },
        { title: 'Last Run', value: 'last_run' },
      ]
    default:
      return []
  }
})

const props = withDefaults(
  defineProps<{
    filter?: string
  }>(),
  {
    filter: new URLSearchParams(window.location.search).get('filter') || 'todo',
  },
)

const lastRunsLoaded = ref(false)
const schedulesLastRuns = ref<Record<string, MostRecentTask>>({})

const currentFilter = ref(props.filter)
const tasks = ref<TaskLight[] | RequestedTaskLight[]>([])
const paginator = ref<Paginator>({
  page: 1,
  limit: $cookies?.get('pipeline-table-limit') || 20,
  count: 0,
  skip: 0,
  page_size: 20,
})
const errors = ref<string[]>([])
const intervalId = ref<number | null>(null)

const router = useRouter()

const requestedTasksStore = useRequestedTasksStore()
const tasksStore = useTasksStore()
const authStore = useAuthStore()
const loadingStore = useLoadingStore()
const scheduleStore = useScheduleStore()
const notificationStore = useNotificationStore()

const canUnRequestTasks = computed(() => authStore.hasPermission('tasks', 'unrequest'))

const handleFilterChange = (newFilter: string) => {
  currentFilter.value = newFilter

  // Navigate to the new filter route
  router.push({
    query: {
      ...router.currentRoute.value.query,
      filter: newFilter,
    },
  })
}

// Watch for filter changes and load data
watch(currentFilter, async (newFilter) => {
  await loadData(paginator.value.limit, paginator.value.skip, newFilter)
})

async function loadData(limit: number, skip: number, filter?: string) {
  if (!filter) {
    filter = currentFilter.value
  }
  lastRunsLoaded.value = false
  switch (filter) {
    case 'todo':
      await requestedTasksStore.fetchRequestedTasks(limit, skip)
      tasks.value = requestedTasksStore.requestedTasks
      paginator.value = requestedTasksStore.paginator
      errors.value = requestedTasksStore.errors
      break
    case 'doing':
      await tasksStore.fetchTasks(limit, skip, [
        'reserved',
        'started',
        'scraper_started',
        'scraper_completed',
        'cancel_requested',
      ])
      tasks.value = tasksStore.tasks
      paginator.value = tasksStore.paginator
      errors.value = tasksStore.errors
      break
    case 'done':
      await tasksStore.fetchTasks(limit, skip, ['succeeded'])
      tasks.value = tasksStore.tasks
      paginator.value = tasksStore.paginator
      errors.value = tasksStore.errors
      break
    case 'failed':
      await tasksStore.fetchTasks(limit, skip, ['scraper_killed', 'failed', 'canceled'])
      tasks.value = tasksStore.tasks
      paginator.value = tasksStore.paginator
      errors.value = tasksStore.errors
      if (errors.value.length === 0) {
        await loadLastRuns()
      }
      break
    default:
      throw new Error(`Invalid filter: ${filter}`)
  }
}

async function loadLastRuns() {
  const schedule_names = Array.from(new Set(tasks.value.map((task) => task.schedule_name)))

  // Set lastRunsLoaded to true immediately and avoid setting the loading state
  // so UI can start displaying data as it arrives
  // loadingStore.startLoading('Loading last runs...')
  lastRunsLoaded.value = true

  // Process each schedule individually with a pause between requests
  for (const schedule_name of schedule_names) {
    if (schedule_name) {
      const result = await scheduleStore.fetchSchedule(schedule_name)
      if (result && result.most_recent_task) {
        schedulesLastRuns.value[schedule_name] = result.most_recent_task
      }
      if (scheduleStore.errors.length > 0) {
        for (const error of scheduleStore.errors) {
          notificationStore.showError(
            `Failed to load last run for schedule ${schedule_name}: ${error}`,
          )
        }
      }
      // Add a 100ms pause between requests to avoid overwhelming the backend
      await new Promise((resolve) => setTimeout(resolve, constants.TASKS_LOAD_SCHEDULES_DELAY))
    }
  }
}

async function handleLimitChange(newLimit: number) {
  $cookies?.set('pipeline-table-limit', newLimit, constants.COOKIE_LIFETIME_EXPIRY)
  await loadData(newLimit, paginator.value.skip, currentFilter.value)
}

onMounted(async () => {
  await loadData(paginator.value.limit, paginator.value.skip, currentFilter.value)

  intervalId.value = window.setInterval(async () => {
    await loadData(paginator.value.limit, paginator.value.skip, currentFilter.value)
  }, 60000)
})

onBeforeUnmount(() => {
  if (intervalId.value) {
    clearInterval(intervalId.value)
  }
})
</script>
