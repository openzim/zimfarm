<template>
  <v-table class="flags-table">
    <tbody>
      <tr v-for="(value, name) in filteredOffliner" :key="name">
        <td>
          <code class="text-pink-accent-2">{{ name }}</code>
        </td>
        <td>
          <span>{{ value }}</span>
        </td>
      </tr>
    </tbody>
  </v-table>
</template>

<script setup lang="ts">
import type { OfflinerFlags } from '@/types/schedule'
import { computed } from 'vue'

interface Props {
  offliner: OfflinerFlags
  shrink?: boolean
  secretFields?: string[]
}

const props = withDefaults(defineProps<Props>(), {
  shrink: false,
  secretFields: () => [],
})

const filteredOffliner = computed(() => {
  const result: Record<string, unknown> = {}
  for (const [key, value] of Object.entries(props.offliner)) {
    if (value !== null && value !== undefined && value !== '') {
      result[key] = value
    }
  }
  // remove the offliner id from the result
  delete result.offliner_id

  // Sort keys alphabetically and create a new object with sorted keys
  const sortedResult: Record<string, unknown> = {}
  Object.keys(result)
    .sort()
    .forEach((key) => {
      sortedResult[key] = result[key]
    })

  return sortedResult
})
</script>

<style scoped>
.flags-table tbody tr:nth-of-type(odd) {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>
