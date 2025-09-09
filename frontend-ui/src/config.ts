import constants from '@/constants'
import httpRequest from '@/utils/httpRequest'
import type { PiniaPluginContext } from 'pinia'
import { inject } from 'vue'

export interface Config {
  ZIMFARM_WEBAPI: string
  ZIMFARM_ZIM_DOWNLOAD_URL: string
}

export const ConfigService = {
  api: (additional_headers?: object) =>
    httpRequest({
      baseURL: '/config.json',
      headers: { ...additional_headers },
    }),

  getConfig: function () {
    return this.api().get<null, Config>('')
  },
}

declare module 'pinia' {
  export interface PiniaCustomProperties {
    config: Config
  }
}

export function configPlugin({ store }: PiniaPluginContext) {
  const config = inject<Config>(constants.config)
  if (config) {
    store.config = config
  }
}

export default ConfigService.getConfig.bind(ConfigService)
