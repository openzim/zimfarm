<template>
  <div>
    <v-card v-if="!errors.length" :class="{ loading: loading }" flat>
      <v-data-table-server
        :headers="headers"
        :items="tasks"
        :loading="loading"
        :loading-text="loadingText"
        :items-per-page="selectedLimit"
        :items-length="props.paginator.count"
        :items-per-page-options="limits"
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
              <span v-bind="props">
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
              <span v-bind="props">
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
          <code class="text-pink-accent-2" v-if="item.worker_name">{{ item.worker_name }}</code>
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
              getTimestampStringForStatus(item.timestamp, 'started'),
              item.updated_at,
            )
          }}
        </template>

        <template #[`item.status`]="{ item }">
          <code class="text-pink-accent-2">{{ item.status }}</code>
        </template>

        <template #[`item.last_run`]="{ item }">
          <span
            v-if="lastRunsLoaded && item.schedule_name && schedulesLastRuns[item.schedule_name]"
          >
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
import { ref, watch } from 'vue'

const props = defineProps<{
  headers: { title: string; value: string }[] // the headers to display
  canUnRequestTasks: boolean // whether the user can unrequest tasks
  canCancelTasks: boolean // whether the user can cancel tasks
  loading: boolean // whether the table is loading
  loadingText: string // the text to display when the table is loading
  tasks: TaskLight[] | RequestedTaskLight[] // the tasks to display
  paginator: Paginator // the paginator
  lastRunsLoaded: boolean // whether the last runs have been loaded
  schedulesLastRuns: Record<string, MostRecentTask> // the last runs for each schedule
  errors: string[] // the errors to display
}>()

const emit = defineEmits<{
  limitChanged: [limit: number]
  loadData: [limit: number, skip: number]
}>()

const limits = [10, 20, 50, 100]
const selectedLimit = ref(props.paginator.limit)

function onUpdateOptions(options: { page: number; itemsPerPage: number }) {
  //  number is the next number, we need to calculate the skip for the request
  const page = options.page > 1 ? options.page - 1 : 0
  emit('loadData', options.itemsPerPage, page * options.itemsPerPage)
}

watch(
  () => props.paginator,
  (newPaginator) => {
    selectedLimit.value = newPaginator.limit
  },
  { immediate: true },
)

function statusClass(status: string) {
  if (status === 'succeeded') return 'schedule-succeeded'
  else if (['failed', 'canceled', 'cancel_requested'].includes(status)) return 'schedule-failed'
  else return 'schedule-running'
}
</script>
