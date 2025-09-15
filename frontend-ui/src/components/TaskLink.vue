<template>
  <v-tooltip v-if="tooltip" :text="formatDt(computedTimestamp)">
    <template v-slot:activator="{ props }">
      <router-link v-bind="props" :to="to" class="text-decoration-none">
        {{ displayText }}
      </router-link>
    </template>
  </v-tooltip>
  <router-link v-else :to="to" class="text-decoration-none">
    {{ displayText }}
  </router-link>
</template>

<script setup lang="ts">
import { formatDt, fromNow } from '@/utils/format'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { computed } from 'vue'

// Props
interface Props {
  id: string
  updatedAt: string
  status: string
  timestamp: [string, string][]
  tooltip?: boolean
  text?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  tooltip: true,
  text: null,
})

// Computed properties
const to = computed(() => {
  return { name: 'task-detail', params: { id: props.id } }
})

const computedTimestamp = computed(() => {
  return getTimestampStringForStatus(props.timestamp, props.status, props.updatedAt)
})

const displayText = computed(() => {
  return props.text === null ? fromNow(computedTimestamp.value) : props.text
})
</script>
