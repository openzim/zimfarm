<template>
  <v-btn
    v-if="canRequestTasks"
    color="primary"
    variant="elevated"
    size="small"
    :loading="isRequesting"
    :disabled="isDisabled"
    @click="emit('fetch-schedules')"
  >
    <v-icon size="small" class="mr-1">mdi-plus</v-icon>
    {{ isRequesting ? requestingText : `Request those ${nbSchedules} recipes` }}
  </v-btn>
</template>

<script setup lang="ts">
import constants from '@/constants'
import { computed, ref } from 'vue'

// Props
interface Props {
  requestingText: string | null
  canRequestTasks: boolean
  count: number
}


const props = defineProps<Props>()

// Define emits
const emit = defineEmits<{
  'fetch-schedules': []
}>()


const requestingText = ref<string | null>(props.requestingText)

// Computed properties
const nbSchedules = computed(() => props.count)
const isDisabled = computed(() =>
  nbSchedules.value < 1 || nbSchedules.value > constants.MAX_SCHEDULES_IN_SELECTION_REQUEST
)
const isRequesting = computed(() => Boolean(requestingText.value))
</script>
