import constants from '@/constants'
import httpRequest from '@/utils/httpRequest'
import type { PiniaPluginContext } from 'pinia'
import { inject } from 'vue'

export interface Config {
  ZIMFARM_WEBAPI: string
  ZIMFARM_ZIM_DOWNLOAD_URL: string
  MATOMO_ENABLED: boolean
  MATOMO_HOST: string
  MATOMO_SITE_ID: number
  MATOMO_TRACKER_FILE_NAME: string
  MONITORING_URL: string
  BLOB_MAX_SIZE: number
  KIWIX_AUTH_CLIENT_ID: string
  KIWIX_AUTH_BASE_URL: string
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
