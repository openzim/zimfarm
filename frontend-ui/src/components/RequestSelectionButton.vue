<template>
  <!-- Worker Selection Dropdown -->
  <WorkerSelector
    v-model="selectedWorker"
    :workers="workers"
    :visible="!isRequesting"
    v-if="props.count > 0"
  />

  <!-- Request Button (Normal Priority) -->
  <v-btn
    color="primary"
    variant="elevated"
    size="small"
    :loading="isRequesting"
    :disabled="isDisabled"
    @click="promptRequest(false)"
  >
    <v-tooltip activator="parent" location="top">Request with normal priority</v-tooltip>
    <v-icon size="small" class="mr-1">mdi-plus</v-icon>
    {{
      isRequesting ? requestingText : `Request ${count} selected recipe${count !== 1 ? 's' : ''}`
    }}
  </v-btn>

  <!-- Fire Button (High Priority) -->
  <v-btn
    v-if="!isRequesting"
    color="warning"
    variant="elevated"
    size="small"
    :disabled="isDisabled"
    @click="promptRequest(true)"
  >
    <v-tooltip activator="parent" location="top">Request with high priority</v-tooltip>
    <v-icon size="small" class="mr-1">mdi-priority-high</v-icon>
    {{
      isRequesting ? requestingText : `Request ${count} selected recipe${count !== 1 ? 's' : ''}`
    }}
  </v-btn>

  <ConfirmDialog
    v-model="showConfirm"
    title="Confirm Request"
    :message="confirmMessage"
    confirm-text="Proceed"
    cancel-text="Abort"
    confirm-color="primary"
    icon="mdi-help-circle"
    icon-color="primary"
    @confirm="handleConfirm"
    @cancel="handleCancel"
  />
</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import WorkerSelector from '@/components/WorkerSelector.vue'
import constants from '@/constants'
import type { Worker } from '@/types/workers'
import { computed, ref } from 'vue'

// Props
interface Props {
  requestingText: string | null
  canRequestTasks: boolean
  count: number
  workers: Worker[]
}

const props = defineProps<Props>()

// Define emits
const emit = defineEmits<{
  'request-tasks': [workerName: string | null, highPriority: boolean]
}>()

// Reactive state
const selectedWorker = ref<string | null>(null)
const showConfirm = ref(false)
const pendingPriority = ref(false)

// Computed properties
const isDisabled = computed(
  () => props.count < 1 || props.count > constants.MAX_RECIPES_IN_SELECTION_REQUEST,
)
const isRequesting = computed(() => Boolean(props.requestingText))

const confirmMessage = computed(() => {
  const priorityText = pendingPriority.value ? 'high priority' : 'normal priority'
  const workerText = selectedWorker.value ? ` to worker ${selectedWorker.value}` : ''
  return `Are you sure you want to request ${props.count} recipe${props.count !== 1 ? 's' : ''}${workerText} with ${priorityText}?`
})

const promptRequest = (highPriority: boolean) => {
  pendingPriority.value = highPriority
  showConfirm.value = true
}

const handleConfirm = () => {
  emit('request-tasks', selectedWorker.value, pendingPriority.value)
  selectedWorker.value = null
  showConfirm.value = false
}

const handleCancel = () => {
  showConfirm.value = false
}
</script>
