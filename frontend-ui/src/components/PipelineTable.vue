<template>
  <div>
    <v-card v-if="!errors.length" :class="{ loading: loading }" flat color="transparent">
      <v-data-table-server
        :headers="headers"
        :items="tasks"
        :loading="loading"
        :loading-text="loadingText"
        :page="props.paginator.page"
        :items-per-page="props.paginator.limit"
        :items-length="props.paginator.count"
        :items-per-page-options="limits"
        :mobile="smAndDown"
        :density="smAndDown ? 'compact' : 'comfortable'"
        class="pipeline-table"
        item-key="id"
        @update:options="onUpdateOptions"
        :hide-default-footer="props.paginator.count === 0"
        :hide-default-header="props.paginator.count === 0"
        disable-sort
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

        <template #[`item.recipe_name`]="{ item }">
          <span v-if="item.recipe_name === null">
            {{ item.original_recipe_name }}
          </span>
          <router-link
            v-else
            :to="{ name: 'recipe-detail', params: { recipeName: item.recipe_name } }"
          >
            {{ item.recipe_name }}
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
                  {{ fromNow(getTimestampStringForStatus(item.timestamp, 'succeeded')) }}
                </router-link>
              </span>
            </template>
            <span>{{ formatDt(getTimestampStringForStatus(item.timestamp, 'succeeded')) }}</span>
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
          <div
            :class="[
              'd-flex',
              'flex-row flex-wrap',
              'flex-md-column',
              { 'justify-end': smAndDown },
            ]"
          >
            <ResourceBadge
              kind="cpu"
              :value="item.config.resources.cpu"
              variant="text"
              :custom-class="smAndDown ? 'pa-0' : undefined"
            />
            <ResourceBadge
              kind="memory"
              :value="item.config.resources.memory"
              variant="text"
              :custom-class="smAndDown ? 'pa-0' : undefined"
            />
            <ResourceBadge
              kind="disk"
              :value="item.config.resources.disk"
              variant="text"
              :custom-class="smAndDown ? 'pa-0' : undefined"
            />
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

        <template #[`item.diagnose`]="{ item }">
          <v-btn
            v-if="props.canRequestTasks"
            size="small"
            color="primary"
            variant="tonal"
            @click="diagnoseTask(item as RequestedTaskLight)"
          >
            Diagnose
          </v-btn>
        </template>

        <template #[`item.remove`]="{ item }">
          <RemoveRequestedTaskButton
            v-if="canUnRequestTasks"
            :id="item.id"
            :size="smAndDown ? 'x-small' : 'small'"
            @requested-task-removed="emit('loadData', props.paginator.limit, 0)"
          />
        </template>

        <template #[`item.cancel`]="{ item }">
          <code
            v-if="item.status === 'canceling' || item.status === 'cancel_requested'"
            class="text-pink-accent-2"
          >
            {{ item.status }}
          </code>
          <CancelTaskButton
            v-else-if="canCancelTasks"
            :id="item.id"
            :size="smAndDown ? 'x-small' : 'small'"
            @task-canceled="emit('loadData', props.paginator.limit, 0)"
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
          <div
            v-if="(item as TaskLight).recipe_most_recent_task"
            :class="['ga-1', 'd-flex', 'align-center', 'flex-wrap', { 'justify-end': smAndDown }]"
          >
            <span>
              <code :class="statusClass((item as TaskLight).recipe_most_recent_task!.status)">
                {{ (item as TaskLight).recipe_most_recent_task!.status }} </code
              >,
            </span>
            <TaskLink
              :id="(item as TaskLight).recipe_most_recent_task!.id"
              :updatedAt="(item as TaskLight).recipe_most_recent_task!.updated_at"
              :status="(item as TaskLight).recipe_most_recent_task!.status"
              :timestamp="(item as TaskLight).recipe_most_recent_task!.timestamp"
            />
          </div>
        </template>

        <template #[`item.requested_by`]="{ item }">
          {{ (item as TaskLight | RequestedTaskLight).requested_by }}
        </template>
      </v-data-table-server>
      <ErrorMessage v-for="error in errors" :key="error" :message="error" />
      <DiagnoseTaskDialog v-model="isDiagnoseDialogOpen" :task="selectedTaskToDiagnose" />
      <ConfirmDialog
        v-model="isConfirmDiagnoseOpen"
        title="Confirm Diagnostics"
        message="Running diagnostics will consume significant resources and should be run only when something is really unexplained or seems abnormal. Do you want to continue?"
        confirm-text="Run Diagnostics"
        confirm-color="primary"
        icon="mdi-alert"
        @confirm="startDiagnostics"
      />
    </v-card>
  </div>
</template>

<script setup lang="ts">
import CancelTaskButton from '@/components/CancelTaskButton.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DiagnoseTaskDialog from '@/components/DiagnoseTaskDialog.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import RemoveRequestedTaskButton from '@/components/RemoveRequestedTaskButton.vue'
import ResourceBadge from '@/components/ResourceBadge.vue'
import TaskLink from '@/components/TaskLink.vue'
import type { Paginator } from '@/types/base'
import type { RequestedTaskLight } from '@/types/requestedTasks'
import type { TaskLight } from '@/types/tasks'
import { formatDt, formatDurationBetween, fromNow } from '@/utils/format'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useDisplay } from 'vuetify'

const router = useRouter()
const route = useRoute()

const { smAndDown } = useDisplay()

const props = defineProps<{
  headers: { title: string; value: string }[] // the headers to display
  canRequestTasks?: boolean // whether the user can request tasks
  canUnRequestTasks: boolean // whether the user can unrequest tasks
  canCancelTasks: boolean // whether the user can cancel tasks
  loading: boolean // whether the table is loading
  loadingText: string // the text to display when the table is loading
  tasks: TaskLight[] | RequestedTaskLight[] // the tasks to display
  paginator: Paginator // the paginator
  errors: string[] // the errors to display
}>()

const emit = defineEmits<{
  limitChanged: [limit: number]
  loadData: [limit: number, skip: number]
}>()

const limits = [10, 20, 50, 100]

const isDiagnoseDialogOpen = ref(false)
const isConfirmDiagnoseOpen = ref(false)
const selectedTaskToDiagnose = ref<RequestedTaskLight | null>(null)
const taskToConfirmDiagnose = ref<RequestedTaskLight | null>(null)

function onUpdateOptions(options: { page: number; itemsPerPage: number }) {
  const query = { ...route.query }

  if (options.page > 1) {
    query.page = options.page.toString()
  } else {
    delete query.page
  }

  router.push({ query })

  if (options.itemsPerPage != props.paginator.limit) {
    emit('limitChanged', options.itemsPerPage)
  }
}

function statusClass(status: string) {
  if (status === 'succeeded') return 'recipe-succeeded'
  else if (['failed', 'canceled', 'cancel_requested'].includes(status)) return 'recipe-failed'
  else return 'recipe-running'
}

function diagnoseTask(task: RequestedTaskLight) {
  taskToConfirmDiagnose.value = task
  isConfirmDiagnoseOpen.value = true
}

function startDiagnostics() {
  if (taskToConfirmDiagnose.value) {
    selectedTaskToDiagnose.value = taskToConfirmDiagnose.value
    isDiagnoseDialogOpen.value = true
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

/* make the table itself transparent so grey appears only on rows */
.pipeline-table {
  background: transparent !important;
}

/* border-collapse: separate for spacing on rows */
.pipeline-table :deep(.v-table__wrapper > table) {
  border-collapse: separate !important;
  border-spacing: 0 6px !important;
}

/* themed background for each row */
.pipeline-table :deep(tbody tr) {
  background-color: rgba(var(--v-theme-on-surface), 0.05);
}

/* counteract outer top/bottom gaps from border-spacing */
.pipeline-table :deep(tbody) {
  margin-top: -6px;
  margin-bottom: -6px;
}

/* remove cell borders since spacing handles separation */
.pipeline-table :deep(tbody tr td) {
  border-bottom: none !important;
}

/* make the table header row transparent to remove grey bg for header */
.pipeline-table :deep(thead) {
  background: transparent !important;
}

.pipeline-table :deep(thead tr th) {
  border-bottom: none !important;
}

/* removes the separator between the tiles and pagination */
.pipeline-table :deep(.v-data-table-footer) {
  background: transparent !important;
  border-top: none !important;
}

/* removes any divider/border from the table wrapper */
.pipeline-table :deep(.v-table__wrapper) {
  border-bottom: none !important;
}
</style>
