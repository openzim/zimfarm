import 'vuetify/styles'
import '@/assets/data-table.css'
import '@/assets/styles.css'
import '@mdi/font/css/materialdesignicons.css' // Ensure you are using css-loader

import { createApp } from 'vue'
// highlight.js
import hljs from 'highlight.js/lib/core'
import css from 'highlight.js/lib/languages/css'
import xml from 'highlight.js/lib/languages/xml'
import plaintext from 'highlight.js/lib/languages/plaintext'
import hljsVuePlugin from '@highlightjs/vue-plugin'
// Vuetify
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

import { createPinia } from 'pinia'
import VueMatomo from 'vue-matomo'
import VueCookies from 'vue-cookies'
import { VColorInput } from 'vuetify/labs/VColorInput'

// config
import getConfig, { configPlugin } from '@/config'

import router from '@/router'

import App from '@/App.vue'
import constants from '@/constants'

// Register highlight.js languages
hljs.registerLanguage('css', css)
hljs.registerLanguage('html', xml) // HTML uses xml language
hljs.registerLanguage('plaintext', plaintext)

const app = createApp(App)

const vuetify = createVuetify({
  components: {
    ...components,
    VColorInput,
  },
  directives,
  theme: {
    defaultTheme: 'system',
  },
})

const pinia = createPinia()

Promise.all([getConfig()]).then(([config]) => {
  app.use(vuetify)
  app.use(pinia)
  app.use(router)
  app.use(VueCookies)
  app.use(hljsVuePlugin)

  // activate matomo stats
  if (config.MATOMO_ENABLED) {
    app.use(VueMatomo, {
      host: config.MATOMO_HOST,
      siteId: config.MATOMO_SITE_ID,
      trackerFileName: config.MATOMO_TRACKER_FILE_NAME,
      router: router,
    })
  }

  // provide config app-wide
  app.provide(constants.config, config)

  // inject plugins into store
  pinia.use(configPlugin)

  app.mount('#app')
})
