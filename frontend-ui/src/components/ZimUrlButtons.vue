<template>
  <div v-if="loading" class="d-flex align-center">
    <v-progress-circular indeterminate size="20" width="2" />
  </div>
  <div v-else-if="displayUrls && displayUrls.length > 0" class="d-inline-flex align-center">
    <v-tooltip v-for="url in displayUrls" :key="`${url.kind}-${url.collection}`" location="bottom">
      <template #activator="{ props: tooltipProps }">
        <v-btn
          v-bind="tooltipProps"
          :href="url.url"
          target="_blank"
          icon
          variant="text"
          :size="compact ? 'x-small' : 'small'"
        >
          <v-icon>{{ url.kind === 'download' ? 'mdi-download' : 'mdi-eye' }}</v-icon>
        </v-btn>
      </template>
      <span>{{ url.kind === 'download' ? 'Download' : 'View' }} ({{ url.collection }})</span>
    </v-tooltip>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ZimUrl } from '@/types/tasks'

const props = withDefaults(
  defineProps<{
    urls?: ZimUrl[]
    loading?: boolean
    compact?: boolean
  }>(),
  {
    urls: undefined,
    loading: false,
    compact: false,
  },
)

const displayUrls = computed(
  () => props.urls?.filter((url) => url.kind === 'view' || url.kind === 'download') ?? [],
)
</script>
