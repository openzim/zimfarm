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
    class="mr-2"
    :loading="isRequesting"
    :disabled="isDisabled"
    @click="handleRequest(selectedWorker, false)"
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
    @click="handleRequest(selectedWorker, true)"
  >
    <v-tooltip activator="parent" location="top">Request with high priority</v-tooltip>
    <v-icon size="small" class="mr-1">mdi-priority-high</v-icon>
    {{
      isRequesting ? requestingText : `Request ${count} selected recipe${count !== 1 ? 's' : ''}`
    }}
  </v-btn>
</template>

<script setup lang="ts">
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

// Computed properties
const isDisabled = computed(
  () => props.count < 1 || props.count > constants.MAX_RECIPES_IN_SELECTION_REQUEST,
)
const isRequesting = computed(() => Boolean(props.requestingText))

const handleRequest = (workerName: string | null, highPriority: boolean) => {
  emit('request-tasks', workerName, highPriority)
  selectedWorker.value = null
}
</script>
