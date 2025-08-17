<template>
  <div>
    <v-card v-if="!errors.length" :class="{ 'loading': loading }" flat>
      <v-card-title v-if="paginator.count > 0" class="d-flex align-center justify-space-between flex-wrap py-2">
        <span class="text-subtitle-1 d-flex align-center">
          Showing max.
          <v-select
            v-model="selectedLimit"
            :items="limits"
            @update:model-value="emit('limitChanged', $event)"
            hide-details
            density="compact"
          />
         out of <strong class="ml-1 mr-1">{{ paginator.count }}</strong> results
        </span>
        <div class="d-flex align-center">
          <RequestSelectionButton
            :can-request-tasks="canRequestTasks"
            :requesting-text="requestingText"
            :count="paginator.count"
            @fetch-schedules="emit('fetchSchedules')"
          />
          <v-btn
            size="small"
            variant="outlined"
            class="ml-2"
            @click="emit('clearFilters')"
          >
            <v-icon size="small" class="mr-1">mdi-close-circle</v-icon>
            clear
          </v-btn>
        </div>
      </v-card-title>

      <v-data-table-server
        :headers="headers"
        :items="schedules"
        :loading="loading"
        :items-per-page="selectedLimit"
        :items-length="paginator.count"
        :items-per-page-options="limits"
        class="elevation-1"
        item-key="name"
        @update:options="onUpdateOptions"
        :hide-default-footer="props.paginator.count === 0"
        :hide-default-header="props.paginator.count === 0"
      >
        <template #loading>
          <div class="d-flex flex-column align-center justify-center pa-8">
            <v-progress-circular indeterminate size="64" />
              <div class="mt-4 text-body-1">{{ loadingText || 'Fetching recipes...' }}</div>
            </div>
        </template>

        <template #[`item.name`]="{ item }">
          <router-link :to="{ name: 'schedule-detail', params: { scheduleName: item.name } }">
            <span class="d-flex align-center">
              {{ item.name }}
              <v-icon v-if="!item.enabled" size="small" color="orange" class="ml-1">
                mdi-pause
              </v-icon>
            </span>
          </router-link>
        </template>

        <template #[`item.category`]="{ item }">
          {{ item.category }}
        </template>

        <template #[`item.language`]="{ item }">
          {{ item.language.name_en }}
        </template>

        <template #[`item.offliner`]="{ item }">
          {{ item.config.offliner || 'Unknown' }}
        </template>

        <template #[`item.requested`]="{ item }">
          <v-icon v-if="item.is_requested" size="small" color="success">
            mdi-check
          </v-icon>
        </template>

        <template #[`item.last_task`]="{ item }">
          <div v-if="item.most_recent_task">
            <code :class="statusClass(item.most_recent_task.status)">
              {{ item.most_recent_task.status }}
            </code>
            <br>
            <TaskLink
              :id="item.most_recent_task.id"
              :updated-at="item.most_recent_task.updated_at"
            />
          </div>
          <span v-else>-</span>
        </template>

        <template #no-data>
          <div class="text-center pa-4">
            <v-icon size="x-large" class="mb-2">mdi-format-list-bulleted</v-icon>
            <div class="text-h6 text-grey-darken-1 mb-2">No recipes found</div>
          </div>
        </template>
      </v-data-table-server>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import RequestSelectionButton from '@/components/RequestSelectionButton.vue'
import TaskLink from '@/components/TaskLink.vue'
import type { Paginator } from '@/types/base'
import type { ScheduleLight } from '@/types/schedule'
import { ref, watch } from 'vue'

// Props
interface Props {
  requestingText: string | null
  headers: { title: string; value: string }[]
  schedules: ScheduleLight[]
  paginator: Paginator
  loading: boolean
  errors: string[]
  loadingText: string
  canRequestTasks: boolean
  filters: {
    name: string
    categories: string[]
    languages: string[]
    tags: string[]
  }
}

const props = defineProps<Props>()

// Define emits
const emit = defineEmits<{
  'limitChanged': [limit: number]
  'loadData': [limit: number, skip: number]
  'clearFilters': []
  'fetchSchedules': []
}>()

const limits = [10, 20, 50, 100]
const selectedLimit = ref(props.paginator.limit)

function onUpdateOptions(options: { page: number, itemsPerPage: number }) {
  // page is 1-indexed, we need to calculate the skip for the request
  const page = options.page > 1 ? options.page - 1 : 0
  emit('loadData', options.itemsPerPage, page * options.itemsPerPage)
}

watch(() => props.paginator, (newPaginator) => {
  selectedLimit.value = newPaginator.limit
}, { immediate: true })

function statusClass(status: string) {
  if (status === 'succeeded') return 'schedule-succeeded'
  else if (['failed', 'canceled', 'cancel_requested'].includes(status)) return 'schedule-failed'
  else return 'schedule-running'
}
</script>

<style scoped>
.schedule-succeeded {
  color: #4caf50;
}

.schedule-failed {
  color: #f44336;
}

.schedule-running {
  color: #ff9800;
}
</style>
