<template>
  <v-form @submit.prevent="handleSubmit" v-if="schedule">
    <div class="d-flex flex-column flex-sm-row justify-end ga-2">
      <v-btn
        :disabled="!hasChanges"
        type="submit"
        :color="hasChanges ? 'primary' : 'secondary'"
        variant="elevated"
      >
        Update Offliner details
      </v-btn>
      <v-btn
        type="reset"
        :disabled="!hasChanges"
        :color="hasChanges ? 'dark' : 'secondary'"
        variant="outlined"
        @click="handleReset"
      >
        Reset
      </v-btn>
    </div>

    <v-divider class="my-4" />

    <v-row>
      <v-col cols="9">
        <h2>Content settings</h2>
      </v-col>
      <v-col cols="3" class="text-right">
        <v-btn
          href="https://github.com/openzim/zimfarm/wiki/Recipe-configuration-%E2%80%90-Content-settings"
          target="_blank"
          color="primary"
          variant="outlined"
        >
          Help
        </v-btn>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="4">
        <v-text-field
          v-model="editSchedule.name"
          label="Recipe Name"
          hint="Recipe's identifier."
          placeholder="wikipedia_fr_all"
          required
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editSchedule.language.code"
          :items="languagesOptions"
          label="Language"
          hint="Use API if wanted language not present."
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editSchedule.tags"
          :items="tags"
          label="Tags"
          hint="Recipe tags, not ZIM tags. Use API to create others."
          multiple
          chips
          closable-chips
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editSchedule.category"
          :items="categoriesOptions"
          label="Category"
          density="compact"
          variant="outlined"
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editSchedule.config.warehouse_path"
          :items="warehousePathsOptions"
          label="Warehouse Path"
          hint="Where to upload files. Usually matches category."
          required
          placeholder="Warehouse Path"
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <SwitchButton
          v-model="editSchedule.enabled"
          label="Status"
          density="compact"
          details="Disabled recipes are not scheduled, but can be run manually."
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editSchedule.periodicity"
          :items="periodicityOptions"
          label="Periodicity"
          hint="How often to automatically request recipe"
          required
          placeholder="Periodicity"
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-combobox
          v-model="editSchedule.context"
          :items="contexts"
          label="Context"
          hint="Execute schedule only on workers associated with this context"
          placeholder="Context"
          :clearable="!!editSchedule.context"
          density="compact"
          variant="outlined"
          persistent-hint
          :menu-props="{ maxHeight: '200px' }"
          :custom-filter="(value, query) => fuzzyFilter(value, query, contexts)"
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12">
        <v-textarea
          v-model="editComment"
          label="Comment"
          hint="Optional comment to describe the changes being made"
          placeholder="Describe your changes..."
          density="compact"
          variant="outlined"
          persistent-hint
          auto-grow
        />
      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <v-row>
      <v-col cols="9">
        <h2>Task settings</h2>
      </v-col>
      <v-col cols="3" class="text-right">
        <v-btn
          href="https://github.com/openzim/zimfarm/wiki/Recipe-configuration-%E2%80%90-Task-settings"
          target="_blank"
          color="primary"
          variant="outlined"
        >
          Help
        </v-btn>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="6">
        <v-select
          v-model="editSchedule.config.offliner.offliner_id"
          :items="offlinersOptions"
          label="Offliner"
          hint="The kind of task to be run"
          density="compact"
          variant="outlined"
          @update:model-value="handleOfflinerChange"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="6">
        <v-select
          v-model="editSchedule.config.platform"
          :items="platformsOptions"
          label="Platform"
          hint="The platform targetted by the offliner"
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="4">
        <v-text-field
          v-model="editSchedule.config.image.name"
          label="Image Name"
          hint="Image name without tag (docker_repo/name)"
          placeholder="openzim/mwoffliner"
          required
          density="compact"
          variant="outlined"
          @update:model-value="debouncedImageNameChange"
          @blur="() => handleImageNameBlur(editSchedule.config.image.name)"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editSchedule.config.image.tag"
          :items="imageTagOptions"
          label="Image Tag"
          hint="Set image name first to get existing values"
          required
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <SwitchButton
          v-model="editSchedule.config.monitor"
          details="Attach a monitoring companion to scraper"
          density="compact"
          label="Monitoring"
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="3">
        <v-text-field
          v-model="editSchedule.config.resources.cpu"
          label="CPU"
          hint="Number of CPU shares to use"
          type="number"
          min="1"
          max="100"
          required
          placeholder="3"
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="3">
        <v-select
          v-model="editSchedule.config.resources.memory"
          :items="memoryOptions"
          label="Memory"
          hint="Required memory. Use API for custom value."
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="3">
        <v-select
          v-model="editSchedule.config.resources.disk"
          :items="diskOptions"
          label="Disk"
          hint="Required disk space. Use API for custom value."
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="3">
        <v-select
          v-model="editSchedule.config.resources.shm"
          :items="memoryOptions"
          label="RAM fs"
          hint="Amount of RAM to mount as /dev/shm. Constrained by RAM & Offliner."
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col>
        <v-textarea
          v-model="editSchedule.config.artifacts_globs_str"
          label="Artifacts"
          hint="! Experts only ! Beware to not include your ZIM files and logs ! Globs of artifacts to archive, one glob expression per line."
          variant="outlined"
          auto-grow
          persistent-hint
        />
      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <v-row v-if="flagsFields.length > 0">
      <v-col cols="9">
        <h2>
          Scraper settings: <code>{{ taskName }}</code> command flags
        </h2>
      </v-col>
      <v-col cols="3" class="text-right">
        <v-btn :href="helpUrl" target="_blank" color="primary" variant="outlined"> Help </v-btn>
      </v-col>
    </v-row>

    <v-table v-if="flagsFields.length > 0" class="flags-table">
      <tbody>
        <tr v-for="field in flagsFields" :key="field.dataKey">
          <th class="w-25 align-top pa-4 font-weight-bold">
            {{ field.label }}
            <span v-if="field.required" class="text-red font-weight-bold text-subtitle-1">*</span>
          </th>
          <td class="align-top py-2">
            <SwitchButton
              v-if="field.component === 'switch'"
              v-model="editFlags[field.dataKey]"
              density="compact"
            />
            <v-select
              v-else-if="field.component === 'multiselect'"
              v-model="editFlags[field.dataKey]"
              :items="field.options"
              multiple
              chips
              closable-chips
              density="compact"
              variant="outlined"
              :placeholder="field.placeholder"
              :rules="getFieldRules(field)"
              :hide-details="'auto'"
              :validate-on="'eager blur'"
            />
            <v-select
              v-else-if="field.component === 'select'"
              v-model="editFlags[field.dataKey]"
              :items="field.options"
              density="compact"
              variant="outlined"
              :placeholder="field.placeholder"
              :required="field.required"
              :rules="getFieldRules(field)"
              :hide-details="'auto'"
              :validate-on="'blur'"
            />
            <v-text-field
              v-else-if="field.component === 'number'"
              v-model="editFlags[field.dataKey]"
              type="number"
              density="compact"
              variant="outlined"
              :placeholder="field.placeholder"
              :required="field.required"
              :step="field.step"
              :rules="getFieldRules(field)"
              :hide-details="'auto'"
              :validate-on="'blur'"
            />
            <v-text-field
              v-else-if="field.component === 'url'"
              v-model="editFlags[field.dataKey]"
              type="url"
              density="compact"
              variant="outlined"
              :placeholder="field.placeholder"
              :required="field.required"
              :rules="getFieldRules(field)"
              :hide-details="'auto'"
              :validate-on="'blur'"
            />
            <v-text-field
              v-else-if="field.component === 'email'"
              v-model="editFlags[field.dataKey]"
              type="email"
              density="compact"
              variant="outlined"
              :placeholder="field.placeholder"
              :required="field.required"
              :rules="getFieldRules(field)"
              :hide-details="'auto'"
              :validate-on="'blur'"
            />
            <v-text-field
              v-else-if="field.component === 'color'"
              v-model="editFlags[field.dataKey]"
              type="color"
              density="compact"
              variant="outlined"
              :placeholder="field.placeholder"
              :required="field.required"
              :rules="getFieldRules(field)"
              :hide-details="'auto'"
              :validate-on="'blur'"
            />
            <v-textarea
              v-else-if="field.component === 'textarea'"
              v-model="editFlags[field.dataKey]"
              density="compact"
              variant="outlined"
              :placeholder="field.placeholder"
              :required="field.required"
              auto-grow
              :rules="getFieldRules(field)"
              :hide-details="'auto'"
              :validate-on="'blur'"
            />
            <v-text-field
              v-else
              v-model="editFlags[field.dataKey]"
              density="compact"
              variant="outlined"
              :placeholder="field.placeholder"
              :required="field.required"
              :rules="getFieldRules(field)"
              :hide-details="'auto'"
              :validate-on="'blur'"
            />
            <v-text class="text-caption">{{ field.description }}</v-text>
          </td>
        </tr>
      </tbody>
    </v-table>

    <div class="d-flex flex-column flex-sm-row justify-end ga-2">
      <v-btn
        :disabled="!hasChanges"
        type="submit"
        :color="hasChanges ? 'primary' : 'secondary'"
        variant="elevated"
      >
        Update Offliner details
      </v-btn>
      <v-btn
        type="reset"
        :disabled="!hasChanges"
        :color="hasChanges ? 'dark' : 'secondary'"
        variant="outlined"
        @click="handleReset"
      >
        Reset
      </v-btn>
    </div>
  </v-form>
  <p v-else>Loading…</p>
</template>

<script setup lang="ts">
import SwitchButton from '@/components/SwitchButton.vue'
import constants from '@/constants'
import type { Resources } from '@/types/base'
import type { Language } from '@/types/language'
import type { OfflinerDefinition } from '@/types/offliner'
import type { Schedule, ScheduleConfig, ScheduleUpdateSchema } from '@/types/schedule'
import { fuzzyFilter, stringArrayEqual } from '@/utils/cmp'
import { formattedBytesSize } from '@/utils/format'
import diff from 'deep-diff'
import { byGrapheme } from 'split-by-grapheme'
import { computed, onUnmounted, ref, watch } from 'vue'

interface FlagField {
  label: string
  dataKey: string
  required: boolean
  description: string | null
  placeholder: string
  component: string
  options?: Array<{ title: string; value: string | undefined }>
  step?: number | null
  min: number | null
  max: number | null
  min_length: number | null
  max_length: number | null
  pattern: string | null
}

export interface Props {
  schedule: Schedule
  languages: Language[]
  tags: string[]
  contexts: string[]
  offliners: string[]
  platforms: string[]
  flagsDefinition: OfflinerDefinition[]
  helpUrl: string
  imageTags: string[]
}

interface Emits {
  (e: 'submit', payload: ScheduleUpdateSchema): void
  (e: 'image-name-change', imageName: string): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const editSchedule = ref<Schedule>(JSON.parse(JSON.stringify(props.schedule)))
const editComment = ref<string>('')
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const editFlags = ref<Record<string, any>>(
  JSON.parse(JSON.stringify(props.schedule.config.offliner)),
)

// Debounced image name change handler
let imageNameChangeTimeout: number | null = null
const lastEmittedImageName = ref<string>('')

const debouncedImageNameChange = (imageName: string) => {
  // Clear existing timeout
  if (imageNameChangeTimeout) {
    clearTimeout(imageNameChangeTimeout)
  }

  // Set new timeout to emit after 1s of no typing
  imageNameChangeTimeout = setTimeout(() => {
    if (imageName !== lastEmittedImageName.value) {
      lastEmittedImageName.value = imageName
      emit('image-name-change', imageName)
    }
  }, 1000)
}

const handleImageNameBlur = (imageName: string) => {
  // Clear any pending timeout
  if (imageNameChangeTimeout) {
    clearTimeout(imageNameChangeTimeout)
    imageNameChangeTimeout = null
  }

  // Immediately emit if the value has changed
  if (imageName !== lastEmittedImageName.value) {
    lastEmittedImageName.value = imageName
    emit('image-name-change', imageName)
  }
}

// Initialize edit data when schedule changes
watch(
  () => props.schedule,
  (newSchedule) => {
    if (newSchedule) {
      editSchedule.value = JSON.parse(JSON.stringify(newSchedule))
      editFlags.value = JSON.parse(JSON.stringify(newSchedule.config.offliner))
      // Initialize lastEmittedImageName with current schedule's image name
      lastEmittedImageName.value = newSchedule.config.image.name
    }
  },
  { deep: true, immediate: true },
)

// Cleanup timeout on component unmount
onUnmounted(() => {
  if (imageNameChangeTimeout) {
    clearTimeout(imageNameChangeTimeout)
  }
})

const taskName = computed(() => {
  return (
    editSchedule.value.config.offliner.offliner_id || props.schedule.config.offliner.offliner_id
  )
})

// Helper function to validate a single field value against its rules
const validateFieldValue = (field: FlagField, value: unknown): boolean => {
  const rules = getFieldRules(field)

  for (const rule of rules) {
    const result = rule(value)
    if (result !== true) {
      return false // Validation failed
    }
  }

  return true // All rules passed
}

// Check if all flag fields are valid
const areAllFieldsValid = computed(() => {
  if (!flagsFields.value.length) return true

  for (const field of flagsFields.value) {
    const value = editFlags.value[field.dataKey]
    if (!validateFieldValue(field, value)) {
      return false
    }
  }

  return true
})

const hasChanges = computed(() => {
  if (!(props.schedule && editSchedule.value)) return false

  // Check basic schedule properties
  const basicProps: Array<keyof Schedule> = ['category', 'name', 'enabled', 'periodicity']
  for (const prop of basicProps) {
    if (editSchedule.value[prop] !== props.schedule[prop]) return true
  }

  // Check context with null/empty string equivalence
  const originalContext = props.schedule.context
  const editedContext = editSchedule.value.context
  if (originalContext !== editedContext) {
    // Consider null and empty string as equivalent
    if (
      !(
        (originalContext === null || originalContext === '') &&
        (editedContext === null || editedContext === '')
      )
    ) {
      return true
    }
  }

  // Check tags
  if (!stringArrayEqual(editSchedule.value.tags, props.schedule.tags)) return true

  // Check language
  if (editSchedule.value.language.code !== props.schedule.language.code) return true

  // Check config properties
  const configProps: Array<keyof ScheduleConfig> = ['warehouse_path', 'platform', 'monitor']
  for (const prop of configProps) {
    if (editSchedule.value.config[prop] !== props.schedule.config[prop]) return true
  }

  // Check image
  if (
    editSchedule.value.config.image.name !== props.schedule.config.image.name ||
    editSchedule.value.config.image.tag !== props.schedule.config.image.tag
  )
    return true

  // Check resources
  const resourceProps: Array<keyof Resources> = ['cpu', 'memory', 'disk', 'shm']
  for (const prop of resourceProps) {
    if (editSchedule.value.config.resources[prop] !== props.schedule.config.resources[prop])
      return true
  }

  // check offliner id
  if (editSchedule.value.config.offliner.offliner_id !== props.schedule.config.offliner.offliner_id)
    return true

  // Check artifacts globs
  const artifacts_globs = processArtifactsGlobs(editSchedule.value.config.artifacts_globs_str)

  if (!stringArrayEqual(artifacts_globs, props.schedule.config.artifacts_globs || [])) return true

  // Check flags - use editFlags instead of the potentially mutated offliner object
  let changes = diff(props.schedule.config.offliner, editFlags.value)

  if (!changes) return false

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  changes = changes.filter(function (change: any) {
    // Filter out empty changes (new empty fields or fields changed to empty)
    if (
      change.kind === 'N' &&
      (change.rhs === '' || change.rhs === undefined || change.rhs === null)
    ) {
      return false
    }
    if (change.kind === 'E') {
      // if we are toggling a switch to false and it's a null on the original object,
      // then it's not a change
      if (change.lhs === null && change.rhs === false) return false
      if (change.rhs === undefined || change.rhs === null) {
        return false
      }
      // If a value is empty and the previous value is null, it's not a change
      if (change.lhs === null && change.rhs === '') return false
    }
    return true
  })

  const hasActualChanges = changes.length > 0

  // Return true only if there are changes AND all fields are valid
  return hasActualChanges && areAllFieldsValid.value
})

const flagsFields = computed(() => {
  if (!props.flagsDefinition) return []

  return props.flagsDefinition.map((field) => {
    let component = 'text'
    let options: Array<{ title: string; value: string | undefined }> | undefined = undefined
    let step = null

    if (field.type === 'hex-color') {
      component = 'color'
    } else if (field.type === 'url') {
      component = 'url'
    } else if (field.type === 'email') {
      component = 'email'
    } else if (field.type === 'integer') {
      component = 'number'
      step = 1
    } else if (field.type === 'float') {
      component = 'number'
      step = 0.1
    } else if (field.type === 'list-of-string-enum') {
      component = 'multiselect'
      options =
        field.choices?.map((choice) => ({
          title: choice.title,
          value: choice.value,
        })) || undefined
    } else if (field.type === 'boolean') {
      component = 'switch'
    } else if (field.type === 'string-enum') {
      component = 'select'
      options =
        field.choices?.map((choice) => ({
          title: choice.title,
          value: choice.value,
        })) || undefined
    } else if (field.type === 'long-text') {
      component = 'textarea'
    }

    return {
      label: field.label || field.data_key,
      dataKey: field.data_key,
      key: field.key,
      required: field.required,
      description: field.description,
      min: field.min,
      max: field.max,
      min_length: field.min_length,
      max_length: field.max_length,
      pattern: field.pattern,
      placeholder: 'Not set',
      component,
      options,
      step,
    }
  })
})

const getFieldRules = (field: FlagField) => {
  const rules: Array<(value: unknown) => boolean | string> = []

  if (field.required) {
    rules.push((value: unknown) => {
      if (!value || value === '' || value === undefined || value === null) {
        return 'This field is required'
      }
      return true
    })
  }

  // Add type-specific validation
  if (field.component === 'url') {
    rules.push((value: unknown) => {
      if (value && typeof value === 'string' && value !== '') {
        try {
          new URL(value)
          return true
        } catch {
          return 'Please enter a valid URL'
        }
      }
      return true
    })
  }

  if (field.component === 'email') {
    rules.push((value: unknown) => {
      if (value && typeof value === 'string' && value !== '') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(value)) {
          return 'Please enter a valid email address'
        }
      }
      return true
    })
  }

  if (field.component === 'number') {
    rules.push((value: unknown) => {
      if (value && value !== '') {
        const num = Number(value)
        if (isNaN(num)) {
          return 'Please enter a valid number'
        }
      }
      return true
    })
  }

  // Add validation for min, max, min_length, and pattern constraints
  const shouldValidate = (value: unknown) => {
    return value !== null && value !== undefined && value !== ''
  }

  // Min length validation
  if (field.min_length !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value) && typeof value === 'string') {
        if (value.split(byGrapheme).length < field.min_length!) {
          return `Minimum length is ${field.min_length} characters`
        }
      }
      return true
    })
  }

  // Max length validation
  if (field.max_length !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value) && typeof value === 'string') {
        if (value.split(byGrapheme).length > field.max_length!) {
          return `Maximum length is ${field.max_length} characters`
        }
      }
      return true
    })
  }

  // Min value validation (for numbers)
  if (field.min !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value)) {
        const num = Number(value)
        if (!isNaN(num) && num < field.min!) {
          return `Minimum value is ${field.min}`
        }
      }
      return true
    })
  }

  // Max value validation (for numbers)
  if (field.max !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value)) {
        const num = Number(value)
        if (!isNaN(num) && num > field.max!) {
          return `Maximum value is ${field.max}`
        }
      }
      return true
    })
  }

  // Pattern validation (regex)
  if (field.pattern !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value) && typeof value === 'string') {
        try {
          // construct the regex from the pattern string
          const regex = new RegExp(field.pattern!)
          if (!regex.test(value)) {
            return `Value must match pattern: ${field.pattern}`
          }
        } catch {
          // If regex is invalid, skip validation
          console.warn(`Invalid regex pattern for field ${field.dataKey}:`, field.pattern)
        }
      }
      return true
    })
  }

  return rules
}

const languagesOptions = computed(() => {
  return props.languages.map((language) => ({
    title: language.name,
    value: language.code,
  }))
})

const categoriesOptions = computed(() => {
  return constants.CATEGORIES.map((category) => ({
    title: category,
    value: category,
  }))
})

const warehousePathsOptions = computed(() => {
  return constants.WAREHOUSE_PATHS.map((path) => ({
    title: path,
    value: path,
  }))
})

const offlinersOptions = computed(() => {
  return props.offliners.map((offliner) => ({
    title: offliner,
    value: offliner,
  }))
})

const platformsOptions = computed(() => {
  const values: Array<{ title: string; value: string | undefined }> = props.platforms.map(
    (platform) => ({
      title: platform,
      value: platform,
    }),
  )
  return values
})

const periodicityOptions = computed(() => {
  return constants.PERIODICITIES.map((periodicity) => ({
    title: periodicity,
    value: periodicity,
  }))
})

const memoryOptions = computed(() => {
  const values = [...constants.MEMORY_VALUES]
  if (values.indexOf(editSchedule.value.config.resources.memory) === -1) {
    values.push(editSchedule.value.config.resources.memory)
  }
  values.sort((a, b) => a - b)
  return values.map((value) => ({ title: formattedBytesSize(value), value }))
})

const diskOptions = computed(() => {
  const values = [...constants.DISK_VALUES]
  if (values.indexOf(editSchedule.value.config.resources.disk) === -1) {
    values.push(editSchedule.value.config.resources.disk)
  }
  values.sort((a, b) => a - b)
  return values.map((value) => ({ title: formattedBytesSize(value), value }))
})

const imageTagOptions = computed(() => {
  return [...props.imageTags].sort().map((tag) => ({ title: tag, value: tag }))
})

const handleSubmit = () => {
  if (!hasChanges.value) return

  const payload = buildPayload()
  if (payload) {
    emit('submit', payload)
    // Clear the comment after submitting
    editComment.value = ''
  }
}

const handleReset = () => {
  if (props.schedule) {
    editSchedule.value = JSON.parse(JSON.stringify(props.schedule))
    editFlags.value = JSON.parse(JSON.stringify(props.schedule.config.offliner))
    editComment.value = ''
  }
}

const processArtifactsGlobs = (artifactsGlobsStr: string | undefined): string[] => {
  return artifactsGlobsStr
    ? artifactsGlobsStr
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line !== '')
    : []
}

const handleOfflinerChange = () => {
  // assume flags are different, so reset edit schedule flags
  editFlags.value = {}
}

const buildPayload = (): ScheduleUpdateSchema | null => {
  const payload: Partial<ScheduleUpdateSchema> = {}

  payload.name = editSchedule.value.name.trim()

  // Basic properties
  const basicProps: Array<keyof Schedule> = ['name', 'category', 'enabled', 'periodicity']
  for (const prop of basicProps) {
    if (editSchedule.value[prop] !== props.schedule[prop]) {
      if (prop === 'name') {
        payload.name = editSchedule.value[prop]
      } else if (prop === 'category') {
        payload.category = editSchedule.value[prop]
      } else if (prop === 'enabled') {
        payload.enabled = editSchedule.value[prop]
      } else if (prop === 'periodicity') {
        payload.periodicity = editSchedule.value[prop]
      }
    }
  }

  // Context with null/empty string equivalence
  const originalContext = props.schedule.context
  const editedContext = editSchedule.value.context
  if (originalContext !== editedContext) {
    // Consider null and empty string as equivalent
    if (
      !(
        (originalContext === null || originalContext === '') &&
        (editedContext === null || editedContext === '')
      )
    ) {
      // If edited context is null (because the user cleared the field), set it to an
      // empty string as the API expects a string. Null values are considered as unset.
      payload.context = editedContext || ''
    }
  }

  // Comment
  if (editComment.value?.trim()) {
    payload.comment = editComment.value.trim()
  }

  // Tags
  if (!stringArrayEqual(editSchedule.value.tags, props.schedule.tags)) {
    payload.tags = editSchedule.value.tags
  }

  // Language
  if (editSchedule.value.language.code !== props.schedule.language.code) {
    payload.language = editSchedule.value.language.code
  }

  // Config properties
  const configProps: Array<keyof ScheduleConfig> = ['warehouse_path', 'platform', 'monitor']
  for (const prop of configProps) {
    if (editSchedule.value.config[prop] !== props.schedule.config[prop]) {
      if (prop === 'warehouse_path') {
        payload.warehouse_path = editSchedule.value.config[prop]
      } else if (prop === 'platform') {
        payload.platform = editSchedule.value.config[prop]
      } else if (prop === 'monitor') {
        payload.monitor = editSchedule.value.config[prop]
      }
    }
  }

  // Offliner name
  if (
    editSchedule.value.config.offliner.offliner_id !== props.schedule.config.offliner.offliner_id
  ) {
    payload.offliner = editSchedule.value.config.offliner.offliner_id as string
  }

  // Image
  if (
    editSchedule.value.config.image.name !== props.schedule.config.image.name ||
    editSchedule.value.config.image.tag !== props.schedule.config.image.tag
  ) {
    payload.image = editSchedule.value.config.image
  }

  // Resources
  const resourceProps: Array<keyof Resources> = ['cpu', 'memory', 'disk', 'shm']
  const resourcesChanged = resourceProps.some(
    (prop) => editSchedule.value.config.resources[prop] !== props.schedule.config.resources[prop],
  )
  if (resourcesChanged) {
    payload.resources = editSchedule.value.config.resources
  }

  // Artifacts
  const artifacts_globs = processArtifactsGlobs(editSchedule.value.config.artifacts_globs_str)

  if (!stringArrayEqual(artifacts_globs, props.schedule.config.artifacts_globs || [])) {
    payload.artifacts_globs = artifacts_globs
  }

  // Flags
  const flags = cleanFlagsPayload(JSON.parse(JSON.stringify(editFlags.value)))
  // remove the offliner_id from the flags as it is not used by the server and the schema is strict
  // server-side
  delete flags.offliner_id
  if (Object.keys(flags).length > 0) {
    payload.flags = flags
  }

  if (Object.keys(payload).length === 0) {
    return null
  }

  return payload as ScheduleUpdateSchema
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const cleanFlagsPayload = (flags: Record<string, any>) => {
  const cleaned = JSON.parse(JSON.stringify(flags))

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recursivelyCleanup = (obj: any) => {
    for (const key in obj) {
      if (typeof obj[key] === 'object' && obj[key] !== null) {
        recursivelyCleanup(obj[key])
      } else if (
        !Array.isArray(obj) &&
        (obj[key] === '' || obj[key] === undefined || obj[key] === null)
      ) {
        // if an object is set to empty string, we update it to null as it should
        // be on the backend since fields are either set or not set and fields that
        // are set shouldn't be empty
        if (obj[key] == '') {
          obj[key] = null
        } else {
          delete obj[key]
        }
      }
    }
  }

  recursivelyCleanup(cleaned)
  return cleaned
}
</script>

<style type="text/css" scoped>
.align-top {
  vertical-align: top;
}
</style>
