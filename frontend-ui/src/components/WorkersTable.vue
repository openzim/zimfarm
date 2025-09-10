<template>
  <div>
    <v-card v-if="!errors.length" :class="{ loading: loading }" flat>
      <v-card-title class="d-flex align-center justify-end">
        <div class="d-flex align-center">
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
        :items="workers"
        :loading="loading"
        :items-per-page="selectedLimit"
        :items-length="props.paginator.count"
        :items-per-page-options="limits"
        class="elevation-1"
        hover
        item-key="name"
        item-value="name"
        v-model:expanded="expanded"
        show-expand
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
          <router-link :to="{ name: 'worker-detail', params: { workerName: item.name } }">
            <code>{{ item.name }}</code>
          </router-link>
        </template>

        <template #[`item.status`]="{ item }">
          <v-chip
            :color="item.status === 'online' ? 'success' : 'dark-grey'"
            size="small"
            variant="tonal"
            :prepend-icon="item.status === 'online' ? 'mdi-server' : 'mdi-skull-crossbones'"
          >
            {{ item.status }}
          </v-chip>
        </template>

        <template #[`item.last_seen`]="{ item }">
          <v-tooltip location="bottom">
            <template #activator="{ props }">
              <span v-bind="props">{{ fromNow(item.last_seen) }}</span>
            </template>
            <span>{{ formatDt(item.last_seen) }}</span>
          </v-tooltip>
        </template>

        <template #[`item.resources`]="{ item }">
          <div class="d-flex flex-column flex-md-row py-1">
            <ResourceBadge kind="cpu" :value="item.resources.cpu" variant="text" />
            <ResourceBadge kind="memory" :value="item.resources.memory" variant="text" />
            <ResourceBadge kind="disk" :value="item.resources.disk" variant="text" />
          </div>
        </template>

        <template #[`item.contexts`]="{ item }">
          <div class="d-flex flex-wrap ga-1 py-1">
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
          </div>
        </template>

        <template #no-data>
          <div class="text-center pa-4">
            <v-icon size="large" class="mb-2">mdi-robot-outline</v-icon>
            <div class="text-body-1">No workers found</div>
          </div>
        </template>

        <template #[`item.data-table-expand`]="{ internalItem, isExpanded, toggleExpand }">
          <v-btn
            :append-icon="isExpanded(internalItem) ? 'mdi-chevron-up' : 'mdi-chevron-down'"
            :text="
              isExpanded(internalItem)
                ? `Collapse (${internalItem.raw?.tasks?.length || 0})`
                : `Running tasks (${internalItem.raw?.tasks?.length || 0})`
            "
            class="text-none"
            :color="isExpanded(internalItem) ? 'primary' : 'medium-emphasis'"
            size="small"
            :variant="isExpanded(internalItem) ? 'tonal' : 'text'"
            width="140"
            border
            slim
            @click="toggleExpand(internalItem)"
          />
        </template>

        <template #expanded-row="{ columns, item }">
          <tr>
            <td :colspan="columns.length" class="py-2">
              <v-sheet rounded elevation="1">
                <v-data-table
                  :headers="taskHeaders"
                  :items="item.tasks || []"
                  density="compact"
                  hide-default-footer
                  hover
                  item-value="id"
                  hide-default-header
                  class="bg-grey-lighten-5"
                >
                  <template #[`item.schedule`]="{ item: task }">
                    <span v-if="task.schedule_name === null">{{
                      task.original_schedule_name
                    }}</span>
                    <router-link
                      v-else
                      :to="{
                        name: 'schedule-detail',
                        params: { scheduleName: task.schedule_name },
                      }"
                    >
                      {{ task.schedule_name }}
                    </router-link>
                  </template>
                  <template #[`item.task`]="{ item: task }">
                    <TaskLink :id="task.id" :updated-at="task.updated_at" />
                  </template>
                  <template #[`item.resources`]="{ item: task }">
                    <div class="d-flex flex-wrap flex-column flex-md-row py-1">
                      <ResourceBadge kind="cpu" :value="task.config.resources.cpu" variant="text" />
                      <ResourceBadge
                        kind="memory"
                        :value="task.config.resources.memory"
                        variant="text"
                      />
                      <ResourceBadge
                        kind="disk"
                        :value="task.config.resources.disk"
                        variant="text"
                      />
                    </div>
                  </template>
                  <template #no-data>
                    <div class="text-center py-4 text-grey">No running tasks</div>
                  </template>
                </v-data-table>
              </v-sheet>
            </td>
          </tr>
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
import type { Worker } from '@/types/workers'
import { formatDt, fromNow } from '@/utils/format'
import { computed, inject, onMounted, ref, watch } from 'vue'
import type { VueCookies } from 'vue-cookies'

const props = defineProps<{
  workerHeaders: { title: string; value: string }[]
  taskHeaders: { title: string; value: string }[]
  workers: Worker[]
  paginator: Paginator
  loading: boolean
  errors: string[]
  loadingText: string
}>()

const emit = defineEmits<{
  limitChanged: [limit: number]
  loadData: [limit: number, skip: number]
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
</script>
