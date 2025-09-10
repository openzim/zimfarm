<template>
  <div class="notification-system">
    <div class="notification-container">
      <v-snackbar
        v-for="(notification, index) in notifications"
        :key="notification.id"
        :model-value="true"
        :timeout="notification.duration"
        :color="getSnackbarColor(notification.type)"
        location="top right"
        :style="{ top: `${12 + index * 60}px` }"
        @update:model-value="() => removeNotification(notification.id)"
      >
        <div class="d-flex align-center">
          <v-icon
            :icon="getIcon(notification.type)"
            class="me-3"
            :color="getIconColor(notification.type)"
          />
          <span class="notification-message" v-html="notification.message"></span>
        </div>

        <template #actions>
          <v-btn
            icon="mdi-close"
            variant="text"
            size="small"
            @click="removeNotification(notification.id)"
          />
        </template>
      </v-snackbar>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useNotificationStore } from '@/stores/notification'
import { storeToRefs } from 'pinia'

const notificationStore = useNotificationStore()
const { notifications } = storeToRefs(notificationStore)
const { removeNotification } = notificationStore

const getSnackbarColor = (type: string): string => {
  switch (type) {
    case 'success':
      return 'success'
    case 'error':
      return 'error'
    case 'warning':
      return 'warning'
    case 'info':
      return 'info'
    default:
      return 'info'
  }
}

const getIcon = (type: string): string => {
  switch (type) {
    case 'success':
      return 'mdi-check-circle'
    case 'error':
      return 'mdi-alert-circle'
    case 'warning':
      return 'mdi-alert'
    case 'info':
      return 'mdi-information'
    default:
      return 'mdi-information'
  }
}

const getIconColor = (type: string): string => {
  switch (type) {
    case 'success':
      return 'white'
    case 'error':
      return 'white'
    case 'warning':
      return 'white'
    case 'info':
      return 'white'
    default:
      return 'white'
  }
}
</script>

<style scoped>
/* Main notification container - fixed to viewport */
/* Notification message text styling */
.notification-message {
  flex: 1;
  word-break: break-word;
  font-size: 0.875rem;
}
</style>
