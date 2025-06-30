<!-- Loading feedback to inform network operation is ongoing

  - displayed as a spinner on top of the carrot logo
  - displayed based on store's loadingstatus
  - hover displays an optional descriptive text -->

<template>
  <v-tooltip
    v-if="shouldDisplay"
    :text="loadingText"
    location="bottom"
  >
    <template v-slot:activator="{ props }">
      <v-icon
        v-bind="props"
        id="main-loader"
        icon="mdi-loading"
        size="large"
        class="loading-spinner"
      />
    </template>
  </v-tooltip>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

defineOptions({
  name: 'LoadingSpinner'
})

const userStore = useUserStore()

const shouldDisplay = computed(() => {
  return userStore.loadingStatus.shouldDisplay
})

const loadingText = computed(() => {
  return userStore.loadingStatus.text
})
</script>

<style scoped>
#main-loader {
  color: white;
  position: absolute;
  top: 0;
  left: 0;
  padding: 0.4rem;
}

.loading-spinner {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}
</style>
