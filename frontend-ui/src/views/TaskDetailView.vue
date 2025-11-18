<!-- Task Detail View
  - listing all info
  - fire schedule button -->

<template>
  <v-container>
    <!-- Cancel Button -->
    <v-row v-if="canCancel" class="mb-4">
      <v-spacer />
      <v-btn
        v-show="canCancelTasks"
        color="error"
        variant="elevated"
        size="small"
        @click="cancel"
        class="mr-4"
      >
        <v-icon class="mr-2">mdi-stop-circle</v-icon>
        Cancel
      </v-btn>
    </v-row>

    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12" sm="4" md="3" lg="2">
        <code class="text-h6">#{{ shortId }}</code>
      </v-col>
      <v-col cols="12" sm="8" md="9" lg="10" v-if="scheduleName">
        <router-link
          :to="{
            name: 'schedule-detail',
            params: { scheduleName: scheduleName },
          }"
          class="text-decoration-none"
        >
          <code class="text-h6 text-primary">
            {{ scheduleName }}
          </code>
        </router-link>
      </v-col>
    </v-row>

    <!-- Content -->
    <div v-if="!error && task">
      <!-- Tabs -->
      <v-tabs v-model="currentTab" class="mb-4" color="primary" slider-color="primary">
        <v-tab
          value="details"
          :to="{ name: 'task-detail', params: { id: props.id } }"
          base-color="primary"
        >
          Info
        </v-tab>
        <v-tab
          base-color="primary"
          value="debug"
          :to="{
            name: 'task-detail-tab',
            params: { id: props.id, selectedTab: 'debug' },
          }"
        >
          Debug
        </v-tab>
      </v-tabs>

      <!-- Details Tab -->
      <v-window v-model="currentTab">
        <v-window-item value="details">
          <v-card>
            <v-card-text>
              <v-table>
                <tbody>
                  <tr>
                    <th class="text-left w-20">ID</th>
                    <td>
                      <code>{{ id }}</code
                      >,
                      <a target="_blank" :href="webApiUrl + '/tasks/' + id">
                        document <v-icon size="small">mdi-open-in-new</v-icon>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left w-20">Recipe</th>
                    <td>
                      <span v-if="task.schedule_name === null || task.schedule_name === 'none'">
                        {{ task.original_schedule_name }}
                      </span>
                      <router-link
                        v-else
                        :to="{
                          name: 'schedule-detail',
                          params: { scheduleName: task.schedule_name },
                        }"
                      >
                        {{ task.schedule_name }}
                      </router-link>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left w-20">Status</th>
                    <td>
                      <code class="text-pink-accent-2">{{ task.status }}</code>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left w-20">Worker</th>
                    <td>
                      <router-link
                        :to="{ name: 'worker-detail', params: { workerName: task.worker_name } }"
                        class="text-decoration-none"
                      >
                        {{ task.worker_name }}
                      </router-link>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left w-20">Started On</th>
                    <td>
                      {{ formatDt(startedOn) }}, after
                      <strong>{{ pipeDuration }} in pipe</strong>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left w-20">Duration</th>
                    <td>
                      {{ taskDuration }}<span v-if="isRunning"> (<strong>Ongoing</strong>)</span>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left align-top pa-4 w-20">Events</th>
                    <td>
                      <v-table density="compact" class="events-table">
                        <tbody>
                          <tr v-for="event in task.events" :key="event.code">
                            <td>
                              <code class="text-pink-accent-2">{{ event.code }}</code>
                            </td>
                            <td>{{ formatDt(event.timestamp) }}</td>
                            <td v-if="event.code === 'requested'">
                              {{ task.requested_by }}
                            </td>
                            <td
                              v-else-if="
                                event.code === 'cancel_requested' &&
                                task.status === 'cancel_requested'
                              "
                            >
                              {{ task.canceled_by }}
                            </td>
                            <td v-else-if="event.code === 'canceled'">
                              {{ task.canceled_by }}
                            </td>
                            <td v-else />
                          </tr>
                        </tbody>
                      </v-table>
                    </td>
                  </tr>
                  <tr v-if="task.files">
                    <th class="text-left w-20">Files</th>
                    <td>
                      <v-table density="compact">
                        <thead>
                          <tr>
                            <th>Filename</th>
                            <th>Size</th>
                            <th>Created After</th>
                            <th>Upload Duration</th>
                            <th>Quality</th>
                            <th>Info</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="file in sortedFiles" :key="file.name">
                            <td>
                              <a
                                target="_blank"
                                :href="
                                  kiwixDownloadUrl + task.config.warehouse_path + '/' + file.name
                                "
                              >
                                {{ file.name }}
                              </a>
                            </td>
                            <td>{{ formattedBytesSize(file.size) }}</td>
                            <td>
                              <v-tooltip :text="formatDt(file.created_timestamp)">
                                <template #activator="{ props }">
                                  <span v-bind="props">{{ createdAfter(file, task) }}</span>
                                </template>
                              </v-tooltip>
                            </td>
                            <td v-if="file.uploaded_timestamp">
                              <v-tooltip :text="formatDt(file.uploaded_timestamp)">
                                <template #activator="{ props }">
                                  <span v-bind="props">{{ uploadDuration(file) }}</span>
                                </template>
                              </v-tooltip>
                            </td>
                            <td v-else>-</td>
                            <td v-if="file.check_result !== undefined">
                              <div class="d-flex flex-sm-column flex-lg-row align-center">
                                <v-tooltip :text="`Return code: ${file.check_result}`">
                                  <template #activator="{ props }">
                                    <v-icon
                                      v-bind="props"
                                      :color="file.check_result === 0 ? 'success' : 'error'"
                                      size="small"
                                    >
                                      {{
                                        file.check_result === 0
                                          ? 'mdi-check-circle'
                                          : 'mdi-close-circle'
                                      }}
                                    </v-icon>
                                  </template>
                                </v-tooltip>
                                <v-btn
                                  v-if="file.check_filename"
                                  variant="text"
                                  size="small"
                                  class="ml-2"
                                  :href="zimfarmChecksUrl(file.check_filename)"
                                  target="_blank"
                                  rel="noopener noreferrer"
                                >
                                  <v-icon>mdi-download</v-icon>
                                </v-btn>
                              </div>
                            </td>
                            <td v-else>-</td>
                            <td v-if="file.info">
                              <v-menu location="left" :close-on-content-click="false">
                                <template #activator="{ props }">
                                  <v-btn v-bind="props" variant="text" size="small">
                                    <v-icon>mdi-information</v-icon>
                                  </v-btn>
                                </template>
                                <FileInfoTable :file-info="file.info" />
                              </v-menu>
                            </td>
                            <td v-else>-</td>
                          </tr>
                        </tbody>
                      </v-table>
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </v-card-text>
          </v-card>
        </v-window-item>

        <!-- Debug Tab -->
        <v-window-item value="debug">
          <v-card>
            <v-card-text>
              <v-table>
                <tbody>
                  <tr v-if="task.config">
                    <th class="text-left w-20">Offliner</th>
                    <td>
                      <a target="_blank" :href="imageUrl">
                        <code>{{ imageHuman }}</code>
                      </a>
                      (<code>{{ task.config.offliner.offliner_id }}</code
                      >)
                    </td>
                  </tr>
                  <tr v-if="task.config">
                    <th class="text-left w-20">Offliner Definition</th>
                    <td>
                      <code>{{ task.version }}</code>
                    </td>
                  </tr>
                  <tr v-if="task.config">
                    <th class="text-left w-20">Resources</th>
                    <td>
                      <ResourceBadge kind="cpu" :value="task.config.resources.cpu" />
                      <ResourceBadge kind="memory" :value="task.config.resources.memory" />
                      <ResourceBadge kind="disk" :value="task.config.resources.disk" />
                      <ResourceBadge
                        kind="shm"
                        :value="task.config.resources.shm"
                        v-if="task.config.resources.shm"
                      />
                      <v-chip v-if="task.config.monitor" color="warning" size="small" class="ml-2">
                        <a target="_blank" :href="monitoringUrl" class="text-decoration-none">
                          <v-icon size="small" class="mr-1">mdi-bug</v-icon>
                          monitored
                        </a>
                      </v-chip>
                    </td>
                  </tr>
                  <tr v-if="task.config">
                    <th class="text-left w-20">Platform</th>
                    <td>{{ task.config.platform || '-' }}</td>
                  </tr>
                  <tr v-if="task.config">
                    <th class="text-left align-top pa-4 w-20">Config</th>
                    <td>
                      <FlagsList
                        :offliner="task.config.offliner"
                        :secret-fields="secretFields"
                        :shrink="false"
                      />
                    </td>
                  </tr>
                  <tr v-if="taskContainer?.command">
                    <th class="text-left align-top pa-4 w-20">
                      Command
                      <v-btn variant="text" size="small" class="ml-2" @click="copyCommand(command)">
                        <v-icon>mdi-content-copy</v-icon>
                      </v-btn>
                    </th>
                    <td class="py-2">
                      <code class="command text-pink-accent-2 text-wrap">{{ command }}</code>
                    </td>
                  </tr>
                  <tr v-if="taskContainer?.exit_code != null">
                    <th class="text-left w-20">Exit-code</th>
                    <td>
                      <code class="text-pink-accent-2">{{ taskContainer.exit_code }}</code>
                    </td>
                  </tr>
                  <tr v-if="hasStats">
                    <th class="text-left w-20">Stats</th>
                    <td>
                      <div class="d-flex flex-wrap ga-2">
                        <v-tooltip
                          v-if="maxMemory"
                          text="Maximum memory used during task execution"
                        >
                          <template #activator="{ props }">
                            <v-chip v-bind="props" size="small">
                              <v-icon size="small" class="mr-1">mdi-memory</v-icon>
                              {{ maxMemory }} (max)
                            </v-chip>
                          </template>
                        </v-tooltip>
                        <v-tooltip
                          v-if="maxDisk"
                          text="Maximum disk space used during task execution"
                        >
                          <template #activator="{ props }">
                            <v-chip v-bind="props" size="small">
                              <v-icon size="small" class="mr-1">mdi-harddisk</v-icon>
                              {{ maxDisk }} (max)
                            </v-chip>
                          </template>
                        </v-tooltip>
                        <v-tooltip
                          v-if="hasCpuStats && cpuStats && cpuStats.max !== null"
                          text="Maximum CPU usage percentage during task execution"
                        >
                          <template #activator="{ props }">
                            <v-chip v-bind="props" size="small">
                              <v-icon size="small" class="mr-1">mdi-cpu-64-bit</v-icon>
                              {{ cpuStats.max.toFixed(1) }}% (max)
                            </v-chip>
                          </template>
                        </v-tooltip>
                        <v-tooltip
                          v-if="hasCpuStats && cpuStats && cpuStats.avg !== null"
                          text="Average CPU usage percentage during task execution"
                        >
                          <template #activator="{ props }">
                            <v-chip v-bind="props" size="small">
                              <v-icon size="small" class="mr-1">mdi-chart-line</v-icon>
                              {{ cpuStats.avg.toFixed(1) }}% (avg)
                            </v-chip>
                          </template>
                        </v-tooltip>
                      </div>
                    </td>
                  </tr>
                  <tr v-if="taskProgress">
                    <th class="text-left w-20">Scraper progress</th>
                    <td>
                      {{ taskProgress.overall }}% ({{ taskProgress.done }} /
                      {{ taskProgress.total }})
                    </td>
                  </tr>
                  <tr v-if="taskContainer?.stdout || taskContainer?.stderr || taskContainer?.log">
                    <td colspan="2">
                      <small>Logs uses UTC Timezone. {{ offsetString }}</small>
                    </td>
                  </tr>
                  <tr v-if="taskContainer?.stdout">
                    <th class="text-left w-20">
                      Scraper stdout
                      <v-btn
                        variant="text"
                        size="small"
                        class="ml-2"
                        @click="copyOutput(taskContainer.stdout, 'stdout')"
                      >
                        <v-icon>mdi-content-copy</v-icon>
                      </v-btn>
                    </th>
                    <td>
                      <pre class="stdout">{{ taskContainer.stdout }}</pre>
                    </td>
                  </tr>
                  <tr v-if="taskContainer?.stderr">
                    <th class="text-left w-20">
                      Scraper stderr
                      <v-btn
                        variant="text"
                        size="small"
                        class="ml-2"
                        @click="copyOutput(taskContainer.stderr, 'stderr')"
                      >
                        <v-icon>mdi-content-copy</v-icon>
                      </v-btn>
                    </th>
                    <td>
                      <pre class="stderr">{{ taskContainer.stderr }}</pre>
                    </td>
                  </tr>
                  <tr v-if="taskContainer?.log">
                    <th class="text-left w-20">Scraper Log</th>
                    <td>
                      <v-btn variant="outlined" size="small" target="_blank" :href="zimfarmLogsUrl">
                        Download log
                      </v-btn>
                    </td>
                  </tr>
                  <tr v-if="taskContainer?.artifacts">
                    <th class="text-left w-20 align-top pa-4">Scraper Artifacts</th>
                    <td>
                      <v-btn
                        variant="outlined"
                        size="small"
                        target="_blank"
                        :href="zimfarmArtifactsUrl"
                      >
                        Download artifacts
                      </v-btn>
                    </td>
                  </tr>
                  <tr v-if="taskDebug.exception">
                    <th class="text-left w-20 align-top pa-4">Exception</th>
                    <td>
                      <pre>{{ taskDebug.exception }}</pre>
                    </td>
                  </tr>
                  <tr v-if="taskDebug.traceback">
                    <th class="text-left w-20 align-top pa-4">Traceback</th>
                    <td>
                      <pre>{{ taskDebug.traceback }}</pre>
                    </td>
                  </tr>
                  <tr v-if="taskDebug.log">
                    <th class="text-left w-20 align-top pa-4">Task-worker Log</th>
                    <td>
                      <pre>{{ taskDebug.log }}</pre>
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </v-card-text>
          </v-card>
        </v-window-item>
      </v-window>
    </div>

    <!-- Error Message -->
    <ErrorMessage v-if="error" :message="error" />
  </v-container>
</template>

<script setup lang="ts">
import ErrorMessage from '@/components/ErrorMessage.vue'
import FileInfoTable from '@/components/FileInfoTable.vue'
import FlagsList from '@/components/FlagsList.vue'
import ResourceBadge from '@/components/ResourceBadge.vue'
import type { Config } from '@/config'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useOfflinerStore } from '@/stores/offliner'
import { useTasksStore } from '@/stores/tasks'
import type { OfflinerDefinition } from '@/types/offliner'
import type { Task, TaskFile } from '@/types/tasks'
import {
  formatDt,
  formatDurationBetween,
  formattedBytesSize,
  getTimezoneDetails,
} from '@/utils/format'
import {
  artifactsUrl,
  checkUrl,
  getSecretFields,
  imageHuman as imageHumanFn,
  imageUrl as imageUrlFn,
  logsUrl,
} from '@/utils/offliner'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { computed, inject, nextTick, onMounted, ref, watch } from 'vue'

// Props
interface Props {
  id: string
  selectedTab?: string
}

const props = withDefaults(defineProps<Props>(), {
  selectedTab: 'details',
})

// Inject config
const config = inject<Config>(constants.config)
if (!config) {
  throw new Error('Config is not defined')
}

// Stores
const authStore = useAuthStore()
const loadingStore = useLoadingStore()
const notificationStore = useNotificationStore()
const tasksStore = useTasksStore()
const offlinerStore = useOfflinerStore()

// Reactive data
const task = ref<Task | null>(null)
const error = ref<string | null>(null)
const currentTab = ref(props.selectedTab)
const flagsDefinition = ref<OfflinerDefinition[]>([])

// Computed properties
const offsetString = computed(() => {
  const tzDetails = getTimezoneDetails()
  return `You are ${tzDetails.tz} (${tzDetails.offsetstr}).`
})

const shortId = computed(() => {
  return props.id.substring(0, 8)
})

const isRunning = computed(() => {
  return !['failed', 'canceled', 'succeeded', 'cancel_requested'].includes(task.value?.status || '')
})

const scheduleName = computed(() => {
  return task.value?.schedule_name || null
})

const taskContainer = computed(() => {
  return task.value?.container || null
})

const taskProgress = computed(() => {
  return taskContainer.value?.progress || null
})

const secretFields = computed(() => getSecretFields(flagsDefinition.value))

const taskDebug = computed(() => {
  return task.value?.debug || {}
})

const taskDuration = computed(() => {
  if (!task.value?.events) return ''
  const first = getTimestampStringForStatus(task.value?.timestamp, 'started', '')
  if (!first) return 'Not actually started ⌛'
  if (isRunning.value) {
    return formatDurationBetween(first, new Date().toISOString())
  }
  const last = task.value.updated_at
  return formatDurationBetween(first, last)
})

const startedOn = computed(() =>
  getTimestampStringForStatus(
    task.value?.timestamp,
    'started',
    getTimestampStringForStatus(task.value?.timestamp, 'reserved'),
  ),
)

const pipeDuration = computed(() =>
  formatDurationBetween(
    getTimestampStringForStatus(task.value?.timestamp, 'requested'),
    getTimestampStringForStatus(
      task.value?.timestamp,
      'started',
      getTimestampStringForStatus(task.value?.timestamp, 'reserved'),
    ),
  ),
)

const sortedFiles = computed(() => {
  if (!task.value?.files) return []
  return Object.values(task.value.files).sort((a, b) => {
    return new Date(a.created_timestamp).getTime() - new Date(b.created_timestamp).getTime()
  })
})

const command = computed(() => {
  return taskContainer.value?.command?.join(' ') || ''
})

const imageHuman = computed(() => {
  if (!task.value?.config) return ''
  return imageHumanFn(task.value.config)
})

const imageUrl = computed(() => {
  if (!task.value?.config) return ''
  return imageUrlFn(task.value.config)
})

const canCancel = computed(() => {
  return task.value && isRunning.value && task.value.id
})

const maxMemory = computed(() => {
  try {
    return formattedBytesSize(taskContainer.value?.stats?.memory?.max || 0)
  } catch {
    return null
  }
})

const maxDisk = computed(() => {
  try {
    return formattedBytesSize(taskContainer.value?.stats?.disk?.max || 0)
  } catch {
    return null
  }
})

const cpuStats = computed(() => {
  const stats = taskContainer.value?.stats?.cpu
  if (!stats) return null
  return {
    max: stats.max ?? null,
    avg: stats.avg ?? null,
  }
})

const hasCpuStats = computed(() => {
  return cpuStats.value && (cpuStats.value.max !== null || cpuStats.value.avg !== null)
})

const hasStats = computed(() => {
  return maxMemory.value || maxDisk.value || hasCpuStats.value
})

const monitoringUrl = computed(() => {
  return `http://monitoring.openzim.org/host/${scheduleName.value}_${shortId.value}.${
    task.value?.worker_name
  }/#menu_cgroup_zimscraper_${task.value?.original_schedule_name}_${
    shortId.value
  }_submenu_cpu;after=${new Date(
    getTimestampStringForStatus(task.value?.timestamp, 'scraper_started', '') || 0,
  ).getTime()};before=${new Date(
    getTimestampStringForStatus(task.value?.timestamp, 'scraper_completed', '') || 0,
  ).getTime()};theme=slate;utc=Africa/Bamako`
})

const webApiUrl = computed(() => config.ZIMFARM_WEBAPI)
const kiwixDownloadUrl = computed(() => config.ZIMFARM_ZIM_DOWNLOAD_URL)
const zimfarmLogsUrl = computed(() => (task.value ? logsUrl(task.value) : ''))
const zimfarmArtifactsUrl = computed(() => (task.value ? artifactsUrl(task.value) : ''))

// Permission computed properties
const canCancelTasks = computed(() => authStore.hasPermission('tasks', 'cancel'))
const canViewTaskSecrets = computed(() => authStore.hasPermission('tasks', 'secrets'))

// Methods
const createdAfter = (file: TaskFile, taskData: Task) => {
  return formatDurationBetween(
    getTimestampStringForStatus(taskData.timestamp, 'scraper_started'),
    file.created_timestamp,
  )
}

const zimfarmChecksUrl = (fileName: string) => (task.value ? checkUrl(task.value, fileName) : '')

const uploadDuration = (file: TaskFile) => {
  if (!file.uploaded_timestamp) return '-'
  return formatDurationBetween(file.created_timestamp, file.uploaded_timestamp)
}

const copyCommand = async (command: string) => {
  try {
    await navigator.clipboard.writeText(command)
    notificationStore.showSuccess('Command copied to clipboard!')
  } catch {
    notificationStore.showWarning(
      'Unable to copy command to clipboard 😞. Please copy it manually.',
    )
  }
}

const copyOutput = async (log: string, name: string = 'stdout') => {
  try {
    await navigator.clipboard.writeText('```\n' + log + '\n```\n')
    notificationStore.showSuccess(`${name} copied to Clipboard!`)
  } catch {
    notificationStore.showError(`Unable to copy ${name} to clipboard 😞. Please copy it manually.`)
  }
}

const cancel = async () => {
  const success = await tasksStore.cancelTask(task.value?.id || '')
  if (success) {
    task.value = null
    await refreshData()
  }
}

const scrollLogsToBottom = () => {
  const logElements = document.querySelectorAll('.stdout, .stderr')
  logElements.forEach((element) => {
    element.scrollTop = element.scrollHeight
  })
}

const refreshData = async () => {
  loadingStore.startLoading('Fetching task...')
  const response = await tasksStore.fetchTask(props.id, !canViewTaskSecrets.value)
  if (response) {
    task.value = response
    // Use nextTick to ensure the DOM has updated before scrolling
    nextTick(() => {
      scrollLogsToBottom()
    })
  } else {
    error.value = 'Failed to fetch task'
    for (const error of tasksStore.errors) {
      notificationStore.showError(error)
    }
  }
  loadingStore.stopLoading()
}

// Lifecycle
onMounted(async () => {
  refreshData()
  if (task.value) {
    const offlinerDefinition = await offlinerStore.fetchOfflinerDefinitionByVersion(
      task.value.offliner,
      task.value.version,
    )
    if (offlinerDefinition) {
      flagsDefinition.value = offlinerDefinition.flags
    }
  }
})

// Watchers
watch(
  () => props.selectedTab,
  (newTab) => {
    currentTab.value = newTab
    refreshData()
  },
)
</script>

<style scoped>
.stdout,
.stderr {
  max-height: 9rem;
  overflow: scroll;
  background-color: rgb(var(--v-theme-surface));
  padding: 1rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.875rem;
}

pre {
  white-space: pre-wrap;
  word-break: break-all;
  margin: 0;
}

.command {
  font-family: monospace;
  background-color: rgb(var(--v-theme-surface));
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.align-top {
  vertical-align: top;
}

.events-table tbody tr:nth-of-type(odd) {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>
