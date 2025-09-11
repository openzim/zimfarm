import constants from '@/constants'
import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Notification {
  id: string
  message: string
  type: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  timestamp: number
}

export const useNotificationStore = defineStore('notification', () => {
  const notifications = ref<Notification[]>([])

  const addNotification = (
    message: string,
    type: Notification['type'] = 'info',
    duration?: number,
  ) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`
    const notification: Notification = {
      id,
      message,
      type,
      duration: duration ?? getDefaultDuration(type),
      timestamp: Date.now(),
    }

    notifications.value.push(notification)

    // Auto-remove notification after duration
    if (notification.duration && notification.duration > 0) {
      setTimeout(() => {
        removeNotification(id)
      }, notification.duration)
    }

    return id
  }

  const removeNotification = (id: string) => {
    const index = notifications.value.findIndex((n) => n.id === id)
    if (index > -1) {
      notifications.value.splice(index, 1)
    }
  }

  const clearAllNotifications = () => {
    notifications.value = []
  }

  const getDefaultDuration = (type: Notification['type']): number => {
    switch (type) {
      case 'error':
        return constants.NOTIFICATION_ERROR_DURATION
      case 'success':
        return constants.NOTIFICATION_SUCCESS_DURATION
      default:
        return constants.NOTIFICATION_DEFAULT_DURATION
    }
  }

  // Convenience methods
  const showSuccess = (message: string, duration?: number) => {
    return addNotification(message, 'success', duration)
  }

  const showError = (message: string, duration?: number) => {
    return addNotification(message, 'error', duration)
  }

  const showWarning = (message: string, duration?: number) => {
    return addNotification(message, 'warning', duration)
  }

  const showInfo = (message: string, duration?: number) => {
    return addNotification(message, 'info', duration)
  }

  return {
    notifications,
    addNotification,
    removeNotification,
    clearAllNotifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
  }
})
