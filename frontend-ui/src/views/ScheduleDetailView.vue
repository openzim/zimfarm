<!-- Schedule detail view
  - listing all info
  - fire schedule button -->

<template>
  <v-container>
    <!-- Action Button Row -->
    <v-row v-if="schedule && schedule.enabled && !schedule.archived">
      <v-col>
        <ScheduleActionButton
          :name="scheduleName"
          :ready="ready"
          :task="task"
          :requested-task="requestedTask"
          :workers="workers"
          :working-text="workingText"
          @request-task="requestTask"
          @fire-existing-task="fireExistingTask"
          @cancel-task="cancelTask"
          @unrequest-task="unrequestTask"
        />
      </v-col>
    </v-row>

    <!-- Title Row -->
    <v-row>
      <v-col>
        <h2 class="text-h4">
          <code>{{ scheduleName }}</code>
        </h2>
      </v-col>
    </v-row>

    <!-- Loading State -->
    <div v-if="!ready && !error" class="text-center pa-8">
      <v-progress-circular indeterminate size="64" color="primary" />
      <div class="mt-4 text-body-1">Loading schedule data...</div>
    </div>

    <!-- Content -->
    <div v-if="ready && schedule">
      <!-- Tabs -->
      <v-tabs v-model="currentTab" class="mb-4" color="primary" slider-color="primary">
        <v-tab
          base-color="primary"
          value="details"
          :to="{
            name: 'schedule-detail',
            params: { scheduleName: scheduleName },
          }"
        >
          <v-icon class="mr-2">mdi-information</v-icon>
          Info
        </v-tab>
        <v-tab
          base-color="primary"
          value="config"
          :to="{
            name: 'schedule-detail-tab',
            params: { scheduleName: scheduleName, selectedTab: 'config' },
          }"
        >
          <v-icon class="mr-2">mdi-cog</v-icon>
          Config
        </v-tab>
        <v-tab
          base-color="primary"
          v-if="canUpdateSchedules"
          value="history"
          :to="{
            name: 'schedule-detail-tab',
            params: { scheduleName: scheduleName, selectedTab: 'history' },
          }"
        >
          <v-icon class="mr-2">mdi-history</v-icon>
          History
        </v-tab>
        <v-tab
          base-color="primary"
          v-if="canUpdateSchedules && !schedule?.archived"
          value="edit"
          :to="{
            name: 'schedule-detail-tab',
            params: { scheduleName: scheduleName, selectedTab: 'edit' },
          }"
        >
          <v-icon class="mr-2">mdi-pencil</v-icon>
          Edit
        </v-tab>
        <v-tab
          base-color="primary"
          v-if="canCreateSchedules && !schedule?.archived"
          value="clone"
          :to="{
            name: 'schedule-detail-tab',
            params: { scheduleName: scheduleName, selectedTab: 'clone' },
          }"
        >
          <v-icon class="mr-2">mdi-content-copy</v-icon>
          Clone
        </v-tab>
        <v-tab
          base-color="primary"
          v-if="canDeleteSchedules"
          value="archive"
          :to="{
            name: 'schedule-detail-tab',
            params: { scheduleName: scheduleName, selectedTab: 'archive' },
          }"
        >
          <v-icon class="mr-2">{{
            schedule?.archived ? 'mdi-archive-arrow-up' : 'mdi-archive'
          }}</v-icon>
          {{ schedule?.archived ? 'Restore' : 'Archive' }}
        </v-tab>

        <v-tab
          base-color="error"
          v-if="canDeleteSchedules && schedule?.archived"
          value="delete"
          :to="{
            name: 'schedule-detail-tab',
            params: { scheduleName: scheduleName, selectedTab: 'delete' },
          }"
        >
          <v-icon class="mr-2">mdi-delete</v-icon>
          Delete
        </v-tab>
      </v-tabs>

      <!-- Tab Content -->
      <v-window v-model="currentTab">
        <!-- Details Tab -->
        <v-window-item value="details">
          <v-card flat>
            <v-card-text>
              <v-table>
                <tbody>
                  <tr>
                    <th class="text-left" style="width: 200px">API</th>
                    <td>
                      <a
                        target="_blank"
                        :href="webApiUrl + '/schedules/' + scheduleName"
                        class="text-decoration-none"
                      >
                        document
                        <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Category</th>
                    <td>{{ schedule.category }}</td>
                  </tr>
                  <tr>
                    <th class="text-left">Language</th>
                    <td>
                      {{ schedule.language.name }} (<code>{{ schedule.language.code }}</code
                      >)
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Enabled</th>
                    <td>
                      <v-chip
                        :color="schedule?.enabled ? 'success' : 'error'"
                        size="small"
                        variant="tonal"
                      >
                        {{ schedule?.enabled }}
                      </v-chip>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Archived</th>
                    <td>
                      {{ schedule?.archived ? 'Yes' : 'No' }}
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Periodicity</th>
                    <td>
                      <code>{{ schedule?.periodicity }}</code>
                    </td>
                  </tr>
                  <tr v-if="schedule?.tags?.length">
                    <th class="text-left">Tags</th>
                    <td>
                      <v-chip
                        v-for="tag in schedule?.tags || []"
                        :key="tag"
                        size="small"
                        color="primary"
                        variant="outlined"
                        density="comfortable"
                        class="mr-2 mb-1 text-caption text-uppercase"
                      >
                        {{ tag }}
                      </v-chip>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Context</th>
                    <td>
                      <v-chip
                        v-if="schedule.context"
                        size="small"
                        variant="outlined"
                        density="comfortable"
                        color="primary"
                        class="mr-2 mb-1 text-caption text-uppercase"
                      >
                        {{ schedule.context }}
                      </v-chip>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Last run</th>
                    <td v-if="lastRun">
                      <v-chip
                        :color="getStatusColor(lastRun.status)"
                        size="small"
                        variant="tonal"
                        class="mr-2"
                      >
                        {{ lastRun.status }}
                      </v-chip>
                      <TaskLink
                        :id="lastRun.id"
                        :updatedAt="lastRun.updated_at"
                        :status="lastRun.status"
                        :timestamp="lastRun.timestamp"
                      />
                    </td>
                    <td v-else>
                      <v-chip size="small" variant="outlined" color="grey"> None 🙁 </v-chip>
                    </td>
                  </tr>
                  <tr v-if="scheduleDurationDict">
                    <th class="text-left">Scraper Duration</th>
                    <td>
                      <span v-if="scheduleDurationDict.single">
                        {{ scheduleDurationDict.formattedDuration }}
                        (<router-link
                          :to="{
                            name: 'worker-detail',
                            params: { workerName: scheduleDurationDict.worker },
                          }"
                        >
                          {{ scheduleDurationDict.worker }}
                        </router-link>
                        on
                        {{ formatDt(scheduleDurationDict.on) }})
                      </span>
                      <span v-else>
                        between
                        {{ scheduleDurationDict.formattedMinDuration }} (<template
                          v-for="(worker, index) in scheduleDurationDict.minWorkers || []"
                          :key="worker.worker_name"
                        >
                          <router-link
                            :to="{
                              name: 'worker-detail',
                              params: { workerName: worker.worker_name },
                            }"
                          >
                            {{ worker.worker_name }} </router-link
                          ><span v-if="index < (scheduleDurationDict.minWorkers?.length || 0) - 1"
                            >,
                          </span> </template
                        >) and {{ scheduleDurationDict.formattedMaxDuration }} (<template
                          v-for="(worker, index) in scheduleDurationDict.maxWorkers || []"
                          :key="worker.worker_name"
                        >
                          <router-link
                            :to="{
                              name: 'worker-detail',
                              params: { workerName: worker.worker_name },
                            }"
                          >
                            {{ worker.worker_name }} </router-link
                          ><span v-if="index < (scheduleDurationDict.maxWorkers?.length || 0) - 1"
                            >,
                          </span> </template
                        >)
                      </span>
                    </td>
                  </tr>
                  <tr v-if="totalDurationDict">
                    <th class="text-left">Total Duration</th>
                    <td>
                      <span v-if="totalDurationDict.single">
                        {{ totalDurationDict.formattedDuration }}
                        (<router-link
                          :to="{
                            name: 'worker-detail',
                            params: { workerName: totalDurationDict.worker },
                          }"
                        >
                          {{ totalDurationDict.worker }}
                        </router-link>
                        on
                        {{ formatDt(totalDurationDict.on) }})
                      </span>
                      <span v-else>
                        between
                        {{ totalDurationDict.formattedMinDuration }} (<template
                          v-for="(worker, index) in totalDurationDict.minWorkers || []"
                          :key="worker.worker_name"
                        >
                          <router-link
                            :to="{
                              name: 'worker-detail',
                              params: { workerName: worker.worker_name },
                            }"
                          >
                            {{ worker.worker_name }} </router-link
                          ><span v-if="index < (totalDurationDict.minWorkers?.length || 0) - 1"
                            >,
                          </span> </template
                        >) and {{ totalDurationDict.formattedMaxDuration }} (<template
                          v-for="(worker, index) in totalDurationDict.maxWorkers || []"
                          :key="worker.worker_name"
                        >
                          <router-link
                            :to="{
                              name: 'worker-detail',
                              params: { workerName: worker.worker_name },
                            }"
                          >
                            {{ worker.worker_name }} </router-link
                          ><span v-if="index < (totalDurationDict.maxWorkers?.length || 0) - 1"
                            >,
                          </span> </template
                        >)
                      </span>
                    </td>
                  </tr>
                  <tr v-if="!canRequestTasks">
                    <th class="text-left">Requested</th>
                    <td v-if="requestedTask === null">
                      <v-progress-circular indeterminate size="16" />
                    </td>
                    <td v-else-if="requestedTask">
                      <code>{{ shortId(requestedTask.id) }}</code
                      >,
                      {{
                        fromNow(getTimestampStringForStatus(requestedTask.timestamp, 'requested'))
                      }}
                      <v-chip
                        v-if="requestedTask.priority"
                        size="small"
                        color="warning"
                        variant="tonal"
                        class="ml-2"
                      >
                        <v-icon size="small" class="mr-1">mdi-fire</v-icon>
                        {{ requestedTask.priority }}
                      </v-chip>
                    </td>
                    <td v-else>
                      <v-chip size="small" variant="outlined" color="grey"> No </v-chip>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left align-top pa-4">History</th>
                    <td v-if="historyRuns.length">
                      <v-table density="compact">
                        <thead>
                          <tr>
                            <th class="text-left">Worker</th>
                            <th class="text-left">Status</th>
                            <th class="text-left">Task</th>
                            <th class="text-left">Total Duration</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="run in historyRuns" :key="run.id">
                            <td>
                              <router-link
                                :to="{
                                  name: 'worker-detail',
                                  params: { workerName: run.worker_name },
                                }"
                                class="text-decoration-none"
                              >
                                {{ run.worker_name }}
                              </router-link>
                            </td>
                            <td>
                              <v-chip
                                :color="getStatusColor(run.status)"
                                size="small"
                                variant="tonal"
                              >
                                {{ run.status }}
                              </v-chip>
                            </td>
                            <td>
                              <span class="text-no-wrap">
                                <TaskLink
                                  :id="run.id"
                                  :updatedAt="run.updated_at"
                                  :status="run.status"
                                  :timestamp="run.timestamp"
                                />
                              </span>
                            </td>
                            <td>
                              <span>{{ calculateTaskDuration(run) }}</span>
                            </td>
                          </tr>
                        </tbody>
                      </v-table>
                    </td>
                    <td v-else>
                      <v-chip size="small" variant="outlined" color="grey"> None 🙁 </v-chip>
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </v-card-text>
          </v-card>
        </v-window-item>

        <!-- History Tab -->
        <v-window-item value="history">
          <div v-if="canUpdateSchedules" class="pa-4">
            <ScheduleHistory
              :history="scheduleHistoryStore.history"
              :has-more="canLoadMoreHistory"
              :loading="loadingHistory"
              :paginator="scheduleHistoryStore.paginator"
              :schedule-name="scheduleName"
              @load="loadHistory"
            />
          </div>
        </v-window-item>

        <!-- Config Tab -->
        <v-window-item value="config">
          <v-card flat>
            <v-card-text>
              <v-table>
                <tbody>
                  <tr>
                    <th class="text-left" style="width: 200px">Offliner</th>
                    <td>
                      <code>{{ offliner }}</code>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Offliner Definition</th>
                    <td>
                      <code>{{ schedule.version }}</code>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Platform</th>
                    <td>
                      <code>{{ platform || '-' }}</code>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Warehouse Path</th>
                    <td>
                      <code>{{ warehousePath }}</code>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Image</th>
                    <td>
                      <a target="_blank" :href="imageUrl" class="text-decoration-none">
                        <code>{{ imageHuman }}</code>
                      </a>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left">Resources</th>
                    <td>
                      <ResourceBadge kind="cpu" :value="config.resources.cpu" />
                      <ResourceBadge kind="memory" :value="config.resources.memory" />
                      <ResourceBadge kind="disk" :value="config.resources.disk" />
                      <ResourceBadge
                        kind="shm"
                        :value="config.resources.shm"
                        v-if="config.resources.shm"
                      />
                      <v-chip
                        v-if="config.monitor || false"
                        size="small"
                        color="warning"
                        variant="tonal"
                        class="ml-2"
                      >
                        <v-icon size="small" class="mr-1">mdi-bug</v-icon>
                        monitored
                      </v-chip>
                    </td>
                  </tr>
                  <tr v-if="schedule?.config?.artifacts_globs">
                    <th class="text-left">Artifacts</th>
                    <td>
                      <code class="text-pink-accent-2">{{
                        schedule?.config?.artifacts_globs
                      }}</code>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left pa-4 align-top">Config</th>
                    <td>
                      <FlagsList :offliner="config.offliner" :secret-fields="secretFields" />
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left pa-4 align-top">
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
                    </th>
                    <td class="py-2">
                      <code class="text-pink-accent-2">{{ command }}</code>
                    </td>
                  </tr>
                  <tr>
                    <th class="text-left pa-4 align-top">
                      Offliner Command
                      <v-btn
                        size="small"
                        variant="outlined"
                        class="ml-2"
                        @click="copyCommand(offlinerCommand)"
                      >
                        <v-icon size="small" class="mr-1">mdi-content-copy</v-icon>
                        Copy
                      </v-btn>
                    </th>
                    <td class="py-2">
                      <code class="text-pink-accent-2">{{ offlinerCommand }}</code>
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </v-card-text>
          </v-card>
        </v-window-item>

        <!-- Edit Tab -->
        <v-window-item value="edit">
          <div v-if="canUpdateSchedules" class="pa-4">
            <!-- Validation Status -->
            <v-alert
              v-if="schedule"
              :type="schedule.is_valid ? 'success' : 'error'"
              variant="tonal"
              class="mb-4"
              closable
            >
              <template #prepend>
                <v-icon :icon="schedule.is_valid ? 'mdi-check-circle' : 'mdi-alert-circle'" />
              </template>
              <strong>{{
                schedule.is_valid ? 'Recipe is valid' : 'Recipe has validation errors'
              }}</strong>
              <div v-if="!schedule.is_valid" class="mt-2">
                Please fix the configuration issues below.
              </div>
            </v-alert>

            <ScheduleEditor
              :schedule="schedule"
              :offliners="offliners"
              :platforms="platforms"
              :languages="languages"
              :tags="tags"
              :contexts="contexts"
              :flags-definition="flagsDefinition"
              :help-url="helpUrl"
              :offliner-versions="offlinerVersions"
              :image-tags="imageTags"
              @submit="updateSchedule"
              @image-name-change="fetchScheduleImageTags"
              @offliner-change="handleOfflinerChange"
              @offliner-version-change="handleOfflinerVersionChange"
            />
          </div>
        </v-window-item>

        <!-- Clone Tab -->
        <v-window-item value="clone">
          <div v-if="canCreateSchedules" class="pa-4">
            <CloneSchedule :from="scheduleName" @clone="cloneSchedule" />
          </div>
        </v-window-item>

        <!-- Archive Tab -->
        <v-window-item value="archive">
          <div v-if="canDeleteSchedules" class="pa-4">
            <ArchiveItem
              :name="scheduleName"
              :is-archived="schedule?.archived || false"
              @archive-item="archiveSchedule"
              @restore-item="restoreSchedule"
            />
          </div>
        </v-window-item>

        <!-- Delete Tab -->
        <v-window-item value="delete">
          <div v-if="canDeleteSchedules" class="pa-4">
            <DeleteItem
              :name="scheduleName"
              description="recipe"
              property="name"
              @delete-item="deleteSchedule"
            />
          </div>
        </v-window-item>
      </v-window>
    </div>

    <ErrorMessage v-if="error" :message="error" />
  </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

import ArchiveItem from '@/components/ArchiveItem.vue'
import CloneSchedule from '@/components/CloneSchedule.vue'
import DeleteItem from '@/components/DeleteItem.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import FlagsList from '@/components/FlagsList.vue'
import ResourceBadge from '@/components/ResourceBadge.vue'
import ScheduleActionButton from '@/components/ScheduleActionButton.vue'
import ScheduleEditor from '@/components/ScheduleEditor.vue'
import ScheduleHistory from '@/components/ScheduleHistory.vue'
import TaskLink from '@/components/TaskLink.vue'
import type { Config } from '@/config'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useContextStore } from '@/stores/context'
import { useLanguageStore } from '@/stores/language'
import { useNotificationStore } from '@/stores/notification'
import { useOfflinerStore } from '@/stores/offliner'
import { usePlatformStore } from '@/stores/platform'
import { useRequestedTasksStore } from '@/stores/requestedTasks'
import { useScheduleStore } from '@/stores/schedule'
import { useScheduleHistoryStore } from '@/stores/scheduleHistory'
import { useTagStore } from '@/stores/tag'
import { useTasksStore } from '@/stores/tasks'
import { useWorkersStore } from '@/stores/workers'
import type { Language } from '@/types/language'
import type { OfflinerDefinition } from '@/types/offliner'
import type { RequestedTaskLight } from '@/types/requestedTasks'
import type { ExpandedScheduleConfig, Schedule, ScheduleUpdateSchema } from '@/types/schedule'
import type { TaskLight } from '@/types/tasks'
import type { Worker } from '@/types/workers'
import { formatDt, formatDurationBetween, fromNow } from '@/utils/format'
import {
  buildCommandWithout,
  buildDockerCommand,
  buildScheduleDuration,
  buildTotalDurationDict,
  getSecretFields,
  imageHuman as imageHumanFn,
  imageUrl as imageUrlFn,
} from '@/utils/offliner'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { inject } from 'vue'

// Props
interface Props {
  scheduleName: string
  selectedTab?: string
}

const props = withDefaults(defineProps<Props>(), {
  selectedTab: 'details',
})

// Router and stores
const router = useRouter()

const authStore = useAuthStore()
const notificationStore = useNotificationStore()
const scheduleStore = useScheduleStore()
const scheduleHistoryStore = useScheduleHistoryStore()
const requestedTasksStore = useRequestedTasksStore()
const tasksStore = useTasksStore()
const workersStore = useWorkersStore()
const tagStore = useTagStore()
const contextStore = useContextStore()
const languageStore = useLanguageStore()
const offlinerStore = useOfflinerStore()
const platformStore = usePlatformStore()

// Config
const appConfig = inject<Config>(constants.config)
if (!appConfig) {
  throw new Error('Config is not defined')
}

// Reactive data

const error = ref<string | null>(null)
const workingText = ref<string | null>(null)
const imageTags = ref<string[]>([])
const tags = ref<string[]>([])
const contexts = ref<string[]>([])
const languages = ref<Language[]>([])
const offliners = ref<string[]>([])
const offlinerVersions = ref<string[]>([])
const platforms = ref<string[]>([])
const flagsDefinition = ref<OfflinerDefinition[]>([])
const helpUrl = ref<string>('')

const ready = ref<boolean>(false)
const schedule = ref<Schedule | null>(null)
const loadingHistory = ref<boolean>(false)
// existing requested task for this schedule
const requestedTask = ref<RequestedTaskLight | null>(null)
// existing running task for this schedule
const task = ref<TaskLight | null>(null)
// history of runs for this schedule
const historyRuns = ref<TaskLight[]>([])
// current tab
const currentTab = ref(props.selectedTab)
// active workers
const workers = ref<Worker[]>([])

// Computed properties
const webApiUrl = computed(() => appConfig.ZIMFARM_WEBAPI)
const lastRun = computed(() => schedule.value?.most_recent_task || null)
const config = computed(() => schedule.value?.config || ({} as ExpandedScheduleConfig))
const offliner = computed(() => config.value?.offliner?.offliner_id || '')
const platform = computed(() => config.value?.platform || '')
const warehousePath = computed(() => config.value?.warehouse_path || '')
const imageHuman = computed(() => imageHumanFn(config.value))
const imageUrl = computed(() => imageUrlFn(config.value))
const secretFields = computed(() => getSecretFields(flagsDefinition.value))
const command = computed(() => buildDockerCommand(schedule.value?.name || '', config.value))
const offlinerCommand = computed(() => buildCommandWithout(config.value))
const scheduleDurationDict = computed(() => {
  return buildScheduleDuration(schedule.value?.duration || null)
})
const totalDurationDict = computed(() => {
  return buildTotalDurationDict(historyRuns.value)
})

// Permission computed properties
const canRequestTasks = computed(() => authStore.hasPermission('tasks', 'request'))
const canUpdateSchedules = computed(() => authStore.hasPermission('schedules', 'update'))
const canCreateSchedules = computed(() => authStore.hasPermission('schedules', 'create'))
const canDeleteSchedules = computed(() => authStore.hasPermission('schedules', 'delete'))

// History-related computed properties
const canLoadMoreHistory = computed(() => {
  const { skip, limit, count } = scheduleHistoryStore.paginator
  return skip + limit < count
})

// Methods
const fetchWorkers = async () => {
  const response = await workersStore.fetchWorkers()
  if (response) {
    workers.value = response
  } else {
    for (const error of workersStore.errors) {
      notificationStore.showError(error)
    }
    workers.value = []
  }
}

const fetchScheduleTasks = async (onSuccess?: () => void) => {
  // Reset state
  requestedTask.value = null
  task.value = null

  // Fetch requested tasks
  const response = await requestedTasksStore.fetchRequestedTasks({
    scheduleName: [props.scheduleName],
  })
  if (response) {
    if (response.length > 0) {
      requestedTask.value = response[0]
    }
    // fetch history runs
    const historyRunsResponse = await tasksStore.fetchTasks({
      scheduleName: props.scheduleName,
    })
    if (historyRunsResponse) {
      historyRuns.value = historyRunsResponse
    } else {
      for (const error of tasksStore.errors) {
        notificationStore.showError(error)
      }
    }

    // fetch running tasks
    const tasksResponse = await tasksStore.fetchTasks({
      scheduleName: props.scheduleName,
      status: constants.CANCELABLE_STATUSES,
    })
    if (tasksResponse) {
      if (tasksResponse.length > 0) {
        task.value = tasksResponse[0]
      }
      // now that we have received all the data, we can call the onSuccess callback
      onSuccess?.()
    } else {
      if (tasksStore.errors.length > 0) {
        for (const error of tasksStore.errors) {
          notificationStore.showError(error)
        }
      }
    }
  } else {
    if (requestedTasksStore.errors.length > 0) {
      for (const error of requestedTasksStore.errors) {
        notificationStore.showError(error)
      }
    }
  }
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

const requestTask = async (workerName: string | null, priority?: boolean) => {
  workingText.value = 'Requesting task…'

  const body: {
    scheduleNames: string[]
    worker: string | null
    priority: number | null
  } = {
    scheduleNames: [props.scheduleName],
    worker: workerName,
    priority: priority ? constants.DEFAULT_FIRE_PRIORITY : null,
  }

  const response = await requestedTasksStore.requestTasks(body)
  if (response) {
    const msg = `Recipe <em>${props.scheduleName}</em> has been requested as <code>${shortId(
      response.requested[0],
    )}</code>.`
    notificationStore.showSuccess(msg)
    workingText.value = null
    // update the requested task
    if (requestedTask.value) {
      requestedTask.value.id = response.requested[0]
      requestedTask.value.priority = priority ? constants.DEFAULT_FIRE_PRIORITY : 0
    }
    await fetchScheduleTasks()
  } else {
    for (const error of requestedTasksStore.errors) {
      notificationStore.showError(error)
    }
  }
  workingText.value = null
}

const fireExistingTask = async () => {
  if (!requestedTask.value) return

  workingText.value = 'Firing it up…'

  const response = await requestedTasksStore.updateRequestedTask(requestedTask.value.id, {
    priority: constants.DEFAULT_FIRE_PRIORITY,
  })
  if (response) {
    const msg = `Added priority to request <code>${shortId(requestedTask.value.id)}</code>.`
    notificationStore.showSuccess(msg)
  } else {
    for (const error of requestedTasksStore.errors) {
      notificationStore.showError(error)
    }
  }
  workingText.value = null
}

const cancelTask = async () => {
  if (!task.value) return

  workingText.value = 'Canceling task…'

  const response = await tasksStore.cancelTask(task.value.id)
  if (response) {
    const msg = `Requested Task <code>${shortId(task.value.id)}</code> has been marked for cancellation.`
    notificationStore.showSuccess(msg)
    task.value = null
    await fetchScheduleTasks()
  } else {
    for (const error of tasksStore.errors) {
      notificationStore.showError(error)
    }
  }
  workingText.value = null
}

const unrequestTask = async () => {
  if (!requestedTask.value) return

  workingText.value = 'Un-requesting task…'

  const response = await requestedTasksStore.deleteRequestedTask(requestedTask.value.id)
  if (response) {
    const msg = `Requested Task <code>${shortId(requestedTask.value.id)}</code> has been deleted.`
    notificationStore.showSuccess(msg)
    requestedTask.value = null
    await fetchScheduleTasks()
  } else {
    for (const error of requestedTasksStore.errors) {
      notificationStore.showError(error)
    }
  }
  workingText.value = null
}

const cloneSchedule = async (newName: string) => {
  const response = await scheduleStore.cloneSchedule(props.scheduleName, newName)
  if (response) {
    notificationStore.showSuccess(
      `Recipe <code>${newName}</code> has been created off <code>${props.scheduleName}</code>.`,
    )
    router.push({ name: 'schedule-detail', params: { scheduleName: newName } })
  } else {
    for (const error of scheduleStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const fetchScheduleImageTags = async (imageName: string) => {
  const parts = imageName.split('/')
  if (parts.length < 2) {
    return // invalid image_name
  }
  const hubName = parts.splice(parts.length - 2, parts.length).join('/')

  const response = await scheduleStore.fetchScheduleImageTags(props.scheduleName, {
    hubName: hubName,
  })
  if (response) {
    imageTags.value = response
  } else {
    for (const error of scheduleStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const updateSchedule = async (update: ScheduleUpdateSchema) => {
  const response = await scheduleStore.updateSchedule(props.scheduleName, update)
  if (response) {
    notificationStore.showSuccess('Recipe updated successfully')
    // if name changed, redirect to the new schedule
    if (update.name) {
      router.push({
        name: 'schedule-detail-tab',
        params: { scheduleName: update.name, selectedTab: 'edit' },
      })
    }
    // update the schedule in the current view
    const updatedSchedule = await scheduleStore.fetchSchedule(
      update.name || props.scheduleName,
      true,
    )
    if (updatedSchedule) {
      schedule.value = updatedSchedule
    } else {
      for (const error of scheduleStore.errors) {
        notificationStore.showError(error)
      }
    }

    // if context was changed, fetch the new contexts
    if (update.context !== null || update.context !== undefined) {
      const newContexts = await contextStore.fetchContexts()
      if (newContexts) {
        contexts.value = newContexts
      } else {
        for (const error of contextStore.errors) {
          notificationStore.showError(error)
        }
      }
    }
  } else {
    for (const error of scheduleStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const validateSchedule = async () => {
  await scheduleStore.validateSchedule(props.scheduleName)
  if (scheduleStore.errors.length > 0) {
    for (const error of scheduleStore.errors) {
      notificationStore.showError(error)
    }
  }
}

// History-related methods
const loadHistory = async ({ limit, skip }: { limit: number; skip: number }) => {
  if (skip > 0 && !canLoadMoreHistory.value) return

  loadingHistory.value = true
  try {
    await scheduleHistoryStore.fetchHistory(props.scheduleName, limit, skip)
  } catch (error) {
    console.error('Failed to load history items', error)
    notificationStore.showError(`Failed to ${skip > 0 ? 'load more' : 'load'} history items`)
  } finally {
    loadingHistory.value = false
  }
}

const deleteSchedule = async () => {
  const response = await scheduleStore.deleteSchedule(props.scheduleName)
  if (response) {
    notificationStore.showSuccess(`Recipe <code>${props.scheduleName}</code> has been deleted.`)
    router.push({ name: 'schedules-list' })
  } else {
    for (const error of scheduleStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const archiveSchedule = async (comment?: string) => {
  const response = await scheduleStore.archiveSchedule(props.scheduleName, comment)
  if (response) {
    notificationStore.showSuccess(`Recipe <code>${props.scheduleName}</code> has been archived.`)
    // Refresh the schedule data to update the archive status
    await refreshData(true)
    // Switch to info tab after archiving
    currentTab.value = 'details'
  } else {
    for (const error of scheduleStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const restoreSchedule = async (comment?: string) => {
  const response = await scheduleStore.restoreSchedule(props.scheduleName, comment)
  if (response) {
    notificationStore.showSuccess(`Recipe <code>${props.scheduleName}</code> has been restored.`)
    // Refresh the schedule data to update the archive status
    await refreshData(true)
    // Switch to info tab after restoring
    currentTab.value = 'details'
  } else {
    for (const error of scheduleStore.errors) {
      notificationStore.showError(error)
    }
  }
}

const refreshData = async (forceReload: boolean = false, fetchHistory: boolean = false) => {
  // Only set ready to false if we don't have any data yet
  if (!schedule.value) {
    ready.value = false
  }

  // Load schedule data (force reload on edit tab or explicitly requested)
  const response = await scheduleStore.fetchSchedule(
    props.scheduleName,
    currentTab.value === 'edit' || forceReload,
  )
  if (response) {
    schedule.value = response
  } else {
    error.value = 'Failed to load schedule data'
  }

  if (schedule.value) {
    if (schedule.value.enabled) {
      await fetchWorkers()
    }
    await fetchScheduleTasks()

    if (fetchHistory) {
      scheduleHistoryStore.clearHistory()
      await loadHistory({ limit: scheduleHistoryStore.paginator.limit, skip: 0 })
    }
    if (forceReload) {
      offlinerVersions.value =
        (await offlinerStore.fetchOfflinerVersions(schedule.value.offliner)) || []
    }
    ready.value = true
  }
}

const getStatusColor = (status: string): string => {
  switch (status) {
    case 'succeeded':
      return 'success'
    case 'failed':
      return 'error'
    case 'running':
      return 'info'
    case 'pending':
      return 'warning'
    default:
      return 'dark-grey'
  }
}

const shortId = (id: string | null): string => {
  return id ? id.substring(0, 8) : ''
}

const calculateTaskDuration = (task: TaskLight): string => {
  if (!task.timestamp) return ''
  const started = getTimestampStringForStatus(task.timestamp, 'started', '')
  if (!started) return 'Not actually started ⌛'

  const completed = getTimestampStringForStatus(
    task.timestamp,
    'succeeded',
    getTimestampStringForStatus(task.timestamp, 'failed', ''),
  )
  if (!completed) return 'Not actually completed ⌛'

  return formatDurationBetween(started, completed)
}

const handleOfflinerChange = async (offliner: string) => {
  // fetch all the offliner versions
  const response = (await offlinerStore.fetchOfflinerVersions(offliner)) || []
  if (response) {
    offlinerVersions.value = response
  } else {
    for (const error of offlinerStore.errors) {
      notificationStore.showError(error)
    }
  }
  // Child component will choose a default version (if needed) and emit
  // @offliner-version-change, which we handle via handleOfflinerVersionChange.
}

const handleOfflinerVersionChange = async (offliner: string, version: string) => {
  // fetch the offliner definition
  const response = await offlinerStore.fetchOfflinerDefinitionByVersion(offliner, version)
  if (response) {
    flagsDefinition.value = response.flags
    helpUrl.value = response.help
  } else {
    for (const error of offlinerStore.errors) {
      notificationStore.showError(error)
    }
  }
}

// Lifecycle
onMounted(async () => {
  // Redirect to details if trying to access restricted tabs without permission
  if (
    (props.selectedTab === 'edit' || props.selectedTab === 'history') &&
    !canUpdateSchedules.value
  ) {
    router.push({ name: 'schedule-detail', params: { scheduleName: props.scheduleName } })
  }

  // just in case the data is not loaded yet rather than using
  // .... computed(() => store.value. Given these stores cache values,
  // we can be sure that the data is already loaded on app mount.
  // Or we fetch again here (if for some reason, say network connection is slow)
  // and we couldn't fetch on app mount.
  tags.value = (await tagStore.fetchTags()) || []
  contexts.value = (await contextStore.fetchContexts()) || []
  languages.value = (await languageStore.fetchLanguages()) || []
  offliners.value = (await offlinerStore.fetchOffliners()) || []
  platforms.value = (await platformStore.fetchPlatforms()) || []
  // after fectching the all the data, we can fetch the offliner definition
  await refreshData(true, props.selectedTab === 'history')
  if (schedule.value) {
    const offlinerDefinition = await offlinerStore.fetchOfflinerDefinitionByVersion(
      schedule.value.offliner,
      schedule.value.version,
    )
    if (offlinerDefinition) {
      helpUrl.value = offlinerDefinition.help
      flagsDefinition.value = offlinerDefinition.flags
    }
    await fetchScheduleImageTags(schedule.value.config.image.name)
    // Get validation errors about the schedule on mount
    if (!schedule.value.is_valid) {
      await validateSchedule()
    }
  }
})

onUnmounted(() => {
  // Clear schedule history to prevent accumulation of history items
  scheduleHistoryStore.clearHistory()
})

// Watch for tab changes
watch(
  () => props.selectedTab,
  async (newTab) => {
    currentTab.value = newTab
    // Only refresh data if we don't have any data yet, or if not cloning or archiving
    if (!schedule.value || !['clone', 'archive', 'delete'].includes(newTab)) {
      await refreshData(newTab === 'edit', newTab === 'history')
    }
  },
)

// Watch for schedule name changes (when navigating to a different schedule)
watch(
  () => props.scheduleName,
  async () => {
    // Reset the current tab to details when switching schedules
    // Clear current data and reload the new schedule
    schedule.value = null
    currentTab.value = 'details'
  },
)
</script>

<style scoped>
.align-top {
  vertical-align: top;
}
</style>
