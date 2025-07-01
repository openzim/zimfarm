<!-- Loading feedback to inform network operation is ongoing

  - displayed as a spinner on top of the carrot logo
  - displayed based on store's loadingstatus
  - hover displays an optional descriptive text -->

<template>
  <v-tooltip v-if="shouldDisplay" :text="loadingText" location="bottom">
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
defineOptions({
  name: 'LoadingSpinner',
})

defineProps<{
  shouldDisplay: boolean
  loadingText: string
}>()
</script>

<style scoped>
#main-loader {
  color: white;
  position: absolute;
  top: 0;
  left: 0;
  padding: 0.4rem;
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
