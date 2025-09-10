<template>
  <div>
    <v-card v-if="!errors.length" class="mb-4" flat>
      <v-card-text>
        <v-row>
          <v-col cols="12" sm="6" md="3">
            <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
              <div class="d-flex align-center">
                <v-icon class="mr-2" color="success">mdi-server</v-icon>
                <div>
                  <div class="text-caption text-medium-emphasis">Online workers</div>
                  <div class="text-h6">{{ onlineWorkers.length }}</div>
                </div>
              </div>
              <v-btn variant="outlined" size="x-small" @click="toggleWorkersList">
                {{ toggleText }}
              </v-btn>
            </v-sheet>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
              <div class="d-flex align-center">
                <v-progress-circular
                  :model-value="percentCpu"
                  :color="colorCpu"
                  size="44"
                  width="4"
                >
                  <span class="text-caption">{{ percentCpu }}%</span>
                </v-progress-circular>
                <div class="ml-3">
                  <div class="text-caption text-medium-emphasis">CPU</div>
                  <div class="text-body-2">{{ usageCpu }}</div>
                </div>
              </div>
            </v-sheet>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
              <div class="d-flex align-center">
                <v-progress-circular
                  :model-value="percentMemory"
                  :color="colorMemory"
                  size="44"
                  width="4"
                >
                  <span class="text-caption">{{ percentMemory }}%</span>
                </v-progress-circular>
                <div class="ml-3">
                  <div class="text-caption text-medium-emphasis">Memory</div>
                  <div class="text-body-2">{{ usageMemory }}</div>
                </div>
              </div>
            </v-sheet>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
              <div class="d-flex align-center">
                <v-progress-circular
                  :model-value="percentDisk"
                  :color="colorDisk"
                  size="44"
                  width="4"
                >
                  <span class="text-caption">{{ percentDisk }}%</span>
                </v-progress-circular>
                <div class="ml-3">
                  <div class="text-caption text-medium-emphasis">Disk</div>
                  <div class="text-body-2">{{ usageDisk }}</div>
                </div>
              </div>
            </v-sheet>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <WorkersTable
      :worker-headers="workerHeaders"
      :task-headers="taskHeaders"
      :workers="filteredWorkers"
      :paginator="paginator"
      :loading="loadingStore.isLoading"
      :loading-text="loadingStore.loadingText"
      :errors="errors"
      @limit-changed="handleLimitChange"
      @load-data="loadData"
    />

    <ErrorMessage v-for="error in errors" :key="error" :message="error" />
  </div>
</template>

<script setup lang="ts">
import ErrorMessage from '@/components/ErrorMessage.vue'
import WorkersTable from '@/components/WorkersTable.vue'
import constants from '@/constants'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useTasksStore } from '@/stores/tasks'
import { useWorkersStore } from '@/stores/workers'
import type { TaskLight } from '@/types/tasks'
import { formattedBytesSize } from '@/utils/format'

import { computed, inject, onBeforeUnmount, onMounted, ref } from 'vue'
import type { VueCookies } from 'vue-cookies'

const $cookies = inject<VueCookies>('$cookies')

// Stores
const workersStore = useWorkersStore()
const tasksStore = useTasksStore()
const notificationStore = useNotificationStore()
const loadingStore = useLoadingStore()

// Reactive state
const errors = ref<string[]>([])
const intervalId = ref<number | null>(null)
const runningTasks = ref<TaskLight[]>([])
const showingAll = ref<boolean>(!getOnlinesOnlyPreference())
const workerHeaders = [
  { title: 'Name', value: 'name' },
  { title: 'Status', value: 'status' },
  { title: 'Last seen', value: 'last_seen' },
  { title: 'Resources', value: 'resources' },
  { title: 'Contexts', value: 'contexts' },
]

const taskHeaders = [
  { title: 'Schedule', value: 'schedule' },
  { title: 'Task', value: 'task' },
  { title: 'Resources', value: 'resources' },
]
const workers = computed(() => workersStore.workers)
const paginator = computed(() => workersStore.paginator)

// Computed properties
const onlineWorkers = computed(() => workers.value.filter((worker) => worker.status === 'online'))
const filteredWorkers = computed(() => (showingAll.value ? workers.value : onlineWorkers.value))
const visibleOnlineWorkers = computed(() =>
  filteredWorkers.value.filter((worker) => worker.status === 'online'),
)
const onlineWorkerNames = computed(() => onlineWorkers.value.map((worker) => worker.name))

const tasks = computed(() => {
  // Only include tasks assigned to online workers for computing resource usage
  return runningTasks.value.filter(
    (task) => onlineWorkerNames.value.indexOf(task.worker_name) !== -1,
  )
})

const maxCpu = computed(() => {
  return visibleOnlineWorkers.value.reduce((sum, worker) => sum + worker.resources.cpu, 0)
})

const maxMemory = computed(() => {
  return visibleOnlineWorkers.value.reduce((sum, worker) => sum + worker.resources.memory, 0)
})

const maxDisk = computed(() => {
  return visibleOnlineWorkers.value.reduce((sum, worker) => sum + worker.resources.disk, 0)
})

const currentCpu = computed(() => {
  return tasks.value.reduce((sum, task) => sum + task.config.resources.cpu, 0)
})

const currentMemory = computed(() => {
  return tasks.value.reduce((sum, task) => sum + task.config.resources.memory, 0)
})

const currentDisk = computed(() => {
  return tasks.value.reduce((sum, task) => sum + task.config.resources.disk, 0)
})

const usageCpu = computed(() => `${currentCpu.value}/${maxCpu.value}`)
const usageMemory = computed(
  () => `${formattedBytesSize(currentMemory.value)}/${formattedBytesSize(maxMemory.value)}`,
)
const usageDisk = computed(
  () => `${formattedBytesSize(currentDisk.value)}/${formattedBytesSize(maxDisk.value)}`,
)
// overallProgress no longer used in UI; kept logic via per-metric percentages

const toggleText = computed(() => (showingAll.value ? 'Hide Offlines' : 'Show All'))

// Percentages for circular stats
const percentCpu = computed(() => {
  const max = maxCpu.value
  return max > 0 ? Math.min(100, Math.round((currentCpu.value * 100) / max)) : 0
})
const percentMemory = computed(() => {
  const max = maxMemory.value
  return max > 0 ? Math.min(100, Math.round((currentMemory.value * 100) / max)) : 0
})
const percentDisk = computed(() => {
  const max = maxDisk.value
  return max > 0 ? Math.min(100, Math.round((currentDisk.value * 100) / max)) : 0
})

// Colors by threshold
function pctColor(pct: number): string {
  // Green for safe (low usage), red for high usage
  if (pct >= 90) return 'error'
  if (pct >= 70) return 'warning'
  return 'success'
}
const colorCpu = computed(() => pctColor(percentCpu.value))
const colorMemory = computed(() => pctColor(percentMemory.value))
const colorDisk = computed(() => pctColor(percentDisk.value))

// Methods

function getOnlinesOnlyPreference(): boolean {
  const value = $cookies?.get('onlines-only')
  return value === null ? false : JSON.parse(value)
}

function saveOnlinesOnlyPreference(value: boolean): void {
  $cookies?.set('onlines-only', JSON.stringify(value), constants.COOKIE_LIFETIME_EXPIRY)
}

function toggleWorkersList(): void {
  showingAll.value = !showingAll.value
  saveOnlinesOnlyPreference(!showingAll.value)
}

async function loadRunningTasks(): Promise<void> {
  const tasks = await tasksStore.fetchTasks({
    limit: 200,
    skip: 0,
    status: [
      'reserved',
      'started',
      'scraper_started',
      'scraper_completed',
      'scraper_killed',
      'cancel_requested',
    ],
  })
  if (tasks) {
    runningTasks.value = tasks
    workersStore.updateWorkerTasks(tasks)
  }

  if (tasksStore.errors.length > 0) {
    errors.value = tasksStore.errors
    for (const error of errors.value) {
      notificationStore.showError(error)
    }
  }
}

async function loadData(limit: number, skip: number, hideLoading: boolean = false): Promise<void> {
  if (!hideLoading) {
    loadingStore.startLoading('Fetching workers...')
  }
  await workersStore.fetchWorkers({ limit, skip })
  workersStore.savePaginatorLimit(limit)
  errors.value = workersStore.errors
  for (const error of errors.value) {
    notificationStore.showError(error)
  }
  await loadRunningTasks()
  if (loadingStore.isLoading) {
    loadingStore.stopLoading()
  }
}

async function handleLimitChange(newLimit: number) {
  workersStore.savePaginatorLimit(newLimit)
}

// Lifecycle
onMounted(async () => {
  intervalId.value = window.setInterval(async () => {
    await loadData(paginator.value.limit, paginator.value.skip, true)
  }, 60000)
})

onBeforeUnmount(() => {
  if (intervalId.value) {
    clearInterval(intervalId.value)
  }
})
</script>
