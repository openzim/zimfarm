<!-- Full-featured button to cancel a task by its id

  - disabled if not signed-in
  - displays a confirmation dialog before cancellation
  - displays a spinner on click
  - calls the API in the background
  - displays result as an AlertFeedback -->

<template>
  <div>
    <v-btn
      v-if="canCancelTasks"
      color="error"
      variant="outlined"
      size="small"
      :loading="isCanceling"
      :disabled="isCanceling"
      @click="showConfirmDialog"
    >
      <v-icon size="small" class="mr-1">mdi-cancel</v-icon>
      {{ isCanceling ? 'Canceling...' : 'Cancel' }}
    </v-btn>

    <ConfirmDialog
      v-model="showDialog"
      title="Cancel Task"
      message="Are you sure you want to cancel this task?"
      confirm-text="Cancel Task"
      cancel-text="Keep Running"
      confirm-color="error"
      icon="mdi-cancel"
      icon-color="error"
      :loading="isCanceling"
      @confirm="cancelTask"
      @cancel="hideConfirmDialog"
    />
  </div>
</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useTasksStore } from '@/stores/tasks'
import { computed, ref } from 'vue'

// Props
interface Props {
  id: string
}

const props = defineProps<Props>()

// Emits
const emit = defineEmits<{
  'task-canceled': [id: string]
}>()

const tasksStore = useTasksStore()
const authStore = useAuthStore()
const notificationStore = useNotificationStore()

const isCanceling = ref(false)
const showDialog = ref(false)

const canCancelTasks = computed(() => authStore.hasPermission('tasks', 'cancel'))

const showConfirmDialog = () => {
  showDialog.value = true
}

const hideConfirmDialog = () => {
  showDialog.value = false
}

const cancelTask = async () => {
  if (isCanceling.value) return

  isCanceling.value = true

  try {
    const success = await tasksStore.cancelTask(props.id)

    if (success) {
      notificationStore.showSuccess('Task cancellation requested')
      emit('task-canceled', props.id)
    } else {
      // Show error notifications from the store
      for (const error of tasksStore.errors) {
        notificationStore.showError(error)
      }
    }
  } catch (error) {
    console.error('Failed to cancel task:', error)
    notificationStore.showError('Failed to cancel task')
  } finally {
    isCanceling.value = false
    hideConfirmDialog()
  }
}
</script>
