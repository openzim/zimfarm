<template>
  <div>
    <v-menu v-if="visible" location="bottom end" offset-y>
      <template v-slot:activator="{ props }">
        <v-btn v-bind="props" variant="outlined" color="primary" size="small" class="mr-2">
          <v-icon size="small" class="mr-1">mdi-server</v-icon>
          {{ displayWorker }}
        </v-btn>
      </template>

      <v-list max-height="250" class="overflow-y-auto">
        <v-list-item
          v-for="worker in allWorkers"
          :key="worker.name"
          @click="handleWorkerChange(worker.name)"
          :color="worker.status === 'online' ? 'success' : 'secondary'"
        >
          <v-list-item-title :class="{ 'text-success': worker.status === 'online' }">
            {{ worker.name }}
          </v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>
  </div>
</template>

<script setup lang="ts">
import type { Worker } from '@/types/workers'
import { computed } from 'vue'

// Props
interface Props {
  workers: Worker[]
  modelValue: string | null
  visible?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  visible: true,
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: string | null]
}>()

// Constants
const ANY_WORKER_NAME = 'Any'

// Computed properties
const displayWorker = computed(() => props.modelValue || ANY_WORKER_NAME)

const allWorkers = computed(() => [
  { name: ANY_WORKER_NAME, status: 'offline' as const },
  ...props.workers,
])

// Methods
const handleWorkerChange = (workerName: string) => {
  const cleanedWorker = workerName === ANY_WORKER_NAME ? null : workerName
  emit('update:modelValue', cleanedWorker)
}
</script>

<style scoped>
/* Custom styles if needed */
</style>
