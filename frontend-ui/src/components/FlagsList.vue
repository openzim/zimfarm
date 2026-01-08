<template>
  <v-table class="flags-table">
    <tbody>
      <tr v-for="(value, name) in filteredOffliner" :key="name">
        <td>
          <code class="text-pink-accent-2">{{ name }}</code>
        </td>
        <td>
          <div class="d-flex align-center ga-2">
            <span>{{ value }}</span>
            <BlobViewer
              v-if="getBlobField(name)"
              :blob-value="String(value)"
              :kind="getBlobField(name)!.kind || 'image'"
            />
          </div>
        </td>
      </tr>
    </tbody>
  </v-table>
</template>

<script setup lang="ts">
import type { OfflinerFlags } from '@/types/schedule'
import type { OfflinerDefinition } from '@/types/offliner'
import { computed } from 'vue'
import BlobViewer from '@/components/BlobViewer.vue'

interface Props {
  offliner: OfflinerFlags
  shrink?: boolean
  flagsDefinition?: OfflinerDefinition[]
}

const props = withDefaults(defineProps<Props>(), {
  shrink: false,
  flagsDefinition: () => [],
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

const getBlobField = (fieldName: string) => {
  if (!props.flagsDefinition || props.flagsDefinition.length === 0) {
    return null
  }
  const field = props.flagsDefinition.find((f) => f.data_key === fieldName)
  return field?.type === 'blob' ? field : null
}
</script>

<style scoped>
.flags-table tbody tr:nth-of-type(odd) {
  background-color: rgba(0, 0, 0, 0.05);
}
</style>
