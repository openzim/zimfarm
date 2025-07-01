<template>
  <main>
    <h1>Schedule Detail {{ schedule_name }}</h1>
  </main>
</template>

<script setup lang="ts">
defineProps<{
  schedule_name: string
}>()
</script>
