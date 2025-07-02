<template>
  <div>
    <v-card v-if="!errors.length" :class="{ 'loading': loading }" flat>
      <v-card-title class="d-flex align-center justify-space-between">
        <span class="text-subtitle-1 d-flex align-center">
          Showing max.
          <v-select
            v-model="selectedLimit"
            :items="limits"
            @change="emit('limitChanged', selectedLimit)"
            hide-details
            density="compact"
          />
          out of <strong class="ml-1 mr-1">{{ props.paginator.count }}</strong> results
        </span>
      </v-card-title>
      <v-data-table-server
        :headers="headers"
        :items="tasks"
        :loading="loading"
        :items-per-page="selectedLimit"
        :items-length="props.paginator.count"
        :items-per-page-options="limits"
        class="elevation-1"
        item-key="id"
        @update:itemsPerPage="emit('limitChanged', $event)"
        @update:options="onUpdateOptions"
      >
        <template #[`item.schedule_name`]="{ item }">
          <span v-if="item.schedule_name === null || item.schedule_name === 'none'">
            {{ item.original_schedule_name }}
          </span>
          <router-link v-else :to="{ name: 'schedule-detail', params: { schedule_name: item.schedule_name } }">
            {{ item.schedule_name }}
          </router-link>
        </template>

        <template #[`item.requested`]="{ item }">
          <v-tooltip location="bottom">
            <template #activator="{ props }">
              <span v-bind="props">
                {{ fromNow((item.timestamp as Record<string, unknown>).requested as string) }}
              </span>
            </template>
            <span>{{ formatDt((item.timestamp as Record<string, unknown>).requested as string) }}</span>
          </v-tooltip>
        </template>

        <template #[`item.started`]="{ item }">
          <v-tooltip location="bottom">
            <template #activator="{ props }">
              <span v-bind="props">
                <router-link :to="{ name: 'task-detail', params: { id: item.id } }">
                  {{ fromNow((item.timestamp as Record<string, unknown>).reserved as string) }}
                </router-link>
              </span>
            </template>
            <span>{{ formatDt((item.timestamp as Record<string, unknown>).reserved as string) }}</span>
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
          <ResourceBadge kind="cpu" :value="item.config.resources.cpu" />
          <ResourceBadge kind="memory" :value="item.config.resources.memory" />
          <ResourceBadge kind="disk" :value="item.config.resources.disk" />
        </template>

        <template #[`item.worker`]="{ item }">
          <code class="text-pink-accent-2" v-if="item.worker_name">{{ item.worker_name }}</code>
          <span v-else>n/a</span>
        </template>

        <template #[`item.remove`]="{ item }">
          <RemoveRequestedTaskButton v-if="canUnRequestTasks" :id="item.id" @requested-task-removed="emit('loadData', selectedLimit, 0)" />
        </template>

        <template #[`item.duration`]="{ item }">
          {{ formatDurationBetween((item.timestamp as Record<string, unknown>).started as string, item.updated_at) }}
        </template>

        <template #[`item.status`]="{ item }">
          <code class="text-pink-accent-2">{{ item.status }}</code>
        </template>

        <template #[`item.last_run`]="{ item }">
          <span v-if="lastRunsLoaded && schedulesLastRuns[item.schedule_name]">
            <code :class="statusClass(getPropertyFor(item.schedule_name, 'status') as string)">
              {{ getPropertyFor(item.schedule_name, 'status') }}
            </code>,
            <TaskLink
              :id="getPropertyFor(item.schedule_name, 'id', '-')"
              :updatedAt="getPropertyFor(item.schedule_name, 'updated_at')"
            />
          </span>
        </template>

        <template #[`item.requested_by`]="{ item }">
          {{ (item as any).requested_by }}
        </template>

      </v-data-table-server>
      <ErrorMessage v-for="error in errors" :key="error" :message="error" />
    </v-card>
  </div>
</template>

<script setup lang="ts">
import ErrorMessage from '@/components/ErrorMessage.vue';
import RemoveRequestedTaskButton from '@/components/RemoveRequestedTaskButton.vue';
import ResourceBadge from '@/components/ResourceBadge.vue';
import TaskLink from '@/components/TaskLink.vue';
import type { Paginator } from '@/types/base';
import type { RequestedTaskLight } from '@/types/requestedTasks';
import type { TaskLight } from '@/types/tasks';
import { formatDt, formatDurationBetween, fromNow } from '@/utils/format';
import { ref, watch } from 'vue';

const props = defineProps<{
  headers: { title: string; value: string }[] // the headers to display
  canUnRequestTasks: boolean // whether the user can unrequest tasks
  loading: boolean // whether the table is loading
  tasks: TaskLight[] | RequestedTaskLight[] // the tasks to display
  paginator: Paginator // the paginator
  lastRunsLoaded: boolean // whether the last runs have been loaded
  schedulesLastRuns: Record<string, Record<string, unknown>> // the last runs for each schedule
  errors: string[] // the errors to display
}>();

const emit = defineEmits<{
  'limitChanged': [limit: number]
  'loadData': [limit: number, skip: number]
}>();

const limits = [10, 20, 50, 100];
const selectedLimit = ref(props.paginator.limit);

function onUpdateOptions(options: { page: number, itemsPerPage: number }) {
  //  number is the next number, we need to calculate the skip for the request
  const page = options.page > 1 ? options.page - 1 : 0
  emit('loadData', options.itemsPerPage, page * options.itemsPerPage);
}

watch(() => props.paginator, (newPaginator) => {
  selectedLimit.value = newPaginator.limit;
});



function getPropertyFor(schedule_name: string, property: string, otherwise?: unknown): string {
  const last_run = props.schedulesLastRuns[schedule_name];
  if (last_run && last_run[property]) return String(last_run[property]);
  if (otherwise) return String(otherwise);
  return '';
}

function statusClass(status: string) {
  if (status === 'succeeded') return 'schedule-succeeded'
  else if (['failed', 'canceled', 'cancel_requested'].includes(status)) return 'schedule-failed'
  else return 'schedule-running'
}
</script>
