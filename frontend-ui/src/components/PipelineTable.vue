<template>
  <div>
    <v-card v-if="!errors.length" :class="{ loading: loading }" flat>
      <!-- Load All Last Runs button - only show in failed tab -->
      <div v-if="showLoadAllButton" class="d-flex justify-end">
        <v-btn
          :loading="loadingAllSchedules"
          :disabled="loadingAllSchedules || tasks.length === 0"
          color="primary"
          variant="tonal"
          prepend-icon="mdi-refresh"
          @click="handleLoadAllLastRuns"
        >
          Load All Last Runs
          <v-tooltip activator="parent" location="bottom">
            Load last run status for all schedules on this page
          </v-tooltip>
        </v-btn>
      </div>

      <v-data-table-server
        :headers="headers"
        :items="tasks"
        :loading="loading"
        :loading-text="loadingText"
        :items-per-page="selectedLimit"
        :items-length="props.paginator.count"
        :items-per-page-options="limits"
        v-model:page="currentPage"
        class="elevation-1"
        item-key="id"
        @update:options="onUpdateOptions"
        :hide-default-footer="props.paginator.count === 0"
        :hide-default-header="props.paginator.count === 0"
      >
        <template #loading>
          <div class="d-flex flex-column align-center justify-center pa-8">
            <v-progress-circular indeterminate size="64" />
            <div class="mt-4 text-body-1">{{ loadingText || 'Fetching tasks...' }}</div>
          </div>
        </template>

        <template #no-data>
          <div class="text-center pa-4">
            <v-icon size="x-large" class="mb-2">mdi-format-list-bulleted</v-icon>
            <div class="text-h6 text-grey-darken-1 mb-2">No tasks found</div>
          </div>
        </template>

        <template #[`item.schedule_name`]="{ item }">
          <span v-if="item.schedule_name === null">
            {{ item.original_schedule_name }}
          </span>
          <router-link
            v-else
            :to="{ name: 'schedule-detail', params: { scheduleName: item.schedule_name } }"
          >
            {{ item.schedule_name }}
          </router-link>
        </template>

        <template #[`item.requested`]="{ item }">
          <v-tooltip location="bottom">
            <template #activator="{ props }">
              <span v-bind="props">
                {{ fromNow(getTimestampStringForStatus(item.timestamp, 'requested')) }}
              </span>
            </template>
            <span>{{ formatDt(getTimestampStringForStatus(item.timestamp, 'requested')) }}</span>
          </v-tooltip>
        </template>

        <template #[`item.started`]="{ item }">
          <v-tooltip location="bottom">
            <template #activator="{ props }">
              <span v-bind="props" class="text-no-wrap">
                <router-link :to="{ name: 'task-detail', params: { id: item.id } }">
                  {{ fromNow(getTimestampStringForStatus(item.timestamp, 'reserved')) }}
                </router-link>
              </span>
            </template>
            <span>{{ formatDt(getTimestampStringForStatus(item.timestamp, 'reserved')) }}</span>
          </v-tooltip>
        </template>

        <template #[`item.completed`]="{ item }">
          <v-tooltip location="bottom">
            <template #activator="{ props }">
              <span v-bind="props" class="text-no-wrap">
                <router-link :to="{ name: 'task-detail', params: { id: item.id } }">
                  {{ fromNow(item.updated_at) }}
                </router-link>
              </span>
            </template>
            <span>{{ formatDt(item.updated_at as string) }}</span>
          </v-tooltip>
        </template>

        <template #[`item.stopped`]="{ item }">
          <v-tooltip location="bottom">
            <template #activator="{ props }">
              <span v-bind="props" class="text-no-wrap">
                <router-link :to="{ name: 'task-detail', params: { id: item.id } }">
                  {{ fromNow(item.updated_at) }}
                </router-link>
              </span>
            </template>
            <span>{{ formatDt(item.updated_at) }}</span>
          </v-tooltip>
        </template>

        <template #[`item.resources`]="{ item }">
          <div class="d-flex flex-sm-column flex-lg-row py-1">
            <ResourceBadge kind="cpu" :value="item.config.resources.cpu" variant="text" />
            <ResourceBadge kind="memory" :value="item.config.resources.memory" variant="text" />
            <ResourceBadge kind="disk" :value="item.config.resources.disk" variant="text" />
          </div>
        </template>

        <template #[`item.worker`]="{ item }">
          <router-link
            v-if="item.worker_name"
            :to="{ name: 'worker-detail', params: { workerName: item.worker_name } }"
            class="text-decoration-none"
          >
            {{ item.worker_name }}
          </router-link>
          <span v-else>n/a</span>
        </template>

        <template #[`item.remove`]="{ item }">
          <RemoveRequestedTaskButton
            v-if="canUnRequestTasks"
            :id="item.id"
            @requested-task-removed="emit('loadData', selectedLimit, 0)"
          />
        </template>

        <template #[`item.cancel`]="{ item }">
          <CancelTaskButton
            v-if="canCancelTasks"
            :id="item.id"
            @task-canceled="emit('loadData', selectedLimit, 0)"
          />
        </template>

        <template #[`item.duration`]="{ item }">
          {{
            formatDurationBetween(
              getTimestampStringForStatus(
                item.timestamp,
                'started',
                getTimestampStringForStatus(item.timestamp, 'reserved'),
              ),
              item.updated_at,
            )
          }}
        </template>

        <template #[`item.status`]="{ item }">
          <code class="text-pink-accent-2">{{ item.status }}</code>
        </template>

        <template #[`item.last_run`]="{ item }">
          <div v-if="item.schedule_name" class="d-flex align-center">
            <span v-if="schedulesLastRuns[item.schedule_name]">
              <code :class="statusClass(schedulesLastRuns[item.schedule_name].status)">
                {{ schedulesLastRuns[item.schedule_name].status }} </code
              >,
              <TaskLink
                :id="schedulesLastRuns[item.schedule_name].id"
                :updatedAt="schedulesLastRuns[item.schedule_name].updated_at"
                :status="schedulesLastRuns[item.schedule_name].status"
                :timestamp="schedulesLastRuns[item.schedule_name].timestamp"
              />
            </span>
            <v-btn
              :icon="loadingSchedules[item.schedule_name] ? 'mdi-loading' : 'mdi-refresh'"
              :loading="loadingSchedules[item.schedule_name]"
              :disabled="loadingSchedules[item.schedule_name]"
              size="small"
              variant="text"
              color="primary"
              @click="handleLoadLastRun(item.schedule_name)"
              density="comfortable"
              class="ml-2"
            >
              <v-icon :class="{ 'mdi-spin': loadingSchedules[item.schedule_name] }">
                {{ loadingSchedules[item.schedule_name] ? 'mdi-loading' : 'mdi-refresh' }}
              </v-icon>
              <v-tooltip activator="parent" location="bottom">
                {{
                  loadingSchedules[item.schedule_name]
                    ? 'Loading...'
                    : 'Load/refresh last run status'
                }}
              </v-tooltip>
            </v-btn>
          </div>
        </template>

        <template #[`item.requested_by`]="{ item }">
          {{ (item as TaskLight | RequestedTaskLight).requested_by }}
        </template>
      </v-data-table-server>
      <ErrorMessage v-for="error in errors" :key="error" :message="error" />
    </v-card>
  </div>
</template>

<script setup lang="ts">
import CancelTaskButton from '@/components/CancelTaskButton.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import RemoveRequestedTaskButton from '@/components/RemoveRequestedTaskButton.vue'
import ResourceBadge from '@/components/ResourceBadge.vue'
import TaskLink from '@/components/TaskLink.vue'
import type { MostRecentTask, Paginator } from '@/types/base'
import type { RequestedTaskLight } from '@/types/requestedTasks'
import type { TaskLight } from '@/types/tasks'
import { formatDt, formatDurationBetween, fromNow } from '@/utils/format'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { computed, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const props = defineProps<{
  headers: { title: string; value: string }[] // the headers to display
  canUnRequestTasks: boolean // whether the user can unrequest tasks
  canCancelTasks: boolean // whether the user can cancel tasks
  loading: boolean // whether the table is loading
  loadingText: string // the text to display when the table is loading
  tasks: TaskLight[] | RequestedTaskLight[] // the tasks to display
  paginator: Paginator // the paginator
  schedulesLastRuns: Record<string, MostRecentTask> // the last runs for each schedule
  errors: string[] // the errors to display
}>()

const emit = defineEmits<{
  limitChanged: [limit: number]
  loadData: [limit: number, skip: number]
  loadLastRun: [scheduleName: string]
  loadAllLastRuns: []
}>()

const router = useRouter()
const route = useRoute()

const limits = [10, 20, 50, 100]
const selectedLimit = ref(Number(route.query.limit) || props.paginator.limit)
const currentPage = ref(Number(route.query.page) || 1)
const loadingSchedules = ref<Record<string, boolean>>({})
const loadingAllSchedules = ref(false)

// Check if we should show the "Load All Last Runs" button (only in failed tab)
const showLoadAllButton = computed(() => {
  return props.headers.some((header) => header.value === 'last_run')
})

function onUpdateOptions(options: { page: number; itemsPerPage: number }) {
  // Only update if the values actually changed to avoid infinite loops
  if (
    Number(route.query.page) === options.page &&
    Number(route.query.limit) === options.itemsPerPage
  ) {
    return
  }
  router.replace({
    query: { ...route.query, limit: options.itemsPerPage.toString(), page: options.page.toString() }
  })
}

// Sync with route query changes to emit loadData once
watch(
  () => route.query,
  (newQuery) => {
    const limit = Number(newQuery.limit) || props.paginator.limit
    const page = Number(newQuery.page) || 1
    const skip = (page - 1) * limit

    currentPage.value = page
    selectedLimit.value = limit

    emit('loadData', limit, skip)
  },
  { immediate: true }
)

function statusClass(status: string) {
  if (status === 'succeeded') return 'schedule-succeeded'
  else if (['failed', 'canceled', 'cancel_requested'].includes(status)) return 'schedule-failed'
  else return 'schedule-running'
}

async function handleLoadLastRun(scheduleName: string) {
  if (!scheduleName) return
  loadingSchedules.value[scheduleName] = true
  try {
    emit('loadLastRun', scheduleName)
  } finally {
    loadingSchedules.value[scheduleName] = false
  }
}

async function handleLoadAllLastRuns() {
  loadingAllSchedules.value = true
  try {
    emit('loadAllLastRuns')
  } finally {
    loadingAllSchedules.value = false
  }
}
</script>

<style scoped>
.mdi-spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
