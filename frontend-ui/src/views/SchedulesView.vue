<!-- Filterable list of schedules with filtered-fire button -->

<template>
  <SchedulesBaseView
    :archived="false"
    :route-name="'schedules-list'"
    :can-request-tasks="canRequestTasks"
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
</template>

<script setup lang="ts">
import RequestSelectionButton from '@/components/RequestSelectionButton.vue'
import SchedulesBaseView from '@/components/SchedulesBaseView.vue'
import { useAuthStore } from '@/stores/auth'
import { computed } from 'vue'

// Stores
const authStore = useAuthStore()

// Computed properties
const canRequestTasks = computed(() => authStore.hasPermission('tasks', 'request'))
</script>
