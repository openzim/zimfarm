<!-- Full-featured button to execute recipe/task action by its name

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
    <!-- Request Button -->
    <v-btn
      v-show="canRequest"
      color="primary"
      variant="elevated"
      size="small"
      class="mr-2"
      :loading="working"
      :disabled="working"
      @click="emit('request-task')"
    >
      <v-tooltip activator="parent" location="top">Request with default options</v-tooltip>
      <v-icon size="small" class="mr-1">mdi-rocket-launch</v-icon>
      Request
    </v-btn>

    <!-- Custom Request Button -->
    <v-btn
      v-show="canRequest"
      color="primary"
      variant="outlined"
      size="small"
      class="mr-2"
      :loading="working"
      :disabled="working"
      @click="emit('custom-request-task')"
    >
      <v-tooltip activator="parent" location="top">Choose worker, priority and flags</v-tooltip>
      <v-icon size="small" class="mr-1">mdi-tune-variant</v-icon>
      Custom request
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
import { useAuthStore } from '@/stores/auth'
import type { RequestedTaskLight } from '@/types/requestedTasks'
import type { TaskLight } from '@/types/tasks'
import { computed } from 'vue'

// Props
interface Props {
  enabled: boolean
  ready: boolean
  task: TaskLight | null
  requestedTask: RequestedTaskLight | null
  workingText: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'request-task'): void
  (e: 'custom-request-task'): void
  (e: 'fire-existing-task'): void
  (e: 'cancel-task'): void
  (e: 'unrequest-task'): void
}>()

// Stores
const authStore = useAuthStore()

// Computed properties
const taskId = computed(() => (props.task ? props.task.id : null))
const visible = computed(
  () => props.ready && (canRequestTasks.value || canUnRequestTasks.value || canCancelTasks.value),
)
const working = computed(() => Boolean(props.workingText))
const isRunning = computed(() => (taskId.value !== null ? Boolean(taskId.value) : null))
const isRequested = computed(() =>
  requestedTaskId.value === null ? null : Boolean(requestedTaskId.value),
)
const canRequest = computed(
  () => props.enabled && !working.value && !isRunning.value && !isRequested.value,
)
const canFireExisting = computed(() => !working.value && isRequested.value)
const canCancel = computed(() => !working.value && isRunning.value && taskId.value)
const canUnRequest = computed(() => !working.value && isRequested.value)
const requestedTaskId = computed(() => props.requestedTask?.id || null)

// Permission computed properties
const canRequestTasks = computed(() => authStore.hasPermission('requested_tasks', 'create'))
const canUnRequestTasks = computed(() => authStore.hasPermission('requested_tasks', 'delete'))
const canCancelTasks = computed(() => authStore.hasPermission('tasks', 'cancel'))
</script>

<style scoped>
/* Custom styles if needed */
</style>
