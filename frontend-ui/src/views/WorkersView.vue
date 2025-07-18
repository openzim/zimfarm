<template>
  <div class="container">
    <!-- Progress and Stats Section -->
    <v-card v-if="!errors.length && ready" class="mb-4" flat>
      <v-card-text>
        <v-row>
          <v-col>
            <v-progress-linear
              :model-value="currentMemory"
              :max="maxMemory"
              :color="progressColor"
              height="24"
              rounded
              striped
            >
              <template #default="{ value }">
                <strong>{{ Math.ceil(value) }}%</strong>
              </template>
            </v-progress-linear>
          </v-col>
          <v-col class="d-flex align-center justify-end flex-column flex-sm-row">
            <v-chip
              variant="text"
              color="success"
              prepend-icon="mdi-server"
              density="compact"
            >
              {{ onlineWorkers.length }} online
            </v-chip>
            <ResourceBadge kind="cpu" :value="0" :human-value="usageCpu" density="compact" variant="text" />
            <ResourceBadge kind="memory" :value="0" :human-value="usageMemory" density="compact" variant="text" />
            <ResourceBadge kind="disk" :value="0" :human-value="usageDisk" density="compact" variant="text" />
            <v-btn
              variant="outlined"
              size="small"
              class="ml-2"
              @click="toggleWorkersList"
            >
              {{ toggleText }}
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Workers Table -->
    <table v-if="!errors.length && workers.length > 0" class="table table-responsive-md table-sm table-striped table-hover">
      <tbody>
        <tr v-for="row in tableRows" :key="row.id">
          <th
            v-if="row.kind === 'worker' && row.worker"
            :rowspan="row.rowspan"
            :id="row.worker.name"
            class="bg-light"
            :class="row.status === 'online' ? 'text-success' : 'text-secondary'"
          >
            <a
              :href="'#' + row.worker.name"
              :class="row.worker.name === $route.hash.split('#')[1] ? 'bg-warning' : 'bg-light'"
            >
              {{ row.worker.name }}
            </a>
          </th>

          <td v-show="row.status === 'offline'" v-if="row.kind === 'worker' && row.worker" colspan="1">
            <v-tooltip location="bottom">
              <template #activator="{ props }">
                <span v-bind="props">
                  <v-icon icon="mdi-skull-crossbones" size="small" />
                  {{ fromNow(row.worker.last_seen) }}
                </span>
              </template>
              <span>{{ formatDt(row.worker.last_seen) }}</span>
            </v-tooltip>
          </td>
          <th v-show="row.status === 'offline'" v-if="row.kind === 'worker' && row.worker" colspan="1" class="text-right">Resources</th>
          <th v-show="row.status === 'online'" v-if="row.kind === 'worker' && row.worker" colspan="2" class="text-right">Resources</th>

          <th v-if="row.kind === 'worker' && row.worker" class="text-center">
            <ResourceBadge kind="cpu" :value="row.worker.resources.cpu" />
          </th>
          <th v-if="row.kind === 'worker' && row.worker" class="text-center">
            <ResourceBadge kind="memory" :value="row.worker.resources.memory" />
          </th>
          <th v-if="row.kind === 'worker' && row.worker" class="text-center">
            <ResourceBadge kind="disk" :value="row.worker.resources.disk" />
          </th>

          <td v-if="row.kind === 'task' && row.task">
            <router-link :to="{ name: 'schedule-detail', params: { scheduleName: row.task.schedule_name } }">
              {{ row.task.schedule_name }}
            </router-link>
          </td>
          <td v-if="row.kind === 'task' && row.task">
            <TaskLink
              :id="row.task.id"
              :updated-at="startedOn(row.task)"
            />
          </td>
          <td v-if="row.kind === 'task' && row.task" class="text-center">{{ row.task.config.resources.cpu }}</td>
          <td v-if="row.kind === 'task' && row.task" class="text-center">{{ formattedBytesSize(row.task.config.resources.memory) }}</td>
          <td v-if="row.kind === 'task' && row.task" class="text-center">{{ formattedBytesSize(row.task.config.resources.disk) }}</td>
        </tr>
      </tbody>
    </table>

    <!-- Error Messages -->
    <ErrorMessage v-for="error in errors" :key="error" :message="error" />
  </div>
</template>

<script setup lang="ts">
import ErrorMessage from '@/components/ErrorMessage.vue'
import ResourceBadge from '@/components/ResourceBadge.vue'
import TaskLink from '@/components/TaskLink.vue'
import constants from '@/constants'
import { useNotificationStore } from '@/stores/notification'
import { useTasksStore } from '@/stores/tasks'
import { useWorkersStore } from '@/stores/workers'
import type { TaskLight } from '@/types/tasks'
import type { Worker } from '@/types/workers'
import { formatDt, formattedBytesSize, fromNow } from '@/utils/format'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { computed, inject, onBeforeUnmount, onMounted, ref } from 'vue'
import type { VueCookies } from 'vue-cookies'

const $cookies = inject<VueCookies>('$cookies')

// Stores
const workersStore = useWorkersStore()
const tasksStore = useTasksStore()
const notificationStore = useNotificationStore()

// Reactive state
const ready = ref<boolean>(false)
const errors = ref<string[]>([])
const showingAll = ref(!getOnlinesOnlyPreference())
const intervalId = ref<number | null>(null)
const runningTasks = ref<TaskLight[]>([])

// Computed properties
const allWorkers = computed(() => workersStore.workers)
const onlineWorkers = computed(() => allWorkers.value.filter(worker => worker.status === 'online'))
const workers = computed(() => showingAll.value ? allWorkers.value : onlineWorkers.value)
const workerNames = computed(() => workers.value.map(worker => worker.name))

const tasks = computed(() => {
  return runningTasks.value.filter(task => workerNames.value.indexOf(task.worker_name) !== -1)
})

const toggleText = computed(() => showingAll.value ? 'Hide Offlines' : 'Show All')

const progressColor = computed(() => {
  const progress = Number(overallProgress.value)
  if (progress <= 10 || progress > 100) return 'error'
  if (progress <= 50) return 'warning'
  if (progress <= 70) return 'info'
  return 'success'
})

const maxCpu = computed(() => {
  return onlineWorkers.value.reduce((sum, worker) => sum + worker.resources.cpu, 0)
})

const maxMemory = computed(() => {
  return onlineWorkers.value.reduce((sum, worker) => sum + worker.resources.memory, 0)
})

const maxDisk = computed(() => {
  return onlineWorkers.value.reduce((sum, worker) => sum + worker.resources.disk, 0)
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
const usageMemory = computed(() => `${formattedBytesSize(currentMemory.value)}/${formattedBytesSize(maxMemory.value)}`)
const usageDisk = computed(() => `${formattedBytesSize(currentDisk.value)}/${formattedBytesSize(maxDisk.value)}`)
const overallProgress = computed(() => {
  return maxMemory.value ? (currentMemory.value * 100 / maxMemory.value).toFixed(0) : 0
})

// Table structure with rowspans like the old version
const tableRows = computed(() => {
  const rows: Array<{
    id: string
    kind: 'worker' | 'task'
    status: string
    rowspan: number
    worker?: Worker
    task?: TaskLight
  }> = []

  for (const worker of workers.value) {
    const status = worker.status
    const rowspan = 1 + worker.tasks.length
    rows.push({
      id: worker.name,
      kind: 'worker',
      status,
      rowspan,
      worker,
    })

    for (const task of worker.tasks) {
      rows.push({
        id: task.id,
        kind: 'task',
        status,
        rowspan: 1,
        task,
      })
    }
  }

  return rows
})

// Methods
function getOnlinesOnlyPreference(): boolean {
  const value = $cookies?.get('onlines-only')
  return value === null ? false : JSON.parse(value)
}

function saveOnlinesOnlyPreference(value: boolean): void {
  $cookies?.set('onlines-only', JSON.stringify(value), constants.COOKIE_LIFETIME_EXPIRY)
}

function startedOn(task: TaskLight): string {
  return getTimestampStringForStatus(task.timestamp, 'started') || 'not started'
}

function toggleWorkersList(): void {
  showingAll.value = !showingAll.value
  saveOnlinesOnlyPreference(!showingAll.value)
}

async function loadRunningTasks(): Promise<void> {
  const tasks = await tasksStore.fetchTasks({limit: 200, skip: 0, status: [
    'reserved',
    'started',
    'scraper_started',
    'scraper_completed',
    'scraper_killed',
    'cancel_requested',
  ]})

  // Clear existing tasks and add new ones to workers
  workersStore.clearWorkerTasks()
  if (tasks) {
    runningTasks.value = tasks
    for (const task of tasks) {
      workersStore.addTaskToWorker(task)
    }
    ready.value = true
  }

  if (tasksStore.errors.length > 0) {
    errors.value = tasksStore.errors
    for (const error of errors.value) {
      notificationStore.showError(error)
    }
  }
}

async function loadData(): Promise<void> {
  await workersStore.fetchWorkers({limit: 100})
  await loadRunningTasks()
}

// Lifecycle
onMounted(async () => {
  await loadData()

  intervalId.value = window.setInterval(async () => {
    await loadData()
  }, 60000)
})

onBeforeUnmount(() => {
  if (intervalId.value) {
    clearInterval(intervalId.value)
  }
})
</script>

<style scoped>

.bg-light {
  background-color: #f8f9fa !important;
}

.text-success {
  color: #28a745 !important;
}

.text-secondary {
  color: #6c757d !important;
}

.bg-warning {
  background-color: #ffc107 !important;
}

.badge {
  display: inline-block;
  padding: 0.25em 0.4em;
  font-size: 75%;
  font-weight: 700;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
  vertical-align: baseline;
  border-radius: 0.25rem;
}

.badge-light {
  color: #212529;
  background-color: #f8f9fa;
}


.table {
  width: 100%;
  margin-bottom: 1rem;
  color: #212529;
  border-collapse: collapse;
}

.table-responsive-md {
  overflow-x: auto;
}

.table-sm td,
.table-sm th {
  padding: 0.3rem;
}

.table-striped tbody tr:nth-of-type(odd) {
  background-color: rgba(0, 0, 0, 0.05);
}

.table-hover tbody tr:hover {
  background-color: rgba(0, 0, 0, 0.075);
}

.table th,
.table td {
  padding: 0.75rem;
  vertical-align: top;
  border-top: 1px solid #dee2e6;
}

.table thead th {
  vertical-align: bottom;
  border-bottom: 2px solid #dee2e6;
}
</style>
