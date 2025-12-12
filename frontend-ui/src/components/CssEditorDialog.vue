<template>
  <v-dialog v-model="isOpen" max-width="600" persistent scrollable>
    <v-card>
      <v-card-title class="text-h6 bg-primary">
        <v-icon class="mr-2">mdi-language-css3</v-icon>
        Edit CSS File
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" @click="handleCancel" size="small" />
      </v-card-title>

      <v-card-text class="pa-4">
        <v-textarea
          v-model="editedContent"
          variant="outlined"
          auto-grow
          :rows="20"
          placeholder="Enter your CSS code here..."
          hide-details
          spellcheck="false"
        />
      </v-card-text>

      <v-card-text v-if="errorMessage" class="text-error py-2">
        <v-icon size="small" class="mr-1">mdi-alert-circle</v-icon>
        {{ errorMessage }}
      </v-card-text>

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn variant="outlined" @click="handleCancel"> Cancel </v-btn>
        <v-btn color="primary" variant="elevated" @click="handleDone" :loading="loading">
          Done
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface Props {
  modelValue: boolean
  cssContent: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  save: [content: string]
  cancel: []
}>()

const isOpen = ref(props.modelValue)
const editedContent = ref(props.cssContent)
const errorMessage = ref('')

// Watch for prop changes
watch(
  () => props.modelValue,
  (newValue) => {
    isOpen.value = newValue
    if (newValue) {
      // Reset content when dialog opens
      editedContent.value = props.cssContent
      errorMessage.value = ''
    }
  },
)

watch(
  () => props.cssContent,
  (newValue) => {
    if (isOpen.value) {
      editedContent.value = newValue
    }
  },
)

watch(isOpen, (newValue) => {
  emit('update:modelValue', newValue)
})

const handleDone = () => {
  errorMessage.value = ''
  emit('save', editedContent.value)
}

const handleCancel = () => {
  errorMessage.value = ''
  emit('cancel')
  isOpen.value = false
}
</script>
