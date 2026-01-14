<template>
  <v-chip :size="size" :density="density" :variant="variant" :class="customClass">
    <v-icon :icon="icon" :size="size" />
    {{ displayedValue }}
  </v-chip>
</template>

<script setup lang="ts">
import { formattedBytesSize } from '@/utils/format'
import { computed } from 'vue'

// Props
interface Props {
  kind: 'cpu' | 'memory' | 'disk' | 'shm'
  value: number
  humanValue?: string
  density?: 'compact' | 'default'
  variant?: 'outlined' | 'text' | 'tonal' | 'plain' | 'elevated' | 'flat'
  size?: 'x-small' | 'small' | 'default' | 'large' | 'x-large'
  customClass?: string
}

const props = withDefaults(defineProps<Props>(), {
  humanValue: undefined,
  density: 'default',
  variant: 'outlined',
  size: 'small',
  customClass: 'mr-2',
})

// Computed properties
const displayedValue = computed(() => {
  if (props.humanValue) {
    return props.humanValue
  }
  return props.kind === 'cpu' ? props.value : formattedBytesSize(props.value)
})

const icon = computed(() => {
  const iconMap = {
    cpu: 'mdi-cpu-64-bit',
    memory: 'mdi-memory',
    disk: 'mdi-harddisk',
    shm: 'mdi-disc',
  }
  return iconMap[props.kind]
})
</script>
