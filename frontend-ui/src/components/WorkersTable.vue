<template>
  <div class="table-responsive">
    <v-card v-if="!errors.length" :class="{ loading: loading }" flat>
      <v-card-title class="d-flex align-center justify-end">
        <div class="d-flex align-center ga-2">
          <v-btn
            size="small"
            variant="outlined"
            color="secondary"
            class="text-none"
            @click="$emit('toggleWorkersList')"
          >
            {{ toggleText }}
          </v-btn>
          <v-btn
            size="small"
            variant="outlined"
            color="primary"
            :prepend-icon="
              expandedAll ? 'mdi-unfold-less-horizontal' : 'mdi-unfold-more-horizontal'
            "
            class="text-none"
            @click="toggleAllRows"
          >
            {{ expandedAll ? 'Collapse all' : 'Expand all' }}
          </v-btn>
        </div>
      </v-card-title>

      <v-data-table-server
        :headers="workerHeaders"
        :items="combinedItems"
        :loading="loading"
        :items-per-page="selectedLimit"
        :items-length="props.paginator.count"
        :items-per-page-options="limits"
        class="elevation-1 combined-table"
        item-key="id"
        item-value="name"
        v-model:expanded="expanded"
        show-expand
        :row-props="getRowProps"
        @update:options="onUpdateOptions"
        :hide-default-footer="props.paginator.count === 0"
        :hide-default-header="props.paginator.count === 0"
      >
        <template #loading>
          <div class="d-flex flex-column align-center justify-center pa-8">
            <v-progress-circular indeterminate size="64" />
            <div class="mt-4 text-body-1">{{ loadingText || 'Fetching workers...' }}</div>
          </div>
        </template>

        <template #[`item.name`]="{ item }">
          <template v-if="item.kind === 'worker'">
            <router-link :to="{ name: 'worker-detail', params: { workerName: item.name } }">
              <code>{{ item.name }}</code>
            </router-link>
          </template>
          <template v-else>
            <v-icon size="x-small" color="primary" class="mr-1">mdi-clipboard-text-outline</v-icon>
            <span v-if="item.task.schedule_name === null">{{
              item.task.original_schedule_name
            }}</span>
            <router-link
              v-else
              :to="{ name: 'schedule-detail', params: { scheduleName: item.task.schedule_name } }"
            >
              {{ item.task.schedule_name }}
            </router-link>
          </template>
        </template>

        <template #[`item.status`]="{ item }">
          <template v-if="item.kind === 'worker'">
            <v-chip
              :color="item.status === 'online' ? 'success' : 'dark-grey'"
              size="small"
              variant="tonal"
              :prepend-icon="item.status === 'online' ? 'mdi-server' : 'mdi-skull-crossbones'"
            >
              {{ item.status }}
            </v-chip>
          </template>
          <template v-else>
            <!-- Empty cell for tasks -->
          </template>
        </template>

        <template #[`item.last_seen`]="{ item }">
          <template v-if="item.kind === 'worker'">
            <v-tooltip location="bottom">
              <template #activator="{ props }">
                <span v-bind="props" class="text-no-wrap">{{ fromNow(item.last_seen) }}</span>
              </template>
              <span>{{ formatDt(item.last_seen) }}</span>
            </v-tooltip>
          </template>
          <template v-else>
            <TaskLink
              :id="item.task.id"
              :updatedAt="item.task.updated_at"
              :status="item.task.status"
              :timestamp="item.task.timestamp"
            />
          </template>
        </template>

        <template #[`item.resources`]="{ item }">
          <div class="d-flex flex-column flex-md-row py-1">
            <template v-if="item.kind === 'worker'">
              <ResourceBadge kind="cpu" :value="item.resources.cpu" variant="text" />
              <ResourceBadge kind="memory" :value="item.resources.memory" variant="text" />
              <ResourceBadge kind="disk" :value="item.resources.disk" variant="text" />
            </template>
            <template v-else>
              <ResourceBadge kind="cpu" :value="item.task.config.resources.cpu" variant="text" />
              <ResourceBadge
                kind="memory"
                :value="item.task.config.resources.memory"
                variant="text"
              />
              <ResourceBadge kind="disk" :value="item.task.config.resources.disk" variant="text" />
            </template>
          </div>
        </template>

        <template #[`item.contexts`]="{ item }">
          <div class="d-flex flex-wrap ga-1 py-1">
            <template v-if="item.kind === 'worker'">
              <v-chip
                v-for="ctx in item.contexts"
                :key="ctx"
                size="x-small"
                color="primary"
                variant="outlined"
                density="comfortable"
                class="mr-1 mb-1 text-caption text-uppercase"
              >
                {{ ctx }}
              </v-chip>
            </template>
            <template v-else>
              <!-- Empty for tasks -->
            </template>
          </div>
        </template>

        <template #no-data>
          <div class="text-center pa-4">
            <v-icon size="large" class="mb-2">mdi-robot-outline</v-icon>
            <div class="text-body-1">No workers found</div>
          </div>
        </template>

        <template #[`item.data-table-expand`]="{ item }">
          <template v-if="item.kind === 'worker'">
            <v-btn
              class="text-none"
              :color="expanded.includes(item.name) ? 'primary' : 'medium-emphasis'"
              size="small"
              :variant="expanded.includes(item.name) ? 'tonal' : 'text'"
              border
              slim
              @click="toggleWorkerRow(item.name)"
            >
              <span class="d-none d-md-inline">
                {{
                  expanded.includes(item.name)
                    ? `Collapse (${item.tasks?.length || 0})`
                    : `Running tasks (${item.tasks?.length || 0})`
                }}
              </span>

              <!-- Icon always visible -->
              <v-icon size="small" class="mr-1">
                {{ expanded.includes(item.name) ? 'mdi-chevron-up' : 'mdi-chevron-down' }}
              </v-icon>
            </v-btn>
          </template>
          <template v-else>
            <!-- Empty cell for tasks -->
          </template>
        </template>
      </v-data-table-server>
      <ErrorMessage v-for="error in errors" :key="error" :message="error" />
    </v-card>
  </div>
</template>

<script setup lang="ts">
import ErrorMessage from '@/components/ErrorMessage.vue'
import ResourceBadge from '@/components/ResourceBadge.vue'
import TaskLink from '@/components/TaskLink.vue'
import constants from '@/constants'
import type { Paginator } from '@/types/base'
import type { TaskLight } from '@/types/tasks'
import type { Worker } from '@/types/workers'
import { formatDt, fromNow } from '@/utils/format'
import { computed, inject, onMounted, ref, watch } from 'vue'
import type { VueCookies } from 'vue-cookies'

const props = defineProps<{
  workerHeaders: { title: string; value: string }[]
  workers: Worker[]
  paginator: Paginator
  loading: boolean
  errors: string[]
  loadingText: string
  toggleText: string
}>()

const emit = defineEmits<{
  limitChanged: [limit: number]
  loadData: [limit: number, skip: number]
  toggleWorkersList: []
}>()

const limits = [10, 20, 50, 100]
const selectedLimit = ref(props.paginator.limit)
const expanded = ref<string[]>([])

const expandedAll = computed(
  () => props.workers.length > 0 && props.workers.every((w) => expanded.value.includes(w.name)),
)

function toggleAllRows(): void {
  const willExpandAll = !expandedAll.value
  expanded.value = willExpandAll ? props.workers.map((w) => w.name) : []
  saveExpandAllPreference(willExpandAll)
}

function toggleWorkerRow(workerName: string): void {
  const index = expanded.value.indexOf(workerName)
  if (index !== -1) {
    expanded.value.splice(index, 1)
  } else {
    expanded.value.push(workerName)
  }
}

// Persist expand/collapse-all preference
const $cookies = inject<VueCookies>('$cookies')

function getExpandAllPreference(): boolean {
  const value = $cookies?.get('workers-expand-all')
  return value === null ? false : JSON.parse(value)
}

function saveExpandAllPreference(value: boolean): void {
  $cookies?.set('workers-expand-all', JSON.stringify(value), constants.COOKIE_LIFETIME_EXPIRY)
}

onMounted(() => {
  if (getExpandAllPreference()) {
    expanded.value = props.workers.map((w) => w.name)
  }
})

watch(
  () => props.workers,
  (newWorkers) => {
    if (getExpandAllPreference()) {
      expanded.value = newWorkers.map((w) => w.name)
    }
  },
)

function onUpdateOptions(options: { page: number; itemsPerPage: number }) {
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

// Build a combined flat list of rows (workers and their tasks) with a `kind` discriminator
type CombinedWorkerItem = Worker & { kind: 'worker'; id: string }
type CombinedTaskItem = { kind: 'task'; id: string; task: TaskLight; worker_name: string }
type CombinedRow = CombinedWorkerItem | CombinedTaskItem

const combinedItems = computed<CombinedRow[]>(() => {
  const rows: CombinedRow[] = []
  for (const worker of props.workers) {
    rows.push({
      kind: 'worker',
      id: `worker:${worker.name}`,
      ...worker,
    })
    if (expanded.value.includes(worker.name)) {
      const tasks = worker.tasks || []
      for (const task of tasks) {
        rows.push({
          kind: 'task',
          id: `task:${task.id}`,
          task,
          worker_name: worker.name,
        })
      }
    }
  }
  return rows
})

type RowProps = { class?: string | string[]; style?: string | Record<string, string> }

function getRowProps({
  internalItem,
  item,
}: {
  internalItem?: { raw?: CombinedRow }
  item?: CombinedRow
}): RowProps {
  const row = internalItem?.raw ?? item
  if (row?.kind === 'task') {
    return { class: 'bg-grey-lighten-4' }
  }
  return {}
}
</script>

<style scoped>
.table-responsive {
  width: 100%;
  overflow-x: auto; /* allows horizontal scroll */
}
</style>
