<template>
  <div>
    <h1>Task Detail {{ id }}</h1>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  id: string
}>()

</script>
