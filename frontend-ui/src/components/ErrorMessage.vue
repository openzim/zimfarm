<!-- Alert string to display an API-generated error message instead of expected content -->

<template>
  <v-alert v-if="message" type="error" variant="tonal" closable class="mb-4">
    {{ message }}
  </v-alert>
</template>

<script setup lang="ts">
// Props
interface Props {
  message?: string | null
}

defineProps<Props>()
</script>
