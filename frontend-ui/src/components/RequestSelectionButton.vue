<template>
  <v-btn
    :color="isDisabled ? undefined : 'primary'"
    variant="elevated"
    size="small"
    class="mr-2"
    :loading="isRequesting"
    :disabled="isDisabled"
    @click="emit('request-tasks')"
  >
    <v-tooltip activator="parent" location="top">Request with default options</v-tooltip>
    <v-icon size="small" class="mr-1">mdi-rocket-launch</v-icon>
    {{
      isRequesting ? requestingText : `Request ${count} selected recipe${count !== 1 ? 's' : ''}`
    }}
  </v-btn>

  <v-btn
    :color="isDisabled ? undefined : 'primary'"
    variant="outlined"
    size="small"
    :disabled="isDisabled || isRequesting"
    @click="emit('custom-request-tasks')"
  >
    <v-tooltip activator="parent" location="top">Choose worker, priority and flags</v-tooltip>
    <v-icon size="small" class="mr-1">mdi-tune-variant</v-icon>
    Custom request
  </v-btn>
</template>

<script setup lang="ts">
import constants from '@/constants'
import { computed } from 'vue'

interface Props {
  requestingText: string | null
  count: number
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'request-tasks': []
  'custom-request-tasks': []
}>()

const isDisabled = computed(
  () => props.count < 1 || props.count > constants.MAX_RECIPES_IN_SELECTION_REQUEST,
)
const isRequesting = computed(() => Boolean(props.requestingText))
</script>
