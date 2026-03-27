<template>
  <v-dialog v-model="isOpen" max-width="800">
    <v-card>
      <v-card-title class="d-flex align-center bg-primary text-white text-subtitle-1">
        <v-icon class="mr-2">mdi-stethoscope</v-icon>
        <span v-if="!isDone && task">
          Running diagnostics for task <strong>{{ shortId }}</strong>
          <v-progress-circular indeterminate size="20" width="2" class="ml-3"></v-progress-circular>
        </span>
        <span v-else-if="isDone && task">
          Diagnostics complete for task <strong>{{ shortId }}</strong>
        </span>
        <span v-else>Diagnose Task</span>
        <v-spacer></v-spacer>
        <v-btn icon="mdi-close" variant="text" @click="close"></v-btn>
      </v-card-title>
      <v-divider></v-divider>

      <v-card-text class="pa-4 bg-grey-lighten-4" style="max-height: 600px; overflow-y: auto">
        <div v-if="!task" class="text-center pa-4 text-grey">No task selected.</div>
        <div v-else>
          <v-data-table
            :headers="headers"
            :items="results"
            :items-per-page="-1"
            hide-default-footer
            class="elevation-1"
            density="compact"
          >
            <template #[`item.reasons`]="{ item }">
              <div v-if="item.status === 'checking'" class="d-flex align-center text-primary py-2">
                <v-progress-circular
                  indeterminate
                  size="16"
                  width="2"
                  class="mr-2"
                ></v-progress-circular>
                Checking compatibility...
              </div>

              <div v-else-if="item.status === 'done'" class="py-2">
                <div v-if="item.errors.length > 0" class="text-grey-darken-2">
                  <ul class="pl-4">
                    <li v-for="(err, i) in item.errors" :key="i" class="mb-1">{{ err }}</li>
                  </ul>
                </div>
                <div v-else class="text-error font-weight-bold d-flex align-center">
                  <v-icon color="error" class="mr-1" size="small">mdi-alert</v-icon>
                  Abnormal: Task should be able to start on this worker!
                </div>
              </div>

              <div v-else-if="item.status === 'failed'" class="py-2 text-error">
                Failed to run diagnostics.
              </div>
            </template>
          </v-data-table>
        </div>
      </v-card-text>

      <v-divider></v-divider>
      <v-card-actions class="pa-3 bg-grey-lighten-5">
        <v-spacer></v-spacer>
        <v-btn color="primary" variant="elevated" @click="close" :loading="!isDone && !!task">
          {{ isDone ? 'Close' : 'Diagnosing...' }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useRequestedTasksStore } from '@/stores/requestedTasks'
import { useWorkersStore } from '@/stores/workers'
import type { RequestedTaskLight } from '@/types/requestedTasks'

const props = defineProps<{
  modelValue: boolean
  task: RequestedTaskLight | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const requestedTasksStore = useRequestedTasksStore()
const workersStore = useWorkersStore()

const isOpen = ref(props.modelValue)
let activeDiagnosisId = 0

const shortId = computed(() => {
  return props.task?.id ? props.task.id.substring(0, 5) : ''
})

watch(
  () => props.modelValue,
  async (val) => {
    isOpen.value = val
    if (val && props.task) {
      activeDiagnosisId++
      await startDiagnosis(props.task, activeDiagnosisId)
    } else if (!val) {
      activeDiagnosisId++ // Cancel any ongoing diagnosis when closed
    }
  },
)

watch(isOpen, (val) => {
  emit('update:modelValue', val)
})

interface DiagnosisResult {
  worker: string
  status: 'checking' | 'done' | 'failed'
  errors: string[]
}

const headers = [
  { title: 'Worker', value: 'worker', width: '25%' },
  { title: 'Reason', value: 'reasons', width: '75%' },
]

const results = ref<DiagnosisResult[]>([])
const isDone = ref(false)

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

const startDiagnosis = async (task: RequestedTaskLight, currentDiagnosisId: number) => {
  results.value = []
  isDone.value = false

  let workersToDiagnose: string[] = []

  if (task.worker_name) {
    workersToDiagnose = [task.worker_name]
  } else {
    let skip = 0
    const limit = 100
    const allWorkers: string[] = []
    while (true) {
      const workersList = await workersStore.fetchWorkers({ limit, skip, hide_offlines: false })
      if (!workersList || workersList.length === 0) break
      allWorkers.push(...workersList.map((w) => w.name))
      if (workersList.length < limit) break
      skip += limit
    }
    workersToDiagnose = allWorkers
  }

  for (let i = 0; i < workersToDiagnose.length; i++) {
    if (activeDiagnosisId !== currentDiagnosisId) return // Abort if dialog was closed or restarted

    const workerName = workersToDiagnose[i]
    const res: DiagnosisResult = {
      worker: workerName,
      status: 'checking',
      errors: [],
    }
    results.value.push(res)

    try {
      const errors = await requestedTasksStore.diagnoseRequestedTask(task.id, workerName)

      if (activeDiagnosisId !== currentDiagnosisId) return

      let finalErrors: string[] = []
      if (errors !== null) {
        finalErrors = Array.isArray(errors) ? errors : [errors as unknown as string]
      }
      results.value[i] = { ...res, status: 'done', errors: finalErrors }
    } catch (e) {
      console.error(e)
      if (activeDiagnosisId !== currentDiagnosisId) return
      results.value[i] = { ...res, status: 'failed' }
    }

    // Sleep for 1 second to avoid hitting the API frequently
    if (i < workersToDiagnose.length - 1) {
      await sleep(1000)
    }
  }

  if (activeDiagnosisId === currentDiagnosisId) {
    isDone.value = true
  }
}

const close = () => {
  isOpen.value = false
}
</script>
