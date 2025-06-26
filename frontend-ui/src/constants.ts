import type { InjectionKey } from 'vue'
import type { Config } from '@/config'

export default {
  config: Symbol() as InjectionKey<Config>,
}
