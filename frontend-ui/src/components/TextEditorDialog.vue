<template>
  <v-dialog v-model="isOpen" max-width="600" persistent scrollable>
    <v-card>
      <v-card-title class="text-h6 bg-primary">
        <v-icon class="mr-2">{{ iconName }}</v-icon>
        Edit {{ fileTypeLabel }} File
        <v-spacer />
        <v-btn icon="mdi-close" variant="text" @click="handleCancel" size="small" />
      </v-card-title>

      <div class="pa-4">
        <CodeEditor
          v-model="editedContent"
          :file-type="fileType"
          :placeholder="`Enter your ${fileTypeLabel} code here...`"
          height="500px"
        />
      </div>

      <div v-if="errorMessage" class="text-error py-2 px-4">
        <v-icon size="small" class="mr-1">mdi-alert-circle</v-icon>
        {{ errorMessage }}
      </div>

      <div class="pa-4">
        <v-textarea
          :model-value="comment"
          @update:model-value="$emit('update:comment', $event)"
          label="Comment (optional)"
          hint="Add a comment about this file"
          variant="outlined"
          density="compact"
          rows="2"
          persistent-hint
        />
      </div>

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
import { ref, watch, computed } from 'vue'
import CodeEditor from '@/components/CodeEditor.vue'

interface Props {
  modelValue: boolean
  textContent: string
  fileType?: 'css' | 'html' | 'txt'
  loading?: boolean
  comment?: string
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  fileType: 'css',
  comment: '',
})

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'update:comment': [value: string]
  save: [content: string]
  cancel: []
}>()

const isOpen = ref(props.modelValue)
const editedContent = ref(props.textContent)
const errorMessage = ref('')

const iconName = computed(() => {
  switch (props.fileType) {
    case 'html':
      return 'mdi-language-html5'
    case 'css':
      return 'mdi-language-css3'
    case 'txt':
      return 'mdi-file-document-outline'
    default:
      return 'mdi-file-document-outline'
  }
})

const fileTypeLabel = computed(() => {
  switch (props.fileType) {
    case 'html':
      return 'HTML'
    case 'css':
      return 'CSS'
    case 'txt':
      return 'Text'
    default:
      return 'Text'
  }
})

// Watch for prop changes
watch(
  () => props.modelValue,
  (newValue) => {
    isOpen.value = newValue
    if (newValue) {
      // Reset content when dialog opens
      editedContent.value = props.textContent
      errorMessage.value = ''
    }
  },
)

watch(
  () => props.textContent,
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
