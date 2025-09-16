<template>
  <v-card flat class="mb-4">
    <v-card-text>
      <v-row>
        <v-col cols="12" sm="6" md="3">
          <v-text-field
            v-model="localFilters.name"
            label="Name"
            placeholder="Search by name..."
            variant="outlined"
            density="compact"
            hide-details
            @change="emitFilters"
          />
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="localFilters.categories"
            :items="categoriesOptions"
            label="Categories"
            placeholder="Select categories"
            variant="outlined"
            density="compact"
            hide-details
            multiple
            chips
            closable-chips
            @update:model-value="emitFilters"
          />
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="localFilters.languages"
            :items="languagesOptions"
            label="Languages"
            placeholder="Select languages"
            variant="outlined"
            density="compact"
            hide-details
            multiple
            chips
            closable-chips
            @update:model-value="emitFilters"
          />
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-select
            v-model="localFilters.tags"
            :items="tagsOptions"
            label="Tags"
            placeholder="Select tags"
            variant="outlined"
            density="compact"
            hide-details
            multiple
            chips
            closable-chips
            @update:model-value="emitFilters"
          />
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import type { Language } from '@/types/language'
import { computed, ref, watch } from 'vue'

// Props
interface Props {
  filters: {
    name: string
    categories: string[]
    languages: string[]
    tags: string[]
  }
  categories: string[]
  languages: Language[]
  tags: string[]
}

const props = defineProps<Props>()

// Define emits
const emit = defineEmits<{
  filtersChanged: [
    filters: {
      name: string
      categories: string[]
      languages: string[]
      tags: string[]
    },
  ]
}>()

// Local filters state
const localFilters = ref({
  name: props.filters.name,
  categories: [...props.filters.categories],
  languages: [...props.filters.languages],
  tags: [...props.filters.tags],
})

// Watch for prop changes and update local state
watch(
  () => props.filters,
  (newFilters) => {
    localFilters.value = {
      name: newFilters.name,
      categories: [...newFilters.categories],
      languages: [...newFilters.languages],
      tags: [...newFilters.tags],
    }
  },
  { deep: true },
)

// Computed properties for select options
const categoriesOptions = computed(() => {
  return props.categories.map((category) => ({
    title: category,
    value: category,
  }))
})

const languagesOptions = computed(() => {
  return props.languages.map((language) => ({
    title: language.name,
    value: language.code,
  }))
})

const tagsOptions = computed(() => {
  return props.tags.map((tag) => ({
    title: tag,
    value: tag,
  }))
})

// Emit filters when they change
function emitFilters() {
  emit('filtersChanged', {
    name: localFilters.value.name,
    categories: localFilters.value.categories,
    languages: localFilters.value.languages,
    tags: localFilters.value.tags,
  })
}
</script>
