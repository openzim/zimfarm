import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import vueJsx from '@vitejs/plugin-vue-jsx'
import { defineConfig } from 'vite'
import vueDevTools from 'vite-plugin-vue-devtools'
import vuetify from 'vite-plugin-vuetify'

import { BREAKPOINTS } from './src/constants/breakpoints.ts'

const sassBreakpoints = Object.entries(BREAKPOINTS)
  .map(([name, value]) => `'${name}': ${value}px`)
  .join(', ')

const vuetifySettingsOverride = `@use 'vuetify/settings' as zimfarm-settings with ($grid-breakpoints: (${sassBreakpoints}), $button-text-transform: uppercase);\n`

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), vueJsx(), vueDevTools(), vuetify({ styles: 'sass' })],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  css: {
    preprocessorOptions: {
      sass: {
        additionalData: vuetifySettingsOverride,
      },
      scss: {
        additionalData: vuetifySettingsOverride,
      },
    },
  },
  optimizeDeps: {
    // Keep Vuetify's overlay modules pre-bundled together so that the internal
    // overlay stack is shared and nested overlays stack above dialogs in dev mode.
    include: [
      'vuetify/components/VOverlay',
      'vuetify/components/VDialog',
      'vuetify/components/VMenu',
      'vuetify/components/VSelect',
      'vuetify/components/VTooltip',
    ],
  },
})
