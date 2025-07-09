import type { Config } from '@/config'
import type { InjectionKey } from 'vue'

export default {
  config: Symbol() as InjectionKey<Config>,
  TOKEN_COOKIE_NAME: 'auth',
  TOKEN_COOKIE_EXPIRY: '6m', // 6 months
  COOKIE_LIFETIME_EXPIRY: '10y', // 10 years
  TASKS_LOAD_SCHEDULES_DELAY: 100,
  MAX_SCHEDULES_IN_SELECTION_REQUEST: 200,
  // Notification constants
  NOTIFICATION_DEFAULT_DURATION: 5000, // 5 seconds
  NOTIFICATION_ERROR_DURATION: 8000, // 8 seconds for errors
  NOTIFICATION_SUCCESS_DURATION: 3000, // 3 seconds for success
  // User roles
  ROLES: ['admin', 'editor', 'editor-requester', 'manager', 'processor', 'worker'] as const,
}
