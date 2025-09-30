<template>
  <div class="d-flex flex-column">
    <span v-if="label" class="text-body-2">{{ label }}</span>
    <div class="d-flex align-center">
      <v-switch
        :model-value="modelValue"
        :color="color"
        :disabled="disabled"
        :density="density"
        :hide-details="hideDetails"
        @update:model-value="handleUpdate"
        :hint="hint"
        :persistent-hint="persistentHint"
      />
      <span class="ml-2 text-body-2 text-medium-emphasis">
        {{ modelValue ? 'Enabled' : 'Disabled' }}
      </span>
    </div>
  </div>
  <div v-if="details" class="mt-1 text-caption text-medium-emphasis">
    {{ details }}
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean
  label?: string
  details?: string
  color?: string
  disabled?: boolean
  density?: 'default' | 'compact' | 'comfortable'
  hideDetails?: boolean | 'auto'
  hint?: string
  persistentHint?: boolean
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

withDefaults(defineProps<Props>(), {
  color: 'primary',
  disabled: false,
  density: 'default',
  hideDetails: true,
})

const emit = defineEmits<Emits>()

const handleUpdate = (value: boolean | null) => {
  emit('update:modelValue', value ?? false)
}
</script>
