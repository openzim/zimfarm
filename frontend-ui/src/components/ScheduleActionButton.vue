<!-- Full-featured button to execute schedule/task action by its name

  - request a task
  - unrequest a task
  - cancel a task
  - fire a task
    - by creating it
    - by setting its priority
  - disabled if not signed-in
  - displays a spinner on click
  - calls the API in the background
  - displays result as an AlertFeedback -->

<template>
  <div v-if="visible" class="d-flex justify-end">
    <!-- Worker Selection Dropdown -->
    <WorkerSelector
      v-if="canSelectWorker"
      v-model="selectedWorker"
      :workers="workers"
      :visible="canSelectWorker"
    />

    <!-- Request Button -->
    <v-btn
      v-show="canRequest"
      color="primary"
      variant="elevated"
      size="small"
      class="mr-2"
      :loading="working"
      :disabled="working"
      @click="emit('request-task', selectedWorker)"
    >
      <v-tooltip activator="parent" location="top"> Request with normal priority </v-tooltip>
      <v-icon size="small" class="mr-1">mdi-plus-circle</v-icon>
      Request
    </v-btn>

    <!-- Un-request Button -->
    <v-btn
      v-show="canUnRequest"
      color="secondary"
      variant="outlined"
      size="small"
      class="mr-2"
      :loading="working"
      :disabled="working"
      @click="emit('unrequest-task')"
    >
      <v-icon size="small" class="mr-1">mdi-delete</v-icon>
      Un-request
    </v-btn>

    <!-- Cancel Button -->
    <v-btn
      v-show="canCancelTasks"
      v-if="canCancel"
      color="error"
      variant="elevated"
      size="small"
      class="mr-2"
      :loading="working"
      :disabled="working"
      @click="emit('cancel-task')"
    >
      <v-icon size="small" class="mr-1">mdi-stop-circle</v-icon>
      Cancel
    </v-btn>

    <!-- Fire Button (High Priority Request) -->
    <v-btn
      v-show="canFire"
      color="warning"
      variant="elevated"
      size="small"
      class="mr-2"
      :loading="working"
      :disabled="working"
      @click="emit('request-task', selectedWorker, true)"
    >
      <v-tooltip activator="parent" location="top"> Request with high priority </v-tooltip>
      <v-icon size="small" class="mr-1">mdi-priority-high</v-icon>
      Request
    </v-btn>

    <!-- Prioritize Existing Task Button -->
    <v-btn
      v-show="canFireExisting"
      color="warning"
      variant="outlined"
      size="small"
      class="mr-2"
      :loading="working"
      :disabled="working"
      @click="emit('fire-existing-task')"
    >
      <v-icon size="small" class="mr-1">mdi-fire</v-icon>
      Prioritize
    </v-btn>

    <!-- Loading Button -->
    <v-btn v-if="working" color="secondary" variant="outlined" size="small" disabled>
      <v-icon size="small" class="mr-1" spin>mdi-loading</v-icon>
      {{ workingText }}
    </v-btn>
  </div>
</template>

<script setup lang="ts">
import WorkerSelector from '@/components/WorkerSelector.vue'
import { useAuthStore } from '@/stores/auth'
import type { RequestedTaskLight } from '@/types/requestedTasks'
import type { TaskLight } from '@/types/tasks'
import type { Worker } from '@/types/workers'
import { computed, ref } from 'vue'

// Props
interface Props {
  enabled: boolean
  ready: boolean
  task: TaskLight | null
  requestedTask: RequestedTaskLight | null
  workers: Worker[]
  workingText: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'request-task', workerName: string | null, priority?: boolean): void
  (e: 'fire-existing-task'): void
  (e: 'cancel-task'): void
  (e: 'unrequest-task'): void
}>()

// Stores
const authStore = useAuthStore()

// Reactive data
const selectedWorker = ref<string | null>(null)

// Computed properties
const taskId = computed(() => (props.task ? props.task.id : null))
const visible = computed(
  () => props.ready && (canRequestTasks.value || canUnRequestTasks.value || canCancelTasks.value),
)
const working = computed(() => Boolean(props.workingText))
const isRunning = computed(() => (taskId.value !== null ? Boolean(taskId.value) : null))
const isScheduled = computed(() =>
  requestedTaskId.value === null ? null : Boolean(requestedTaskId.value),
)
const canRequest = computed(
  () => props.enabled && !working.value && !isRunning.value && !isScheduled.value,
)
const canFire = computed(() => !working.value && canRequest.value)
const canFireExisting = computed(() => !working.value && isScheduled.value)
const canCancel = computed(() => !working.value && isRunning.value && taskId.value)
const canUnRequest = computed(() => !working.value && isScheduled.value)
const canSelectWorker = computed(() => canRequest.value || canFire.value)
const requestedTaskId = computed(() => props.requestedTask?.id || null)

// Permission computed properties
const canRequestTasks = computed(() => authStore.hasPermission('requested_tasks', 'create'))
const canUnRequestTasks = computed(() => authStore.hasPermission('requested_tasks', 'delete'))
const canCancelTasks = computed(() => authStore.hasPermission('tasks', 'cancel'))
</script>

<style scoped>
/* Custom styles if needed */
</style>
