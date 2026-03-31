<template>
  <v-btn
    v-if="canRestore"
    color="success"
    variant="elevated"
    size="small"
    :loading="isRestoring"
    :disabled="isDisabled"
    @click="emit('restore-recipes')"
  >
    <v-icon size="small" class="mr-1">mdi-archive-arrow-up</v-icon>
    {{
      isRestoring
        ? restoringText
        : `Restore ${nbRecipes} selected recipe${nbRecipes !== 1 ? 's' : ''}`
    }}
  </v-btn>
</template>

<script setup lang="ts">
import { computed } from 'vue'

// Props
interface Props {
  restoringText: string | null
  canRestore: boolean
  count: number
}

const props = defineProps<Props>()

// Define emits
const emit = defineEmits<{
  'restore-recipes': string[]
}>()

// Computed properties
const nbRecipes = computed(() => props.count)
const isDisabled = computed(() => nbRecipes.value < 1)
const isRestoring = computed(() => Boolean(props.restoringText))
</script>
