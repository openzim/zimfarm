<!-- Filterable list of schedules with filtered-fire button -->

<template>
  <div>
    <SchedulesBaseView
      :archived="false"
      :route-name="'schedules-list'"
      :can-request-tasks="canRequestTasks"
      @filters-updated="handleFiltersUpdated"
    >
      <template #actions="{ selectedSchedules, requestingText, handleFetchSchedules }">
        <RequestSelectionButton
          v-if="canRequestTasks"
          :can-request-tasks="canRequestTasks"
          :requesting-text="requestingText"
          :count="selectedSchedules.length"
          @fetch-schedules="handleFetchSchedules"
        />
      </template>
    </SchedulesBaseView>

    <div v-if="canAccessArchives" class="pa-0 mt-4">
      <v-tooltip location="top">
        <template #activator="{ props }">
          <v-btn
            v-bind="props"
            variant="outlined"
            size="small"
            :loading="loadingArchivedCount"
            @click="navigateToArchives"
          >
            <v-icon size="small" class="mr-2">mdi-archive</v-icon>
            {{ archivedCountText }}
          </v-btn>
        </template>
        <span>{{ archivedTooltipText }}</span>
      </v-tooltip>
    </div>
  </div>
</template>

<script setup lang="ts">
import RequestSelectionButton from '@/components/RequestSelectionButton.vue'
import SchedulesBaseView from '@/components/SchedulesBaseView.vue'
import { useAuthStore } from '@/stores/auth'
import { useScheduleStore } from '@/stores/schedule'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

// Stores
const authStore = useAuthStore()
const scheduleStore = useScheduleStore()
const router = useRouter()

// State
const currentFilters = ref({
  name: '',
  categories: [] as string[],
  languages: [] as string[],
  tags: [] as string[],
})
const archivedCount = ref(0)
const loadingArchivedCount = ref(false)

// Computed properties
const canRequestTasks = computed(() => authStore.hasPermission('requested_tasks', 'create'))
const canAccessArchives = computed(() => authStore.hasPermission('schedules', 'archive'))

const archivedCountText = computed(() => {
  if (loadingArchivedCount.value) {
    return 'Loading...'
  }
  const count = archivedCount.value
  return `ARCHIVES (${count})`
})

const archivedTooltipText = computed(() => {
  const count = archivedCount.value
  return count === 1 ? '1 matching archived recipe' : `${count} matching archived recipes`
})

// Methods
async function fetchArchivedCount(filters: typeof currentFilters.value) {
  if (!canAccessArchives.value) return

  loadingArchivedCount.value = true
  try {
    await scheduleStore.fetchSchedules(
      1, // limit - we only need the count
      0, // skip
      filters.categories.length > 0 ? filters.categories : undefined,
      filters.languages.length > 0 ? filters.languages : undefined,
      filters.tags.length > 0 ? filters.tags : undefined,
      filters.name || undefined,
      true, // archived
    )
    archivedCount.value = scheduleStore.paginator.count
  } catch (error) {
    console.error('Failed to fetch archived count', error)
    archivedCount.value = 0
  } finally {
    loadingArchivedCount.value = false
  }
}

function handleFiltersUpdated(filters: typeof currentFilters.value) {
  currentFilters.value = filters
  fetchArchivedCount(filters)
}

function navigateToArchives() {
  const query: Record<string, string | string[]> = {}

  if (currentFilters.value.name) {
    query.name = currentFilters.value.name
  }
  if (currentFilters.value.categories.length === 1) {
    query.category = currentFilters.value.categories[0]
  } else if (currentFilters.value.categories.length > 1) {
    query.category = currentFilters.value.categories
  }
  if (currentFilters.value.languages.length === 1) {
    query.lang = currentFilters.value.languages[0]
  } else if (currentFilters.value.languages.length > 1) {
    query.lang = currentFilters.value.languages
  }
  if (currentFilters.value.tags.length === 1) {
    query.tag = currentFilters.value.tags[0]
  } else if (currentFilters.value.tags.length > 1) {
    query.tag = currentFilters.value.tags
  }

  router.push({
    name: 'archived-schedules',
    query: Object.keys(query).length > 0 ? query : undefined,
  })
}
</script>
