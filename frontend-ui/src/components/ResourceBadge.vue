<template>
  <v-chip
    variant="outlined"
    size="small"
    class="mr-2"
  >
    <v-icon
      :icon="icon"
      size="small"
      class="mr-1"
    />
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
}

const props = withDefaults(defineProps<Props>(), {
  humanValue: undefined
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
    shm: 'mdi-disc'
  }
  return iconMap[props.kind]
})
</script>
