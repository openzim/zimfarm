<template>
  <div v-if="loading" class="d-flex align-center">
    <v-progress-circular indeterminate size="20" width="2" />
    <span v-if="!compact && !iconOnly" class="ml-2 text-grey">Loading URLs...</span>
  </div>
  <div v-else-if="urls && urls.length > 0" :class="iconOnly ? 'd-inline-flex align-center' : ''">
    <v-tooltip v-for="url in urls" :key="`${url.kind}-${url.collection}`" location="bottom">
      <template #activator="{ props: tooltipProps }">
        <v-btn
          v-bind="tooltipProps"
          :href="url.url"
          target="_blank"
          :icon="iconOnly || compact"
          :prepend-icon="
            iconOnly || compact ? undefined : url.kind === 'download' ? 'mdi-download' : 'mdi-eye'
          "
          :variant="iconOnly ? 'text' : compact ? 'text' : 'outlined'"
          :size="iconOnly ? 'x-small' : compact ? 'x-small' : 'small'"
          :class="iconOnly ? 'ml-1' : compact ? '' : 'mr-2'"
        >
          <v-icon v-if="iconOnly || compact" :size="iconOnly ? 'small' : undefined">
            {{ url.kind === 'download' ? 'mdi-download' : 'mdi-eye' }}
          </v-icon>
          <span v-else>{{ url.kind === 'download' ? 'Download' : 'View' }}</span>
        </v-btn>
      </template>
      <span>{{ url.kind === 'download' ? 'Download' : 'View' }} ({{ url.collection }})</span>
    </v-tooltip>
  </div>
  <span v-else-if="!iconOnly" class="text-grey">{{ emptyText }}</span>
</template>

<script setup lang="ts">
import type { ZimUrl } from '@/types/tasks'

withDefaults(
  defineProps<{
    urls?: ZimUrl[]
    loading?: boolean
    compact?: boolean
    iconOnly?: boolean
    emptyText?: string
  }>(),
  {
    urls: undefined,
    loading: false,
    compact: false,
    iconOnly: false,
    emptyText: 'No URLs available',
  },
)
</script>
