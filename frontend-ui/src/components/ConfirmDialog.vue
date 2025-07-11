<template>
  <v-dialog
    v-model="isOpen"
    :max-width="maxWidth"
    persistent
  >
    <v-card>
      <v-card-title class="text-h6">
        <v-icon class="mr-2" :color="iconColor">
          {{ icon }}
        </v-icon>
        {{ title }}
      </v-card-title>

      <v-card-text class="text-body-1">
        {{ message }}
      </v-card-text>

      <v-card-actions class="pa-4">
        <v-spacer />
        <v-btn
          variant="outlined"
          @click="handleCancel"
        >
          {{ cancelText }}
        </v-btn>
        <v-btn
          :color="confirmColor"
          variant="elevated"
          @click="handleConfirm"
          :loading="loading"
        >
          {{ confirmText }}
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

// Props
interface Props {
  modelValue: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  confirmColor?: string
  icon?: string
  iconColor?: string
  maxWidth?: string | number
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Please Confirm',
  confirmText: 'YES',
  cancelText: 'NO',
  confirmColor: 'error',
  icon: 'mdi-alert-circle',
  iconColor: 'warning',
  maxWidth: 400,
  loading: false
})

// Emits
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'confirm': []
  'cancel': []
}>()

// Reactive data
const isOpen = ref(props.modelValue)

// Computed properties
const dialogValue = computed({
  get: () => isOpen.value,
  set: (value: boolean) => {
    isOpen.value = value
    emit('update:modelValue', value)
  }
})

// Methods
const handleConfirm = () => {
  emit('confirm')
  dialogValue.value = false
}

const handleCancel = () => {
  emit('cancel')
  dialogValue.value = false
}

// Watch for prop changes
watch(() => props.modelValue, (newValue) => {
  isOpen.value = newValue
})

watch(isOpen, (newValue) => {
  emit('update:modelValue', newValue)
})
</script>
