<template>
  <div :class="['d-flex', 'ga-1', layoutClass]">
    <span>
      <code :class="statusClass">{{ status }}</code
      ><template v-if="showTime">,</template>
    </span>
    <span v-if="showTime">
      <v-tooltip v-if="tooltip" :text="formatDt(computedTimestamp)" location="bottom">
        <template v-slot:activator="{ props: tooltipProps }">
          <router-link
            v-if="taskId"
            v-bind="tooltipProps"
            :to="{ name: 'task-detail', params: { id: taskId } }"
            class="text-decoration-none text-no-wrap"
          >
            {{ fromNow(computedTimestamp) }}
          </router-link>
          <span v-else v-bind="tooltipProps" class="text-no-wrap">
            {{ fromNow(computedTimestamp) }}
          </span>
        </template>
      </v-tooltip>
      <router-link
        v-else-if="taskId"
        :to="{ name: 'task-detail', params: { id: taskId } }"
        class="text-decoration-none text-no-wrap"
      >
        {{ fromNow(computedTimestamp) }}
      </router-link>
      <span v-else class="text-no-wrap">
        {{ fromNow(computedTimestamp) }}
      </span>
    </span>
  </div>
</template>

<script setup lang="ts">
import { formatDt, fromNow } from '@/utils/format'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { computed } from 'vue'
import { useDisplay } from 'vuetify'

// Props
interface Props {
  status: string
  timestamp?: [string, string][] | null
  updatedAt?: string | null
  taskId?: string | null
  tooltip?: boolean
  showTime?: boolean
  layout?: 'row' | 'column'
  justifyOnSmall?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  timestamp: null,
  updatedAt: null,
  taskId: null,
  tooltip: true,
  showTime: true,
  layout: 'row',
  justifyOnSmall: true,
})

const { smAndDown } = useDisplay()

// Computed properties
const layoutClass = computed(() => {
  const classes = props.layout === 'column' ? 'flex-column' : 'flex-row flex-wrap align-center'
  return smAndDown.value && props.justifyOnSmall ? `${classes} justify-end` : classes
})

const computedTimestamp = computed(() => {
  if (props.timestamp) {
    return getTimestampStringForStatus(props.timestamp, props.status, props.updatedAt || '')
  }
  return props.updatedAt || ''
})

const statusClass = computed(() => {
  const status = props.status.toLowerCase()
  if (status === 'succeeded') return 'text-success'
  if (['failed', 'canceled', 'cancel_requested', 'canceling'].includes(status))
    return 'text-pink-accent-2'
  return 'text-warning'
})
</script>
