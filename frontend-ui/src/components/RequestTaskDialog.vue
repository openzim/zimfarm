<!-- Dialog to review and fine-tune the parameters used to request a task

  - optionally displays the offliner flags that will be passed to the scraper
  - lets the editor override flags for this request only
  - lets the editor choose the target worker and priority -->
<template>
  <v-dialog
    :model-value="modelValue"
    max-width="800"
    scrollable
    persistent
    @update:model-value="handleDialogUpdate"
  >
    <v-card>
      <v-card-title class="d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-tune-variant</v-icon>
        <span v-if="recipeName" class="d-flex align-baseline ga-2">
          <span class="font-weight-regular text-medium-emphasis">Request</span>
          <code class="font-weight-bold">{{ recipeName }}</code>
        </span>
        <span v-else class="d-flex align-baseline ga-2">
          <span class="font-weight-regular text-medium-emphasis">Request</span>
          <span class="font-weight-bold">
            {{ count }} selected recipe{{ count !== 1 ? 's' : '' }}
          </span>
        </span>
      </v-card-title>

      <v-card-subtitle>
        {{ selectedWorker ? `Target worker: ${selectedWorker}` : 'Any available worker' }}
        ·
        {{ priorityLabel }}
      </v-card-subtitle>

      <v-card-text>
        <v-row dense class="mb-3">
          <v-col cols="12" sm="6">
            <v-select
              v-model="selectedWorker"
              :items="workerItems"
              label="Worker"
              placeholder="Any available worker"
              clearable
              density="compact"
              variant="outlined"
              hide-details
            />
          </v-col>
          <v-col cols="12" sm="6">
            <v-select
              v-model="priority"
              :items="priorityItems"
              label="Priority"
              hint="0 = default; higher values are scheduled first (5 = high, 10 = highest)"
              persistent-hint
              density="compact"
              variant="outlined"
            />
          </v-col>
        </v-row>

        <template v-if="showFlags">
          <v-alert type="info" variant="tonal" density="compact" class="mb-4">
            These are the offliner flags that will be used for this task. Changes only apply to this
            request and are not saved on the recipe.
          </v-alert>

          <div v-if="filteredFields.length === 0" class="text-medium-emphasis pa-4 text-center">
            <v-icon size="large" class="mb-2">mdi-filter-off-outline</v-icon>
            <div>No flags to display.</div>
          </div>

          <div v-else>
            <v-row v-for="field in filteredFields" :key="field.dataKey" no-gutters class="py-2">
              <v-col cols="12">
                <div v-if="isChanged(field.dataKey)" class="d-flex justify-end mb-1">
                  <v-chip size="x-small" color="warning" variant="tonal">modified</v-chip>
                </div>

                <OfflinerFlagInput
                  :field="field"
                  :model-value="localFlags[field.dataKey]"
                  :offliner="flags?.offliner_id"
                  :label="field.label + (field.required ? ' *' : '')"
                  @update:model-value="(value) => setFlagValue(field.dataKey, value)"
                />
              </v-col>

              <v-divider class="mt-1" />
            </v-row>
          </div>
        </template>
      </v-card-text>

      <v-card-actions class="pa-4">
        <v-btn v-if="showFlags" variant="outlined" :disabled="!hasChanges" @click="resetFlags">
          Reset
        </v-btn>
        <v-spacer />
        <v-btn variant="outlined" @click="cancel">Cancel</v-btn>
        <v-btn :color="priority > 0 ? 'warning' : 'primary'" variant="elevated" @click="confirm">
          <v-icon size="small" class="mr-1">
            {{ priority > 0 ? 'mdi-priority-high' : 'mdi-rocket-launch' }}
          </v-icon>
          Request
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import OfflinerFlagInput from '@/components/OfflinerFlagInput.vue'
import type { OfflinerDefinition } from '@/types/offliner'
import type { OfflinerFlags } from '@/types/recipe'
import type { RequestTaskOptions } from '@/types/requestedTasks'
import type { Worker } from '@/types/workers'
import type { FlagField } from '@/utils/offlinerFlags'
import {
  buildFlagFields,
  buildFlagVisibilityContext,
  isFlagFieldVisible,
  isFlagValueSet,
  normalizeFlagValue,
} from '@/utils/offlinerFlags'
import { computed, ref, watch } from 'vue'

interface Props {
  modelValue: boolean
  recipeName?: string
  flags?: OfflinerFlags
  flagsDefinition?: OfflinerDefinition[]
  workers?: Worker[]
  count?: number
}

const props = withDefaults(defineProps<Props>(), {
  recipeName: undefined,
  flags: undefined,
  flagsDefinition: () => [],
  workers: () => [],
  count: 1,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  confirm: [payload: RequestTaskOptions]
}>()

const selectedWorker = ref<string | null>(null)
const priority = ref(0)
const localFlags = ref<Record<string, unknown>>({})
const originalFlags = ref<Record<string, unknown>>({})

const workerItems = computed(() =>
  props.workers.map((worker) => ({
    title: worker.name,
    value: worker.name,
  })),
)

const priorityItems = computed(() =>
  Array.from({ length: 11 }, (_, priority) => ({
    title: String(priority),
    value: priority,
  })),
)

const priorityLabel = computed(() => `Priority ${priority.value}`)

const showFlags = computed(() => Boolean(props.flags) && props.flagsDefinition.length > 0)

const clone = (flags: Record<string, unknown>): Record<string, unknown> => {
  const copy: Record<string, unknown> = JSON.parse(JSON.stringify(flags ?? {}))
  delete copy.offliner_id
  return copy
}

const resetFlags = () => {
  localFlags.value = clone(originalFlags.value)
}

watch(
  () => props.modelValue,
  (isOpen) => {
    if (isOpen) {
      selectedWorker.value = null
      priority.value = 0
      originalFlags.value = clone(props.flags ?? {})
      localFlags.value = clone(props.flags ?? {})
    }
  },
  { immediate: true },
)

const fields = computed<FlagField[]>(() => buildFlagFields(props.flagsDefinition))

const flagVisibility = computed(() => buildFlagVisibilityContext(props.flagsDefinition))

const isFieldVisible = (field: FlagField): boolean =>
  isFlagFieldVisible(field, flagVisibility.value, localFlags.value)

const filteredFields = computed(() => {
  return fields.value.filter(
    (field) =>
      isFieldVisible(field) && (field.required || isFlagValueSet(localFlags.value[field.dataKey])),
  )
})

const setFlagValue = (key: string, value: unknown) => {
  localFlags.value[key] = value
}

const flagsEqual = (first: unknown, second: unknown): boolean =>
  JSON.stringify(normalizeFlagValue(first)) === JSON.stringify(normalizeFlagValue(second))

const isChanged = (key: string): boolean =>
  !flagsEqual(localFlags.value[key], originalFlags.value[key])

const hasChanges = computed(() => fields.value.some((field) => isChanged(field.dataKey)))

const changedFlags = (): Record<string, unknown> | null => {
  const overrides: Record<string, unknown> = {}
  const keys = new Set([...Object.keys(originalFlags.value), ...Object.keys(localFlags.value)])

  for (const key of keys) {
    if (key === 'offliner_id') continue
    if (!flagsEqual(localFlags.value[key], originalFlags.value[key])) {
      overrides[key] = normalizeFlagValue(localFlags.value[key])
    }
  }

  return Object.keys(overrides).length > 0 ? overrides : null
}

const confirm = () => {
  emit('confirm', {
    worker: selectedWorker.value,
    priority: priority.value > 0 ? priority.value : null,
    flags: showFlags.value ? changedFlags() : null,
  })
}

const cancel = () => {
  emit('update:modelValue', false)
}

const handleDialogUpdate = (value: boolean) => {
  emit('update:modelValue', value)
}
</script>
