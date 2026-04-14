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

                <v-divider class="my-3" />

                <div class="text-subtitle-2 mb-2">
                  <v-icon size="small" class="mr-1">mdi-docker</v-icon>
                  Docker Image
                  <v-chip
                    v-if="worker.docker_image"
                    :color="isImageOutdated ? 'warning' : 'success'"
                    size="x-small"
                    variant="tonal"
                    class="ml-2"
                    :prepend-icon="isImageOutdated ? 'mdi-alert' : 'mdi-check-circle'"
                  >
                  </v-chip>
                </div>

                <!-- Current image -->
                <div class="text-caption text-medium-emphasis mb-1">Current</div>
                <div v-if="worker.docker_image" class="text-body-2">
                  <div class="mb-1 d-flex align-center ga-1">
                    <span class="text-medium-emphasis">ID:</span>
                    <code class="text-break">{{ worker.docker_image.hash?.substring(7, 19) }}</code>
                  </div>
                  <div class="text-caption text-medium-emphasis">
                    Built {{ fromNow(worker.docker_image.created_at) }}
                  </div>
                  <div v-if="isImageOutdated" class="text-caption text-warning mt-1">
                    <v-icon size="x-small" color="warning">mdi-clock-alert-outline</v-icon>
                    {{ imageAge }} behind latest
                  </div>
                </div>
                <div v-else class="text-body-2 text-medium-emphasis">N/A</div>

                <!-- Latest image -->
                <template v-if="latestImage">
                  <v-divider class="my-2" />
                  <div class="text-caption text-medium-emphasis mb-1">Latest</div>
                  <div class="text-body-2">
                    <div class="mb-1 d-flex align-center ga-1">
                      <span class="text-medium-emphasis">ID:</span>
                      <code class="text-break">{{ latestImage.hash?.substring(7, 19) }}</code>
                    </div>
                    <div class="text-caption text-medium-emphasis">
                      Released {{ fromNow(latestImage.created_at) }}
                    </div>
                  </div>
                </template>
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

                  <template #[`item.recipe_name`]="{ item }">
                    <span v-if="item.recipe_name === null">N/A</span>
                    <router-link
                      v-else
                      :to="{
                        name: 'recipe-detail',
                        params: { recipeName: item.recipe_name },
                      }"
                    >
                      {{ item.recipe_name }}
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

              <!-- SSH Keys Section -->
              <v-sheet rounded border class="pa-3 mt-4">
                <div class="text-subtitle-2 mb-2 d-flex align-center">
                  <v-icon size="small" class="mr-1">mdi-key</v-icon>
                  SSH Keys
                </div>
                <div
                  v-if="!worker.ssh_keys || !worker.ssh_keys.length"
                  class="text-body-2 text-medium-emphasis"
                >
                  No SSH keys added
                </div>
                <template v-else>
                  <!-- Header (visible on md and up) -->
                  <div class="d-none d-md-flex font-weight-medium text-body-2 pb-2 mb-2 border-b">
                    <div class="flex-grow-1" style="flex-basis: 30%">SSH Key</div>
                    <div class="flex-grow-1" style="flex-basis: 50%">Fingerprint</div>
                    <div v-if="canManageSshKeys" style="flex-basis: 20%; min-width: 120px">
                      Actions
                    </div>
                  </div>
                  <!-- SSH Key Items -->
                  <div
                    v-for="sshKey in worker.ssh_keys"
                    :key="sshKey.name"
                    class="d-flex flex-column flex-md-row align-start align-md-center py-3 border-b"
                  >
                    <div class="flex-grow-1 mb-2 mb-md-0" style="flex-basis: 30%">
                      <div class="text-caption text-medium-emphasis d-md-none">SSH Key</div>
                      <div class="text-body-2">{{ sshKey.name }}</div>
                    </div>
                    <div class="flex-grow-1 mb-2 mb-md-0" style="flex-basis: 50%">
                      <div class="text-caption text-medium-emphasis d-md-none">Fingerprint</div>
                      <code class="text-body-2">{{ sshKey.fingerprint }}</code>
                    </div>
                    <div
                      v-if="canManageSshKeys"
                      class="mt-2 mt-md-0"
                      style="flex-basis: 20%; min-width: 120px"
                    >
                      <v-btn
                        color="error"
                        size="small"
                        variant="outlined"
                        @click="confirmDeleteSshKey(sshKey)"
                      >
                        <v-icon size="small" class="mr-1">mdi-delete</v-icon>
                        Delete
                      </v-btn>
                    </div>
                  </div>
                </template>
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

          <!-- Add SSH Key -->
          <v-card v-if="canManageSshKeys" class="mt-4">
            <v-card-title class="text-subtitle-1">
              <v-icon class="mr-2">mdi-key-plus</v-icon>
              Add SSH Key
            </v-card-title>
            <v-card-text>
              <v-form @submit.prevent="addSshKey">
                <v-row no-gutters>
                  <v-col cols="12">
                    <SshKeyInput v-model="keyFormData" />
                  </v-col>
                  <v-col cols="12" sm="4" class="ml-auto">
                    <v-btn
                      type="submit"
                      color="primary"
                      variant="elevated"
                      :disabled="!keyPayload.key"
                      block
                    >
                      Add SSH Key
                    </v-btn>
                  </v-col>
                </v-row>
              </v-form>
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

    <!-- SSH Key Delete Confirmation Dialog -->
    <ConfirmDialog
      v-model="showSshKeyConfirmDialog"
      :title="sshKeyConfirmDialogTitle"
      :message="sshKeyConfirmDialogMessage"
      confirm-text="DELETE"
      cancel-text="CANCEL"
      confirm-color="error"
      icon="mdi-delete"
      icon-color="error"
      @confirm="handleConfirmDeleteSshKey"
      @cancel="handleCancelDeleteSshKey"
    />
  </v-container>
</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DiffViewer from '@/components/DiffViewer.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import ResourceBadge from '@/components/ResourceBadge.vue'
import SshKeyInput from '@/components/SshKeyInput.vue'
import SwitchButton from '@/components/SwitchButton.vue'
import TaskLink from '@/components/TaskLink.vue'
import type { Config } from '@/config'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useContextStore } from '@/stores/context'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useWorkersStore } from '@/stores/workers'
import type { DockerImageVersion, WorkerMetrics, SshKeyRead } from '@/types/workers'
import { fuzzyFilter } from '@/utils/cmp'
import { formattedBytesSize, formatDurationBetween, fromNow } from '@/utils/format'
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
const latestImage = ref<DockerImageVersion | null>(null)
const contexts = ref<string[]>([])
const currentTab = ref(props.selectedTab)
const saving = ref(false)

const editContexts = ref<Array<{ name: string; ip: string | null }>>([])

// Confirmation dialog state
const showConfirmDialog = ref(false)

const canUpdateWorkers = computed(() => authStore.hasPermission('workers', 'update'))

const isImageOutdated = computed(() => {
  if (!worker.value?.docker_image || !latestImage.value) return false
  return worker.value.docker_image.hash !== latestImage.value.hash
})

const imageAge = computed(() => {
  if (!worker.value?.docker_image?.created_at || !latestImage.value?.created_at) return ''
  return formatDurationBetween(worker.value.docker_image.created_at, latestImage.value.created_at)
})

const runningTasksHeaders = [
  { title: 'Recipe', value: 'recipe_name' },
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
  const [res, latest] = await Promise.all([
    workersStore.fetchWorkerMetrics(workerName.value),
    workersStore.fetchLatestWorkerImage(),
  ])
  if (res) {
    worker.value = res
    editContexts.value = convertFromContextRecord(res.contexts || {})
    adminDisabled.value = res.admin_disabled
    error.value = null
  } else {
    error.value = workersStore.errors[0] || 'Failed to fetch worker'
    notificationStore.showError(error.value)
  }
  latestImage.value = latest
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

const canManageSshKeys = computed(() => authStore.hasPermission('workers', 'ssh_keys'))

const showSshKeyConfirmDialog = ref(false)
const sshKeyConfirmDialogTitle = ref('')
const sshKeyConfirmDialogMessage = ref('')
let pendingSshKey: SshKeyRead | null = null

// Add-key form state
const keyFormData = ref({ name: '', key: '' })
const keyPayload = computed(() => {
  if (!keyFormData.value.name.length || !keyFormData.value.key.length) {
    return { key: '' }
  }
  return { key: keyFormData.value.key }
})

const confirmDeleteSshKey = (sshKey: SshKeyRead) => {
  pendingSshKey = sshKey
  sshKeyConfirmDialogTitle.value = 'Delete SSH Key'
  sshKeyConfirmDialogMessage.value = `Are you sure you want to delete SSH Key "${sshKey.name}"?`
  showSshKeyConfirmDialog.value = true
}

const handleConfirmDeleteSshKey = async () => {
  if (pendingSshKey) {
    await deleteSshKeyAction(pendingSshKey)
    pendingSshKey = null
  }
}

const handleCancelDeleteSshKey = () => {
  pendingSshKey = null
}

const deleteSshKeyAction = async (sshKey: SshKeyRead) => {
  loadingStore.startLoading('Deleting key...')
  try {
    const ok = await workersStore.deleteSshKey(workerName.value, sshKey.fingerprint)
    if (ok) {
      notificationStore.showSuccess(`Key Removed! SSH Key "${sshKey.name}" has been removed.`)
      await refreshData()
    } else {
      for (const err of workersStore.errors) {
        notificationStore.showError(err)
      }
    }
  } catch (err) {
    console.error('Error deleting SSH key:', err)
    notificationStore.showError('Failed to delete SSH key')
  } finally {
    loadingStore.stopLoading()
  }
}

const addSshKey = async () => {
  if (!keyPayload.value.key) return
  loadingStore.startLoading('Adding key...')
  const ok = await workersStore.addSshKey(workerName.value, keyPayload.value)
  if (ok) {
    notificationStore.showSuccess(`Key added! SSH Key has been added.`)
    keyFormData.value = { name: '', key: '' }
    await refreshData()
  } else {
    for (const err of workersStore.errors) {
      notificationStore.showError(err)
    }
  }
  loadingStore.stopLoading()
}
</script>
