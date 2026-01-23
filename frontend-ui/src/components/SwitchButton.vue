<template>
  <v-switch
    persistent-hint
    :label="label"
    :hint="details"
    :model-value="modelValue"
    :color="color"
    :disabled="disabled"
    :density="density"
    :hide-details="'auto'"
    @update:model-value="handleUpdate"
  />
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean
  label?: string
  details?: string
  color?: string
  disabled?: boolean
  density?: 'default' | 'compact' | 'comfortable'
}

interface Emits {
  (e: 'update:modelValue', value: boolean): void
}

withDefaults(defineProps<Props>(), {
  color: 'primary',
  disabled: false,
  density: 'default',
})

const emit = defineEmits<Emits>()

const handleUpdate = (value: boolean | null) => {
  emit('update:modelValue', value ?? false)
}
</script>
