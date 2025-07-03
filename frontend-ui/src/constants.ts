import type { Config } from '@/config'
import type { InjectionKey } from 'vue'

export default {
  config: Symbol() as InjectionKey<Config>,
  TOKEN_COOKIE_NAME: 'auth',
  TOKEN_COOKIE_EXPIRY: '6m', // 6 months
  COOKIE_LIFETIME_EXPIRY: '10y', // 10 years
  TASKS_LOAD_SCHEDULES_CHUNK_SIZE: 5,
}
