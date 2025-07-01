import '@mdi/font/css/materialdesignicons.css' // Ensure you are using css-loader

import { createApp } from 'vue'
// Vuetify
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import 'vuetify/styles'

import { createPinia } from 'pinia'
import VueCookies from 'vue-cookies'

// config
import getConfig, { configPlugin } from './config'

import router from '@/router'

import App from '@/App.vue'
import constants from './constants'

const app = createApp(App)

const vuetify = createVuetify({
  components,
  directives,
})

const pinia = createPinia()

Promise.all([getConfig()]).then(([config]) => {
  app.use(vuetify)
  app.use(pinia)
  app.use(router)
  app.use(VueCookies)

  // provide config app-wide
  app.provide(constants.config, config)

  // inject plugins into store
  pinia.use(configPlugin)

  app.mount('#app')
})
