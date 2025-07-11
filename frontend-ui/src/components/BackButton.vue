<!-- Simple back button to mimic browser back -->
<template>
  <v-btn
    color="secondary"
    size="small"
    variant="outlined"
    prepend-icon="mdi-arrow-left-circle"
    @click="goBack"
  >
    Go Back
  </v-btn>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const hasHistory = computed(() => window.history.length > 1)

const goBack = () => {
  if (hasHistory.value) {
    router.back()
  }
}
</script>
