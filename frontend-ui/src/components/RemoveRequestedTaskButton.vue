<!-- Full-featured button to remove a requested task by its id

  - disabled if not signed-in
  - displays a confirmation dialog before removal
  - displays a spinner on click
  - calls the API in the background
  - displays result as an AlertFeedback -->

<template>
  <div>
    <v-btn
      v-if="canUnRequestTasks"
      color="error"
      variant="outlined"
      size="small"
      :loading="isRemoving"
      :disabled="isRemoving"
      @click="showConfirmDialog"
    >
      <v-icon size="small" class="mr-1">mdi-delete</v-icon>
      {{ isRemoving ? 'Removing...' : 'Remove' }}
    </v-btn>

    <ConfirmDialog
      v-model="showDialog"
      title="Remove Requested Task"
      message="Are you sure you want to remove this requested task?"
      confirm-text="Remove"
      cancel-text="Cancel"
      confirm-color="error"
      icon="mdi-delete"
      icon-color="error"
      :loading="isRemoving"
      @confirm="removeTask"
      @cancel="hideConfirmDialog"
    />
  </div>
</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useAuthStore } from '@/stores/auth'
import { useRequestedTasksStore } from '@/stores/requestedTasks'
import { computed, ref } from 'vue'

// Props
interface Props {
  id: string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'requested-task-removed': [id: string]
}>()

const requestedTasksStore = useRequestedTasksStore()
const authStore = useAuthStore()

const isRemoving = ref(false)
const showDialog = ref(false)

const canUnRequestTasks = computed(() => authStore.hasPermission('tasks', 'unrequest'))

const showConfirmDialog = () => {
  showDialog.value = true
}

const hideConfirmDialog = () => {
  showDialog.value = false
}

const removeTask = async () => {
  if (isRemoving.value) return

  isRemoving.value = true

  try {
    const success = await requestedTasksStore.removeRequestedTask(props.id)

    if (success) {
      // Emit event to parent component
      // TODO: Set parent.working to false, not sure what this means
      // TODO: parent.alertSuccess
      emit('requested-task-removed', props.id)
    }
  } catch (error) {
    console.error('Failed to remove requested task:', error)
  } finally {
    isRemoving.value = false
    hideConfirmDialog()
  }
}
</script>
