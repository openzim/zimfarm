<template>
  <SchedulesBaseView :archived="true" :route-name="'archived-schedules'" :can-request-tasks="false">
    <template #actions="{ selectedSchedules, restoringText, handleRestoreSchedules }">
      <RestoreSelectionButton
        v-if="canRestore"
        :can-restore="canRestore"
        :restoring-text="restoringText"
        :count="selectedSchedules.length"
        @restore-schedules="handleRestoreSchedules"
      />
    </template>
  </SchedulesBaseView>
</template>

<script setup lang="ts">
import RestoreSelectionButton from '@/components/RestoreSelectionButton.vue'
import SchedulesBaseView from '@/components/SchedulesBaseView.vue'
import { useAuthStore } from '@/stores/auth'
import { computed } from 'vue'

// Stores
const authStore = useAuthStore()

// Computed properties
const canRestore = computed(() => authStore.hasPermission('schedules', 'update'))
</script>
