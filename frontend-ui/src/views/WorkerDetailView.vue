<template>
  <v-container>
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12" class="d-flex align-center">
        <code class="text-h6 mr-2">{{ workerName }}</code>
        <v-chip
          :color="metrics?.status === 'online' ? 'success' : 'dark'"
          size="small"
          variant="tonal"
          :prepend-icon="metrics?.status === 'online' ? 'mdi-server' : 'mdi-skull-crossbones'"
        >
          {{ metrics?.status || 'offline' }}
        </v-chip>
      </v-col>
    </v-row>

    <div v-if="!error && metrics">
      <!-- Tabs -->
      <v-tabs v-model="currentTab" class="mb-4">
        <v-tab :to="{ name: 'worker-detail', params: { workerName } }" value="details">Info</v-tab>
        <v-tab
          :to="{ name: 'worker-detail-tab', params: { workerName, selectedTab: 'edit' } }"
          value="edit"
          >Edit</v-tab
        >
      </v-tabs>

      <v-window v-model="currentTab">
        <!-- Info Tab -->
        <v-window-item value="details">
          <v-row>
            <v-col cols="12" sm="4">
              <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-progress-circular
                    :model-value="percentCpu"
                    :color="colorCpu"
                    size="44"
                    width="4"
                  >
                    <span class="text-caption">{{ percentCpu }}%</span>
                  </v-progress-circular>
                  <div class="ml-3">
                    <div class="text-caption text-medium-emphasis">CPU</div>
                    <div class="text-body-2">{{ usageCpu }}</div>
                  </div>
                </div>
              </v-sheet>
            </v-col>
            <v-col cols="12" sm="4">
              <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-progress-circular
                    :model-value="percentMemory"
                    :color="colorMemory"
                    size="44"
                    width="4"
                  >
                    <span class="text-caption">{{ percentMemory }}%</span>
                  </v-progress-circular>
                  <div class="ml-3">
                    <div class="text-caption text-medium-emphasis">Memory</div>
                    <div class="text-body-2">{{ usageMemory }}</div>
                  </div>
                </div>
              </v-sheet>
            </v-col>
            <v-col cols="12" sm="4">
              <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-progress-circular
                    :model-value="percentDisk"
                    :color="colorDisk"
                    size="44"
                    width="4"
                  >
                    <span class="text-caption">{{ percentDisk }}%</span>
                  </v-progress-circular>
                  <div class="ml-3">
                    <div class="text-caption text-medium-emphasis">Disk</div>
                    <div class="text-body-2">{{ usageDisk }}</div>
                  </div>
                </div>
              </v-sheet>
            </v-col>
          </v-row>

          <!-- Task metrics -->
          <v-row class="mt-2">
            <v-col cols="12" sm="6" md="3">
              <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-icon class="mr-2" color="primary">mdi-format-list-bulleted</v-icon>
                  <div>
                    <div class="text-caption text-medium-emphasis">Total tasks</div>
                    <div class="text-h6">{{ metrics.nb_tasks_total }}</div>
                  </div>
                </div>
              </v-sheet>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-icon class="mr-2" color="info">mdi-flag-checkered</v-icon>
                  <div>
                    <div class="text-caption text-medium-emphasis">Completed</div>
                    <div class="text-h6">{{ metrics.nb_tasks_completed }}</div>
                  </div>
                </div>
              </v-sheet>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-icon class="mr-2" color="success">mdi-check-circle</v-icon>
                  <div>
                    <div class="text-caption text-medium-emphasis">Succeeded</div>
                    <div class="text-h6">{{ metrics.nb_tasks_succeeded }}</div>
                  </div>
                </div>
              </v-sheet>
            </v-col>
            <v-col cols="12" sm="6" md="3">
              <v-sheet rounded border class="pa-2 d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-icon class="mr-2" color="error">mdi-close-circle</v-icon>
                  <div>
                    <div class="text-caption text-medium-emphasis">Failed</div>
                    <div class="text-h6">{{ metrics.nb_tasks_failed }}</div>
                  </div>
                </div>
              </v-sheet>
            </v-col>
          </v-row>

          <v-row class="mt-2">
            <v-col cols="12" sm="3">
              <v-sheet rounded border class="pa-3">
                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon size="small" class="mr-1">mdi-ip-network-outline</v-icon>
                  Last IP
                </div>
                <div>
                  <code>{{ metrics.last_ip || '-' }}</code>
                </div>

                <v-divider class="my-3" />

                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon size="small" class="mr-1">mdi-shape</v-icon>
                  Contexts
                </div>
                <div class="d-flex flex-wrap ga-1 py-1">
                  <v-chip
                    v-for="ctx in metrics.contexts"
                    :key="ctx"
                    size="x-small"
                    color="primary"
                    variant="outlined"
                    density="comfortable"
                    class="text-caption text-uppercase"
                  >
                    {{ ctx }}
                  </v-chip>
                </div>

                <v-divider class="my-3" />

                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon size="small" class="mr-1">mdi-docker</v-icon>
                  Offliners
                </div>
                <div class="d-flex flex-wrap ga-1 py-1">
                  <v-chip
                    v-for="off in metrics.offliners"
                    :key="off"
                    size="x-small"
                    color="secondary"
                    variant="outlined"
                    density="comfortable"
                    class="text-uppercase text-caption"
                  >
                    {{ off }}
                  </v-chip>
                </div>
              </v-sheet>
            </v-col>
            <v-col cols="12" sm="9">
              <v-sheet rounded border class="pa-3">
                <div class="text-subtitle-2 mb-2">Running tasks</div>
                <v-table density="compact">
                  <thead>
                    <tr>
                      <th>Schedule</th>
                      <th>Resources</th>
                      <th>Task</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-if="metrics.running_tasks.length === 0">
                      <td colspan="3" class="text-medium-emphasis">No running tasks</td>
                    </tr>
                    <tr v-for="t in metrics.running_tasks" :key="t.id">
                      <td>
                        <span v-if="t.schedule_name === null">N/A</span>
                        <router-link
                          v-else
                          :to="{
                            name: 'schedule-detail',
                            params: { scheduleName: t.schedule_name },
                          }"
                        >
                          {{ t.schedule_name }}
                        </router-link>
                      </td>
                      <td>
                        <div class="d-flex flex-sm-column flex-lg-row py-1">
                          <ResourceBadge
                            kind="cpu"
                            :value="t.config.resources.cpu"
                            variant="text"
                          />
                          <ResourceBadge
                            kind="memory"
                            :value="t.config.resources.memory"
                            variant="text"
                          />
                          <ResourceBadge
                            kind="disk"
                            :value="t.config.resources.disk"
                            variant="text"
                          />
                        </div>
                      </td>
                      <td>
                        <TaskLink
                          v-if="t.id && t.updated_at"
                          :id="t.id"
                          :updated-at="t.updated_at"
                        />
                        <span v-else class="text-caption">-</span>
                      </td>
                    </tr>
                  </tbody>
                </v-table>
              </v-sheet>
            </v-col>
          </v-row>
        </v-window-item>

        <!-- Edit Tab -->
        <v-window-item value="edit">
          <v-card>
            <v-card-text>
              <v-form @submit.prevent="save">
                <v-row>
                  <v-col cols="12">
                    <v-combobox
                      v-model="editContexts"
                      density="compact"
                      variant="outlined"
                      label="Select a context or create a new one"
                      hint="Execute tasks that are associated with these contexts"
                      persistent-hint
                      :items="contexts"
                      multiple
                      chips
                      closable-chips
                      :clearable="!!editContexts.length"
                      :menu-props="{ maxHeight: '200px' }"
                      :custom-filter="(value, query) => fuzzyFilter(value, query, contexts)"
                    />
                  </v-col>
                </v-row>
                <div class="d-flex">
                  <v-spacer />
                  <v-btn color="primary" type="submit" :loading="saving" :disabled="!hasChanges"
                    >Update Worker</v-btn
                  >
                </div>
              </v-form>
            </v-card-text>
          </v-card>
        </v-window-item>
      </v-window>
    </div>

    <ErrorMessage v-if="error" :message="error" />
  </v-container>
</template>

<script setup lang="ts">
import ErrorMessage from '@/components/ErrorMessage.vue'
import ResourceBadge from '@/components/ResourceBadge.vue'
import TaskLink from '@/components/TaskLink.vue'
import type { Config } from '@/config'
import constants from '@/constants'
import { useContextStore } from '@/stores/context'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useWorkersStore } from '@/stores/workers'
import type { WorkerMetrics } from '@/types/workers'
import { fuzzyFilter, stringArrayEqual } from '@/utils/cmp'
import { formattedBytesSize } from '@/utils/format'
import { computed, inject, onMounted, ref, watch } from 'vue'

interface Props {
  workerName: string
  selectedTab?: string
}

const props = withDefaults(defineProps<Props>(), {
  selectedTab: 'details',
})

const config = inject<Config>(constants.config)
if (!config) {
  throw new Error('Config is not defined')
}

const workersStore = useWorkersStore()
const contextStore = useContextStore()
const loadingStore = useLoadingStore()
const notificationStore = useNotificationStore()

const error = ref<string | null>(null)
const metrics = ref<WorkerMetrics | null>(null)
const contexts = ref<string[]>([])
const currentTab = ref(props.selectedTab)
const saving = ref(false)

const editContexts = ref<string[]>([])

const hasChanges = computed(() => {
  const original = metrics.value?.contexts || []
  return !stringArrayEqual(editContexts.value, original)
})

const workerName = computed(() => props.workerName)

const usageCpu = computed(
  () => `${metrics.value?.current_usage.cpu ?? 0}/${metrics.value?.resources.cpu ?? 0}`,
)
const usageMemory = computed(
  () =>
    `${formattedBytesSize(metrics.value?.current_usage.memory ?? 0)}/${formattedBytesSize(
      metrics.value?.resources.memory ?? 0,
    )}`,
)
const usageDisk = computed(
  () =>
    `${formattedBytesSize(metrics.value?.current_usage.disk ?? 0)}/${formattedBytesSize(
      metrics.value?.resources.disk ?? 0,
    )}`,
)

function pctColor(pct: number): string {
  if (pct >= 90) return 'error'
  if (pct >= 70) return 'warning'
  return 'success'
}

const percentCpu = computed(() => {
  const max = metrics.value?.resources.cpu ?? 0
  const cur = metrics.value?.current_usage.cpu ?? 0
  return max > 0 ? Math.min(100, Math.round((cur * 100) / max)) : 0
})
const percentMemory = computed(() => {
  const max = metrics.value?.resources.memory ?? 0
  const cur = metrics.value?.current_usage.memory ?? 0
  return max > 0 ? Math.min(100, Math.round((cur * 100) / max)) : 0
})
const percentDisk = computed(() => {
  const max = metrics.value?.resources.disk ?? 0
  const cur = metrics.value?.current_usage.disk ?? 0
  return max > 0 ? Math.min(100, Math.round((cur * 100) / max)) : 0
})
const colorCpu = computed(() => pctColor(percentCpu.value))
const colorMemory = computed(() => pctColor(percentMemory.value))
const colorDisk = computed(() => pctColor(percentDisk.value))

async function refreshData() {
  loadingStore.startLoading('Fetching worker...')
  const res = await workersStore.fetchWorkerMetrics(workerName.value)
  if (res) {
    metrics.value = res
    editContexts.value = res.contexts || []
    error.value = null
  } else {
    error.value = workersStore.errors[0] || 'Failed to fetch worker'
    notificationStore.showError(error.value)
  }
  loadingStore.stopLoading()
}

async function save() {
  if (!metrics.value) return
  saving.value = true
  const ok = await workersStore.updateWorkerContext(workerName.value, {
    contexts: editContexts.value,
  })
  saving.value = false
  if (ok) {
    notificationStore.showSuccess('Worker updated')
    await refreshData()
    contexts.value = (await contextStore.fetchContexts()) || []
  }
}

onMounted(async () => {
  contexts.value = (await contextStore.fetchContexts()) || []
  await refreshData()
})

watch(
  () => props.selectedTab,
  (newVal) => {
    currentTab.value = newVal
    refreshData()
  },
)
</script>
