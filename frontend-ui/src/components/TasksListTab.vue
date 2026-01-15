<template>
  <v-tabs v-model="activeTab" color="primary" slider-color="primary" class="mb-4" grow>
    <v-tab
      base-color="primary"
      v-for="filterOption in filterOptions"
      :key="filterOption.value"
      :value="filterOption.value"
      class="text-none text-subtitle-2"
      @click="$emit('filter-changed', filterOption.value)"
    >
      {{ filterOption.label }}
    </v-tab>
  </v-tabs>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  filter: string
  filterOptions: { value: string; label: string }[]
}>()

defineEmits<{
  'filter-changed': [filter: string]
}>()

// Reactive data
const activeTab = ref(props.filter)

// Watch for prop changes to update active tab
watch(
  () => props.filter,
  (newFilter) => {
    activeTab.value = newFilter
  },
)
</script>

<style scoped>
/* Custom styles if needed */
</style>
