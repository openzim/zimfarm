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
          <v-card flat>
            <v-card-text class="pa-0">
              <div>
                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">ID</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <code>{{ id }}</code
                    >,
                    <a target="_blank" :href="webApiUrl + '/tasks/' + id">
                      document <v-icon size="small">mdi-open-in-new</v-icon>
                    </a>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Recipe</div>
                  </v-col>
                  <v-col cols="12" md="9">
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
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Status</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <code class="text-pink-accent-2">{{ task.status }}</code>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Worker</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <router-link
                      :to="{ name: 'worker-detail', params: { workerName: task.worker_name } }"
                      class="text-decoration-none"
                    >
                      {{ task.worker_name }}
                    </router-link>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Started On</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    {{ formatDt(startedOn) }}, after
                    <strong>{{ pipeDuration }} in pipe</strong>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Duration</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    {{ taskDuration }}<span v-if="isRunning"> (<strong>Ongoing</strong>)</span>
                  </v-col>
                </v-row>
                <v-divider class="my-2"></v-divider>

                <v-row no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Events</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <v-data-table
                      :headers="eventsHeaders"
                      :items="task.events"
                      :mobile="smAndDown"
                      :density="smAndDown ? 'compact' : 'comfortable'"
                      item-key="code"
                      hide-default-footer
                      disable-sort
                      class="events-table"
                    >
                      <template #[`item.code`]="{ item }">
                        <code class="text-pink-accent-2">{{ item.code }}</code>
                      </template>

                      <template #[`item.timestamp`]="{ item }">
                        {{ formatDt(item.timestamp) }}
                      </template>

                      <template #[`item.user`]="{ item }">
                        <span v-if="item.code === 'requested'">
                          {{ task.requested_by }}
                        </span>
                        <span
                          v-else-if="
                            item.code === 'cancel_requested' && task.status === 'cancel_requested'
                          "
                        >
                          {{ task.canceled_by }}
                        </span>
                        <span v-else-if="item.code === 'canceled'">
                          {{ task.canceled_by }}
                        </span>
                        <span v-else>-</span>
                      </template>
                    </v-data-table>
                  </v-col>
                </v-row>
                <v-divider v-if="task.files" class="my-2"></v-divider>

                <v-row v-if="task.files" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Files</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <v-data-table
                      :headers="filesHeaders"
                      :items="sortedFiles"
                      :mobile="smAndDown"
                      :density="smAndDown ? 'compact' : 'comfortable'"
                      item-key="name"
                      hide-default-footer
                      disable-sort
                      :class="smAndDown ? '' : 'files-table'"
                    >
                      <template #[`item.name`]="{ item }">
                        <a
                          target="_blank"
                          :href="kiwixDownloadUrl + task.config.warehouse_path + '/' + item.name"
                        >
                          {{ item.name }}
                        </a>
                      </template>

                      <template #[`item.size`]="{ item }">
                        {{ formattedBytesSize(item.size) }}
                      </template>

                      <template #[`item.created_after`]="{ item }">
                        <v-tooltip :text="formatDt(item.created_timestamp)">
                          <template #activator="{ props }">
                            <span v-bind="props">{{ createdAfter(item, task) }}</span>
                          </template>
                        </v-tooltip>
                      </template>

                      <template #[`item.upload_duration`]="{ item }">
                        <v-tooltip
                          v-if="item.uploaded_timestamp"
                          :text="formatDt(item.uploaded_timestamp)"
                        >
                          <template #activator="{ props }">
                            <span v-bind="props">{{ uploadDuration(item) }}</span>
                          </template>
                        </v-tooltip>
                        <span v-else>-</span>
                      </template>

                      <template #[`item.quality`]="{ item }">
                        <div
                          v-if="item.check_result !== undefined"
                          :class="['d-flex', 'align-center', { 'justify-end': smAndDown }]"
                        >
                          <v-tooltip :text="`Return code: ${item.check_result}`">
                            <template #activator="{ props }">
                              <v-icon
                                v-bind="props"
                                :color="item.check_result === 0 ? 'success' : 'error'"
                                size="small"
                              >
                                {{
                                  item.check_result === 0 ? 'mdi-check-circle' : 'mdi-close-circle'
                                }}
                              </v-icon>
                            </template>
                          </v-tooltip>
                          <v-btn
                            v-if="item.check_filename"
                            variant="text"
                            size="small"
                            class="ml-2"
                            :href="zimfarmChecksUrl(item.check_filename)"
                            target="_blank"
                            rel="noopener noreferrer"
                          >
                            <v-icon>mdi-download</v-icon>
                          </v-btn>
                        </div>
                        <span v-else>-</span>
                      </template>

                      <template #[`item.info`]="{ item }">
                        <div :class="['d-flex', { 'justify-end': smAndDown }]">
                          <v-menu v-if="item.info" location="left" :close-on-content-click="false">
                            <template #activator="{ props }">
                              <v-btn v-bind="props" variant="text" size="small">
                                <v-icon>mdi-information</v-icon>
                              </v-btn>
                            </template>
                            <FileInfoTable :file-info="item.info" />
                          </v-menu>
                          <span v-else>-</span>
                        </div>
                      </template>
                    </v-data-table>
                  </v-col>
                </v-row>
              </div>
            </v-card-text>
          </v-card>
        </v-window-item>

        <!-- Debug Tab -->
        <v-window-item value="debug">
          <v-card flat>
            <v-card-text class="pa-0">
              <div>
                <v-row v-if="task.config" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Offliner</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <a target="_blank" :href="imageUrl">
                      <code>{{ imageHuman }}</code>
                    </a>
                    (<code>{{ task.config.offliner.offliner_id }}</code
                    >)
                  </v-col>
                </v-row>
                <v-divider v-if="task.config" class="my-2"></v-divider>

                <v-row v-if="task.config" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Offliner Definition</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <code>{{ task.version }}</code>
                  </v-col>
                </v-row>
                <v-divider v-if="task.config" class="my-2"></v-divider>

                <v-row v-if="task.config" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Resources</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <div class="d-flex flex-row flex-wrap ga-1">
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
                    </div>
                  </v-col>
                </v-row>
                <v-divider v-if="task.config" class="my-2"></v-divider>

                <v-row v-if="task.config" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Platform</div>
                  </v-col>
                  <v-col cols="12" md="9">{{ task.config.platform || '-' }}</v-col>
                </v-row>
                <v-divider v-if="task.config" class="my-2"></v-divider>

                <v-row v-if="task.config" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Config</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <FlagsList
                      :offliner="task.config.offliner"
                      :flags-definition="flagsDefinition"
                      :shrink="false"
                    />
                  </v-col>
                </v-row>
                <v-divider v-if="task.config" class="my-2"></v-divider>

                <v-row v-if="taskContainer?.command" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">
                      Command
                      <v-btn
                        size="small"
                        variant="outlined"
                        class="ml-2"
                        @click="copyCommand(command)"
                      >
                        <v-icon size="small" class="mr-1">mdi-content-copy</v-icon>
                        Copy
                      </v-btn>
                    </div>
                  </v-col>
                  <v-col cols="12" md="9" class="text-break">
                    <code class="text-pink-accent-2">{{ command }}</code>
                  </v-col>
                </v-row>
                <v-divider v-if="taskContainer?.command" class="my-2"></v-divider>

                <v-row v-if="taskContainer?.exit_code != null" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Exit-code</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <code class="text-pink-accent-2">{{ taskContainer.exit_code }}</code>
                  </v-col>
                </v-row>
                <v-divider v-if="taskContainer?.exit_code != null" class="my-2"></v-divider>

                <v-row v-if="hasStats" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Stats</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <div class="d-flex flex-wrap ga-2">
                      <v-tooltip v-if="maxMemory" text="Maximum memory used during task execution">
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
                  </v-col>
                </v-row>
                <v-divider v-if="hasStats" class="my-2"></v-divider>

                <v-row v-if="taskProgress" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Scraper progress</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    {{ taskProgress.overall }}% ({{ taskProgress.done }} / {{ taskProgress.total }})
                  </v-col>
                </v-row>
                <v-divider v-if="taskProgress" class="my-2"></v-divider>

                <v-row
                  v-if="taskContainer?.stdout || taskContainer?.stderr || taskContainer?.log"
                  no-gutters
                  class="py-2"
                >
                  <v-col cols="12">
                    <small>Logs uses UTC Timezone. {{ offsetString }}</small>
                  </v-col>
                </v-row>

                <v-row v-if="taskContainer?.stdout" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">
                      Scraper stdout
                      <v-progress-circular
                        v-if="debugRefreshInProgress"
                        indeterminate
                        size="small"
                        class="ml-1"
                      />
                      <v-btn
                        size="small"
                        variant="outlined"
                        class="ml-2"
                        @click="copyOutput(taskContainer.stdout, 'stdout')"
                      >
                        <v-icon size="small" class="mr-1">mdi-content-copy</v-icon>
                        Copy
                      </v-btn>
                    </div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <pre class="stdout">{{ taskContainer.stdout }}</pre>
                  </v-col>
                </v-row>
                <v-divider v-if="taskContainer?.stdout" class="my-2"></v-divider>

                <v-row v-if="taskContainer?.stderr" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">
                      Scraper stderr
                      <v-btn
                        size="small"
                        variant="outlined"
                        class="ml-2"
                        @click="copyOutput(taskContainer.stderr, 'stderr')"
                      >
                        <v-icon size="small" class="mr-1">mdi-content-copy</v-icon>
                        Copy
                      </v-btn>
                    </div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <pre class="stderr">{{ taskContainer.stderr }}</pre>
                  </v-col>
                </v-row>
                <v-divider v-if="taskContainer?.stderr" class="my-2"></v-divider>

                <v-row v-if="taskContainer?.log" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Scraper Log</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <v-btn variant="outlined" size="small" target="_blank" :href="zimfarmLogsUrl">
                      Download log
                    </v-btn>
                  </v-col>
                </v-row>
                <v-divider v-if="taskContainer?.log" class="my-2"></v-divider>

                <v-row v-if="taskContainer?.artifacts" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Scraper Artifacts</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <v-btn
                      variant="outlined"
                      size="small"
                      target="_blank"
                      :href="zimfarmArtifactsUrl"
                    >
                      Download artifacts
                    </v-btn>
                  </v-col>
                </v-row>
                <v-divider v-if="taskContainer?.artifacts" class="my-2"></v-divider>

                <v-row v-if="taskDebug.exception" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Exception</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <pre>{{ taskDebug.exception }}</pre>
                  </v-col>
                </v-row>
                <v-divider v-if="taskDebug.exception" class="my-2"></v-divider>

                <v-row v-if="taskDebug.traceback" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Traceback</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <pre>{{ taskDebug.traceback }}</pre>
                  </v-col>
                </v-row>
                <v-divider v-if="taskDebug.traceback" class="my-2"></v-divider>

                <v-row v-if="taskDebug.log" no-gutters class="py-2">
                  <v-col cols="12" md="3">
                    <div class="text-subtitle-2">Task-worker Log</div>
                  </v-col>
                  <v-col cols="12" md="9">
                    <pre>{{ taskDebug.log }}</pre>
                  </v-col>
                </v-row>
              </div>
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
  imageHuman as imageHumanFn,
  imageUrl as imageUrlFn,
  logsUrl,
} from '@/utils/offliner'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { computed, inject, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useDisplay } from 'vuetify'

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

const { smAndDown } = useDisplay()

// Reactive data
const task = ref<Task | null>(null)
const error = ref<string | null>(null)
const currentTab = ref(props.selectedTab)
const flagsDefinition = ref<OfflinerDefinition[]>([])
const debugRefreshInProgress = ref(false)
const debugRefreshIntervalId = ref<ReturnType<typeof setInterval> | null>(null)

const eventsHeaders = [
  { title: 'Event', value: 'code' },
  { title: 'Timestamp', value: 'timestamp' },
  { title: 'User', value: 'user' },
]

const filesHeaders = [
  { title: 'Filename', value: 'name', width: '30%' },
  { title: 'Size', value: 'size' },
  { title: 'Created After', value: 'created_after' },
  { title: 'Upload Duration', value: 'upload_duration' },
  { title: 'Quality', value: 'quality' },
  { title: 'Info', value: 'info' },
]

// Computed properties
const offsetString = computed(() => {
  const tzDetails = getTimezoneDetails()
  return `You are ${tzDetails.tz} (${tzDetails.offsetstr}).`
})

const shortId = computed(() => {
  return props.id.substring(0, 5)
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
  return `${config.MONITORING_URL}/host/${scheduleName.value}_${shortId.value}.${
    task.value?.worker_name
  }#after=${new Date(
    getTimestampStringForStatus(task.value?.timestamp, 'scraper_started', '') || 0,
  ).getTime()};before=${new Date(
    getTimestampStringForStatus(task.value?.timestamp, 'scraper_completed', '') ||
      task.value?.updated_at ||
      0,
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

const refreshData = async (options?: { hideLoading?: boolean }) => {
  if (!options?.hideLoading) {
    loadingStore.startLoading('Fetching task...')
  }
  const response = await tasksStore.fetchTask(props.id, !canViewTaskSecrets.value)
  if (response) {
    task.value = response
    // Use nextTick to ensure the DOM has updated before scrolling
    nextTick(() => {
      scrollLogsToBottom()
    })
  } else {
    if (!options?.hideLoading) {
      error.value = 'Failed to fetch task'
      for (const error of tasksStore.errors) {
        notificationStore.showError(error)
      }
    }
  }
  if (!options?.hideLoading) {
    loadingStore.stopLoading()
  }
}

const refreshDebugOnly = async () => {
  if (debugRefreshInProgress.value) return
  debugRefreshInProgress.value = true
  try {
    await refreshData({ hideLoading: true })
  } finally {
    debugRefreshInProgress.value = false
  }
}

// Lifecycle
onMounted(async () => {
  await refreshData()
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

watch(
  () => [currentTab.value, task.value, isRunning.value] as const,
  ([tab, t, running]) => {
    if (debugRefreshIntervalId.value) {
      clearInterval(debugRefreshIntervalId.value)
      debugRefreshIntervalId.value = null
    }
    if (tab === 'debug' && t && running) {
      debugRefreshIntervalId.value = window.setInterval(refreshDebugOnly, 60000)
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (debugRefreshIntervalId.value) {
    clearInterval(debugRefreshIntervalId.value)
    debugRefreshIntervalId.value = null
  }
})
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

.events-table :deep(tbody tr:nth-of-type(odd)) {
  background-color: rgba(0, 0, 0, 0.05);
}

.files-table :deep(.v-data-table__td:first-child),
.files-table :deep(.v-data-table__th:first-child) {
  max-width: 30%;
  word-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  overflow-wrap: break-word;
}

/* Additional word-wrap styles for mobile table cells in this view */
:deep(.v-data-table__tr--mobile .v-data-table__td) {
  word-wrap: break-word;
  word-break: break-word;
  white-space: normal;
  overflow-wrap: break-word;
}
</style>
