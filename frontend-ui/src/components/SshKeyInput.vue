<template>
  <div>
    <v-row>
      <v-col cols="12">
        <v-tabs v-model="keyInputMode" color="primary" align-tabs="start">
          <v-tab value="file">Upload File</v-tab>
          <v-tab value="text">Enter Text</v-tab>
        </v-tabs>
      </v-col>
    </v-row>
    <v-row>
      <v-col cols="12">
        <!-- File Upload Mode -->
        <v-file-input
          v-if="keyInputMode === 'file'"
          v-model="keyFile"
          label="RSA Public Key"
          placeholder="Select an RSA public key file (.pub)"
          hint="Choose an RSA public key file (usually ends with .pub)"
          accept=".pub,text/plain"
          variant="outlined"
          density="compact"
          @update:model-value="keyFileSelected"
        />
        <!-- Text Input Mode -->
        <v-textarea
          v-else
          v-model="keyFormData.key"
          label="SSH Public Key"
          placeholder="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@hostname"
          :hint="
            keyFormData.key && !validateSSHKey(keyFormData.key)
              ? 'Invalid SSH key format'
              : 'Paste your complete SSH public key here (including the name at the end)'
          "
          :error="!!(keyFormData.key && !validateSSHKey(keyFormData.key))"
          variant="outlined"
          density="compact"
          rows="3"
          auto-grow
          @update:model-value="keyTextChanged"
        />
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useNotificationStore } from '@/stores/notification'

const props = defineProps<{
  modelValue: { name: string; key: string }
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: { name: string; key: string }): void
}>()

const notificationStore = useNotificationStore()

const keyFormData = ref({ name: props.modelValue?.name || '', key: props.modelValue?.key || '' })
const keyFile = ref<File | File[] | null>(null)
const keyInputMode = ref<'file' | 'text'>('file')

watch(
  () => keyFormData.value,
  (newVal) => {
    emit('update:modelValue', { name: newVal.name, key: newVal.key })
  },
  { deep: true },
)

const validateSSHKey = (key: string): boolean => {
  if (!key.trim()) return false
  const parts = key.trim().split(/\s+/)
  return parts.length === 3
}

const keyTextChanged = () => {
  if (!keyFormData.value.key) {
    keyFormData.value.name = ''
    return
  }
  const parts = keyFormData.value.key.trim().split(/\s+/)
  keyFormData.value.name = parts.length >= 3 ? parts[2].trim() : ''
}

const keyFileSelected = () => {
  keyFormData.value.key = ''
  keyFormData.value.name = ''

  const file = Array.isArray(keyFile.value) ? keyFile.value[0] : keyFile.value
  if (!file) return
  if (file.size > 1024) {
    notificationStore.showError(
      `File ${file.name} doesn't appear to be an RSA public file (too large). ${file.size}`,
    )
    keyFile.value = null
    return
  }
  const reader = new FileReader()
  reader.onerror = (evt) => {
    notificationStore.showError(`File ${file.name} failed to read: ${evt}`)
    keyFile.value = null
  }
  reader.onload = (evt) => {
    const result = evt.target?.result as string
    const parts = result.trim().split(/\s+/)
    if (parts.length !== 3) {
      notificationStore.showError(`File ${file.name} doesn't appear to be an SSH public file.`)
      keyFile.value = null
      return
    }
    keyFormData.value.key = result.trim()
    keyFormData.value.name = parts[2].trim()
  }
  reader.readAsText(file, 'UTF-8')
}
</script>
