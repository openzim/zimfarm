<template>
  <v-container>
    <!-- Header -->
    <v-row class="mb-4">
      <v-col cols="12" class="d-flex flex-column flex-sm-row ga-2">
        <code class="text-h6 mr-2">{{ workerName }}</code>
        <div class="d-flex flex-wrap flex-align-center ga-2">
          <v-chip
            :color="worker?.status === 'online' ? 'success' : 'dark'"
            size="small"
            variant="tonal"
            :prepend-icon="worker?.status === 'online' ? 'mdi-server' : 'mdi-skull-crossbones'"
          >
            {{ worker?.status || 'offline' }}
          </v-chip>

          <!-- Local scheduling status -->
          <v-chip
            v-if="worker?.cordoned"
            color="info"
            size="small"
            variant="tonal"
            prepend-icon="mdi-pause-circle"
          >
            Cordoned by worker owner
          </v-chip>

          <!-- Admin scheduling status -->
          <v-chip
            v-if="worker?.admin_disabled"
            color="error"
            size="small"
            variant="tonal"
            prepend-icon="mdi-shield-alert"
          >
            Disabled by Zimfarm Administrator
          </v-chip>

          <!-- Selfish worker status -->
          <v-chip
            v-if="worker?.selfish"
            color="warning"
            size="small"
            variant="tonal"
            prepend-icon="mdi-account-lock"
          >
            Selfish
          </v-chip>
        </div>
      </v-col>
    </v-row>

    <div v-if="!error && worker">
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
                    <div class="text-h6">{{ worker.nb_tasks_total }}</div>
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
                    <div class="text-h6">{{ worker.nb_tasks_completed }}</div>
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
                    <div class="text-h6">{{ worker.nb_tasks_succeeded }}</div>
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
                    <div class="text-h6">{{ worker.nb_tasks_failed }}</div>
                  </div>
                </div>
              </v-sheet>
            </v-col>
          </v-row>

          <v-row class="mt-2">
            <v-col cols="12" sm="3">
              <v-sheet rounded border class="pa-3">
                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon size="small" class="mr-1">mdi-shape</v-icon>
                  Contexts
                </div>
                <div class="d-flex flex-wrap ga-1 py-1">
                  <v-chip
                    v-for="(ip, ctx) in worker.contexts"
                    :key="ctx"
                    size="x-small"
                    color="primary"
                    variant="outlined"
                    density="comfortable"
                    class="text-caption text-uppercase"
                  >
                    <template v-if="canUpdateWorkers && ip"> {{ ctx }}: {{ ip }} </template>
                    <template v-else>
                      {{ ctx }}
                    </template>
                  </v-chip>
                </div>

                <v-divider class="my-3" />

                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon size="small" class="mr-1">mdi-ip-network</v-icon>
                  Last IP
                  <v-tooltip v-if="worker.ip_changed" location="bottom">
                    <template #activator="{ props }">
                      <v-icon v-bind="props" size="small" color="warning" class="ml-1">
                        mdi-alert-circle-outline
                      </v-icon>
                    </template>
                    <span>IP discrepancy detected between worker IP and context IPs</span>
                  </v-tooltip>
                </div>
                <div class="text-body-2">
                  {{ worker.last_ip || 'N/A' }}
                </div>

                <v-divider class="my-3" />

                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon size="small" class="mr-1">mdi-docker</v-icon>
                  Offliners
                </div>
                <div class="d-flex flex-wrap ga-1 py-1">
                  <v-chip
                    v-for="off in worker.offliners"
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
                <v-data-table
                  :headers="runningTasksHeaders"
                  :items="worker.running_tasks"
                  :mobile="smAndDown"
                  :density="smAndDown ? 'compact' : 'comfortable'"
                  item-key="id"
                  hide-default-footer
                  disable-sort
                >
                  <template #no-data>
                    <div class="text-center pa-4 text-medium-emphasis">No running tasks</div>
                  </template>

                  <template #[`item.schedule_name`]="{ item }">
                    <span v-if="item.schedule_name === null">N/A</span>
                    <router-link
                      v-else
                      :to="{
                        name: 'schedule-detail',
                        params: { scheduleName: item.schedule_name },
                      }"
                    >
                      {{ item.schedule_name }}
                    </router-link>
                  </template>

                  <template #[`item.resources`]="{ item }">
                    <div :class="['d-flex', 'flex-row flex-wrap', { 'justify-end': smAndDown }]">
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

                  <template #[`item.task`]="{ item }">
                    <TaskLink
                      v-if="item.id && item.updated_at"
                      :id="item.id"
                      :updatedAt="item.updated_at"
                      :status="item.status"
                      :timestamp="item.timestamp"
                    />
                    <span v-else class="text-caption">-</span>
                  </template>
                </v-data-table>
              </v-sheet>
            </v-col>
          </v-row>
        </v-window-item>

        <!-- Edit Tab -->
        <v-window-item value="edit">
          <v-card v-if="canUpdateWorkers">
            <v-card-text>
              <v-form @submit.prevent="save">
                <!-- Worker Status Toggle -->
                <SwitchButton
                  :model-value="workerEnabled"
                  @update:model-value="updateWorkerEnabled"
                  label="Worker Status"
                  :details="
                    adminDisabled
                      ? 'Worker is disabled and will not receive new tasks'
                      : 'Worker is enabled and can receive new tasks'
                  "
                  density="compact"
                />
                <v-divider class="my-2" />
                <v-row>
                  <v-col cols="12">
                    <p class="text-body-2 text-medium-emphasis">
                      Configure the contexts and IP addresses for this worker.
                    </p>
                  </v-col>
                </v-row>

                <!-- Context Form Entries -->
                <v-row v-for="(context, index) in editContexts" :key="index">
                  <v-col cols="12" sm="6">
                    <v-combobox
                      v-model="context.name"
                      density="compact"
                      variant="outlined"
                      label="Select a context or create a new one"
                      hint="Execute tasks that are associated with these contexts"
                      persistent-hint
                      :items="contexts"
                      :menu-props="{ maxHeight: '200px' }"
                      :custom-filter="(value, query) => fuzzyFilter(value, query, contexts)"
                      :rules="[
                        (v) => !!v || 'Context name is required',
                        (v) => !isDuplicateContextName(v, index) || 'Context name must be unique',
                      ]"
                      required
                    />
                  </v-col>
                  <v-col cols="12" sm="5">
                    <v-text-field
                      v-model="context.ip"
                      label="IP address for this context"
                      hint="IP address that the context will be associated with"
                      density="compact"
                      variant="outlined"
                      persistent-hint
                      placeholder="192.168.1.1"
                    />
                  </v-col>
                  <v-col cols="12" sm="1">
                    <div>
                      <v-btn
                        icon="mdi-delete"
                        variant="elevated"
                        color="error"
                        size="small"
                        class="d-none d-sm-block"
                        @click="removeContext(index)"
                      />
                    </div>

                    <v-btn
                      variant="outlined"
                      color="error"
                      size="large"
                      class="d-flex d-sm-none w-100"
                      @click="removeContext(index)"
                    >
                      <v-icon size="large" class="mr-1">mdi-delete</v-icon>
                      Delete context
                    </v-btn>
                  </v-col>
                </v-row>

                <v-divider class="my-4" />

                <!-- Add Context Button -->
                <div class="d-flex flex-column flex-sm-row justify-end ga-2">
                  <v-btn
                    variant="outlined"
                    color="primary"
                    prepend-icon="mdi-plus"
                    :disabled="!canAddContext"
                    @click="addContext"
                  >
                    Add Context
                  </v-btn>
                  <v-btn color="primary" type="submit" :loading="saving" :disabled="!canSubmit">
                    Update Worker
                  </v-btn>
                </div>
              </v-form>
            </v-card-text>
          </v-card>
          <v-card v-else>
            <v-card-text class="text-center">
              <v-icon size="64" color="error">mdi-lock</v-icon>
              <h3 class="text-h6 mt-4">Access Denied</h3>
              <p class="text-body-2 text-medium-emphasis">
                You don't have permission to edit worker contexts.
              </p>
            </v-card-text>
          </v-card>
        </v-window-item>
      </v-window>
    </div>

    <ErrorMessage v-if="error" :message="error" />

    <!-- Worker Update Confirmation Dialog -->
    <ConfirmDialog
      v-model="showConfirmDialog"
      title="Confirm Contexts Update"
      confirm-text="Save Changes"
      cancel-text="Cancel"
      confirm-color="primary"
      icon="mdi-pencil"
      icon-color="primary"
      :max-width="600"
      :loading="saving"
      @confirm="handleConfirmUpdate"
      @cancel="handleCancelUpdate"
    >
      <template #content>
        <div class="mb-4">
          <h3 class="text-h6 mb-2">Changes Summary</h3>
          <p class="text-body-2 text-medium-emphasis mb-3">
            Please review the changes below before confirming the update.
          </p>
        </div>

        <!-- Diff Viewer -->
        <div class="mb-4">
          <DiffViewer :differences="workerDifferences" />
        </div>
      </template>
    </ConfirmDialog>
  </v-container>
</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DiffViewer from '@/components/DiffViewer.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import ResourceBadge from '@/components/ResourceBadge.vue'
import SwitchButton from '@/components/SwitchButton.vue'
import TaskLink from '@/components/TaskLink.vue'
import type { Config } from '@/config'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useContextStore } from '@/stores/context'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useWorkersStore } from '@/stores/workers'
import type { WorkerMetrics } from '@/types/workers'
import { fuzzyFilter } from '@/utils/cmp'
import { formattedBytesSize } from '@/utils/format'
import diff from 'deep-diff'
import { computed, inject, onMounted, ref, watch } from 'vue'
import { useDisplay } from 'vuetify'

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

const authStore = useAuthStore()
const workersStore = useWorkersStore()
const contextStore = useContextStore()
const loadingStore = useLoadingStore()
const notificationStore = useNotificationStore()
const { smAndDown } = useDisplay()

const error = ref<string | null>(null)
const worker = ref<WorkerMetrics | null>(null)
const contexts = ref<string[]>([])
const currentTab = ref(props.selectedTab)
const saving = ref(false)

const editContexts = ref<Array<{ name: string; ip: string | null }>>([])

// Confirmation dialog state
const showConfirmDialog = ref(false)

const canUpdateWorkers = computed(() => authStore.hasPermission('workers', 'update'))

const runningTasksHeaders = [
  { title: 'Schedule', value: 'schedule_name' },
  { title: 'Resources', value: 'resources' },
  { title: 'Task', value: 'task' },
]

const hasChanges = computed(() => {
  if (!worker.value) return false

  const originalContexts = worker.value.contexts || {}
  const editedContexts = convertToContextRecord(editContexts.value)

  const changes = diff(
    { contexts: originalContexts, admin_disabled: worker.value.admin_disabled },
    { contexts: editedContexts, admin_disabled: adminDisabled.value },
  )
  return changes && changes.length > 0
})

// Generate differences for the diff viewer
const workerDifferences = computed(() => {
  if (!worker.value) return undefined

  const originalContexts = worker.value.contexts || {}
  const editedContexts = convertToContextRecord(editContexts.value)

  return diff(
    { contexts: originalContexts, admin_disabled: worker.value.admin_disabled },
    { contexts: editedContexts, admin_disabled: adminDisabled.value },
  )
})

// Check for duplicate context names
const hasDuplicateContextNames = computed(() => {
  const names = editContexts.value
    .map((context) => context.name?.trim())
    .filter((name) => name !== '')
  return names.length !== new Set(names).size
})

// Check if add context button should be disabled
const canAddContext = computed(() => {
  return !hasDuplicateContextNames.value
})

const addContext = () => {
  editContexts.value.push({ name: '', ip: null })
}

const removeContext = (index: number) => {
  editContexts.value.splice(index, 1)
}

const adminDisabled = ref(false)

const workerEnabled = computed(() => !adminDisabled.value)

const updateWorkerEnabled = (value: boolean) => {
  adminDisabled.value = !value
}

const convertToContextRecord = (
  contexts: Array<{ name: string; ip: string | null }>,
): Record<string, string | null> => {
  const record: Record<string, string | null> = {}
  contexts.forEach((context) => {
    if (context.name.trim()) {
      record[context.name.trim()] = context.ip?.trim() || null
    }
  })
  return record
}

const convertFromContextRecord = (
  contexts: Record<string, string | null>,
): Array<{ name: string; ip: string | null }> => {
  const entries = Object.entries(contexts)
  if (entries.length === 0) {
    return []
  }
  return entries.map(([name, ip]) => ({ name, ip }))
}

const isDuplicateContextName = (name: string, currentIndex: number): boolean => {
  if (!name.trim()) return false

  return editContexts.value.some(
    (context, index) => index !== currentIndex && context.name.trim() === name.trim(),
  )
}

const workerName = computed(() => props.workerName)

const usageCpu = computed(
  () => `${worker.value?.current_usage.cpu ?? 0}/${worker.value?.resources.cpu ?? 0}`,
)
const usageMemory = computed(
  () =>
    `${formattedBytesSize(worker.value?.current_usage.memory ?? 0)}/${formattedBytesSize(
      worker.value?.resources.memory ?? 0,
    )}`,
)
const usageDisk = computed(
  () =>
    `${formattedBytesSize(worker.value?.current_usage.disk ?? 0)}/${formattedBytesSize(
      worker.value?.resources.disk ?? 0,
    )}`,
)

function pctColor(pct: number): string {
  if (pct >= 90) return 'error'
  if (pct >= 70) return 'warning'
  return 'success'
}

const percentCpu = computed(() => {
  const max = worker.value?.resources.cpu ?? 0
  const cur = worker.value?.current_usage.cpu ?? 0
  return max > 0 ? Math.min(100, Math.round((cur * 100) / max)) : 0
})
const percentMemory = computed(() => {
  const max = worker.value?.resources.memory ?? 0
  const cur = worker.value?.current_usage.memory ?? 0
  return max > 0 ? Math.min(100, Math.round((cur * 100) / max)) : 0
})
const percentDisk = computed(() => {
  const max = worker.value?.resources.disk ?? 0
  const cur = worker.value?.current_usage.disk ?? 0
  return max > 0 ? Math.min(100, Math.round((cur * 100) / max)) : 0
})
const colorCpu = computed(() => pctColor(percentCpu.value))
const colorMemory = computed(() => pctColor(percentMemory.value))
const colorDisk = computed(() => pctColor(percentDisk.value))

async function refreshData() {
  loadingStore.startLoading('Fetching worker...')
  const res = await workersStore.fetchWorkerMetrics(workerName.value)
  if (res) {
    worker.value = res
    editContexts.value = convertFromContextRecord(res.contexts || {})
    adminDisabled.value = res.admin_disabled
    error.value = null
  } else {
    error.value = workersStore.errors[0] || 'Failed to fetch worker'
    notificationStore.showError(error.value)
  }
  loadingStore.stopLoading()
}

const save = () => {
  if (!canSubmit.value) return

  // Show confirmation dialog instead of directly submitting
  showConfirmDialog.value = true
}

const handleConfirmUpdate = async () => {
  if (saving.value) return

  saving.value = true

  try {
    // Convert form data to the expected schema
    const contextsPayload = convertToContextRecord(editContexts.value)

    const ok = await workersStore.updateWorker(workerName.value, {
      contexts: contextsPayload,
      admin_disabled: adminDisabled.value,
    })

    if (ok) {
      notificationStore.showSuccess('Worker updated')
      await refreshData()
      contexts.value = (await contextStore.fetchContexts()) || []
      currentTab.value = 'details'
    } else {
      for (const error of workersStore.errors) {
        notificationStore.showError(error)
      }
    }
  } finally {
    saving.value = false
    showConfirmDialog.value = false
  }
}

const handleCancelUpdate = () => {
  showConfirmDialog.value = false
}

const canSubmit = computed(() => {
  return hasChanges.value && !hasDuplicateContextNames.value
})

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

// Redirect to details tab if no permission to edit
watch(
  () => currentTab.value,
  (newTab) => {
    if (newTab === 'edit' && !canUpdateWorkers.value) {
      currentTab.value = 'details'
    }
  },
  { immediate: true },
)
</script>
