<template>
  <div>
    <!-- Update User Form -->
    <v-card class="mb-4">
      <v-card-text>
        <v-form @submit.prevent="updateUser">
          <v-row>
            <v-col cols="12" sm="6" md="4">
              <v-select
                v-model="form.role"
                :items="roles"
                label="Role"
                variant="outlined"
                density="compact"
                hide-details
              />
            </v-col>
            <v-col cols="12" sm="6" md="4">
              <v-text-field
                v-model="form.email"
                type="email"
                label="Email"
                placeholder="Email"
                variant="outlined"
                density="compact"
                hide-details
              />
            </v-col>
            <v-col cols="12" sm="6" md="4" class="d-flex align-end">
              <v-btn type="submit" color="primary" variant="elevated" :disabled="!payload" block>
                Update User
              </v-btn>
            </v-col>
          </v-row>

          <v-row v-if="isCustomRole">
            <v-col cols="12">
              <v-textarea
                v-model="form.customScope"
                label="Custom Scope (JSON)"
                placeholder='{"tasks": {"read": true, "create": false}, "schedules": {"read": true}}'
                hint="Enter the custom scope as JSON. Include all namespaces (tasks, schedules, users, workers, zim, requested_tasks, offliners) with their permissions."
                persistent-hint
                :error-messages="customScopeError ? [customScopeError] : []"
                variant="outlined"
                density="compact"
                rows="10"
                auto-grow
              />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <!-- Change Password Form -->
    <v-card class="mb-4">
      <v-card-text>
        <v-form @submit.prevent="emit('change-password', form.password)">
          <v-row>
            <v-col cols="12" sm="8" md="6">
              <v-text-field
                v-model="form.password"
                label="Password (generated)"
                placeholder="Password"
                variant="outlined"
                density="compact"
                hide-details
                required
              />
            </v-col>
            <v-col>
              <v-btn
                type="submit"
                color="primary"
                variant="elevated"
                :disabled="!form.password"
                block
              >
                Change Password
              </v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <!-- Add SSH Key Form (only for workers) -->
    <v-card v-if="form.role === 'worker'">
      <v-card-text>
        <v-form @submit.prevent="addKey">
          <v-row>
            <v-col cols="12">
              <v-tabs v-model="keyInputMode" color="primary" align-tabs="start">
                <v-tab value="file">Upload File</v-tab>
                <v-tab value="text">Enter Text</v-tab>
              </v-tabs>
            </v-col>
          </v-row>

          <v-row>
            <v-col cols="12" sm="8" md="6">
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
                v-model="keyForm.key"
                label="SSH Public Key"
                placeholder="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC... user@hostname"
                :hint="
                  keyForm.key && !validateSSHKey(keyForm.key)
                    ? 'Invalid SSH key format'
                    : 'Paste your complete SSH public key here (including the name at the end)'
                "
                :error="!!(keyForm.key && !validateSSHKey(keyForm.key))"
                variant="outlined"
                density="compact"
                rows="3"
                auto-grow
                @update:model-value="keyTextChanged"
              />
            </v-col>
            <v-col>
              <v-btn
                type="submit"
                color="primary"
                variant="elevated"
                :disabled="!keyPayload.name || !keyPayload.key"
                block
              >
                Add SSH Key
              </v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import constants from '@/constants'
import { useNotificationStore } from '@/stores/notification'
import { generatePassword } from '@/utils/browsers'

// Stores and services
const notificationStore = useNotificationStore()

// Props
interface Props {
  user: {
    username: string
    email: string
    role?: string
    scope?: Record<string, Record<string, boolean>>
  }
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (
    e: 'update-user',
    payload: {
      role?: (typeof constants.ROLES)[number]
      email?: string
      scope?: Record<string, Record<string, boolean>>
    },
  ): void
  (e: 'change-password', password: string): void
  (e: 'add-key', keyPayload: { name: string; key: string }): void
}>()

const roles = constants.ROLES

// Reactive data
const form = ref({
  email: '',
  role: '' as (typeof constants.ROLES)[number],
  password: '',
  customScope: '',
})

const keyForm = ref({
  name: '',
  key: '',
})

const keyFile = ref<File | null>(null)
const keyInputMode = ref<'file' | 'text'>('file')

// Computed properties
const isCustomRole = computed(() => form.value.role === 'custom')

const payload = computed(() => {
  const result: {
    role?: (typeof constants.ROLES)[number]
    email?: string
    scope?: Record<string, Record<string, boolean>>
  } = {}

  // If role is custom, we send scope instead of role
  if (form.value.role === 'custom') {
    if (!form.value.customScope.trim()) {
      return null
    }
    try {
      const parsedScope = JSON.parse(form.value.customScope)
      result.scope = parsedScope
    } catch {
      return null
    }
  } else {
    // For non-custom roles, send the role
    result.role = form.value.role
  }

  // Only include email if it has changed
  if (form.value.email !== props.user.email) {
    result.email = form.value.email
  }

  // Return null if no changes were made
  if (!result.role && !result.scope && !result.email) {
    return null
  }

  return result
})

const customScopeError = computed(() => {
  if (form.value.role !== 'custom' || !form.value.customScope.trim()) {
    return null
  }
  try {
    JSON.parse(form.value.customScope)
    return null
  } catch {
    return 'Invalid JSON format'
  }
})

const keyPayload = computed(() => {
  const payload = { name: keyForm.value.name, key: keyForm.value.key }
  if (!payload.name.length || !payload.key.length) {
    return { name: '', key: '' }
  }
  return payload
})

// Simple password generator
const genPassword = () => generatePassword(8)

// Watchers
watch(keyInputMode, (newMode) => {
  if (newMode === 'file') {
    // Clear text form when switching to file mode
    keyForm.value.name = ''
    keyForm.value.key = ''
  } else {
    // Clear file when switching to text mode
    keyFile.value = null
  }
})

// Watch for role changes to help populate custom scope template
watch(
  () => form.value.role,
  (newRole, oldRole) => {
    if (newRole === 'custom' && oldRole !== 'custom') {
      if (!form.value.customScope.trim() && props.user.scope) {
        form.value.customScope = JSON.stringify(props.user.scope, null, 2)
      }
    }
  },
)

// Methods
const keyTextChanged = () => {
  if (!keyForm.value.key) {
    keyForm.value.name = ''
    return
  }

  const parts = keyForm.value.key.trim().split(/\s/)
  if (parts.length >= 3) {
    keyForm.value.name = parts[2].trim()
  } else {
    keyForm.value.name = ''
  }
}

const keyFileSelected = () => {
  keyForm.value.key = ''
  keyForm.value.name = ''

  const file = keyFile.value as File
  if (!file) {
    return
  }

  if (file.size > 1024) {
    notificationStore.showError(
      `File ${file.name} doesn't appear to be an RSA public file (too large). ${file.size}`,
    )
    // Clear the file input on error
    keyFile.value = null
    return
  }

  const reader = new FileReader()
  reader.onerror = (evt) => {
    notificationStore.showError(`File ${file.name} failed to read: ${evt}`)
    // Clear the file input on error
    keyFile.value = null
  }
  reader.onload = (evt) => {
    const result = evt.target?.result as string
    const parts = result.trim().split(/\s/)
    if (parts.length !== 3) {
      notificationStore.showError(`File ${file.name} doesn't appear to be an SSH public file.`)
      // Clear the file input on error
      keyFile.value = null
      return
    }

    keyForm.value.key = result.trim()
    keyForm.value.name = parts[2].trim()
  }
  reader.readAsText(file, 'UTF-8')
}

const validateSSHKey = (key: string): boolean => {
  if (!key.trim()) return false

  const parts = key.trim().split(/\s/)
  if (parts.length !== 3) return false

  return true
}

const addKey = () => {
  if (!keyPayload.value.name || !keyPayload.value.key) return

  // Validate SSH key format for text input
  if (keyInputMode.value === 'text' && !validateSSHKey(keyForm.value.key)) {
    notificationStore.showError(
      'Invalid SSH key format. Please ensure it starts with a valid key type (ssh-rsa, ssh-ed25519, etc.)',
    )
    return
  }

  emit('add-key', keyPayload.value)
}

const updateUser = () => {
  if (!payload.value) return
  emit('update-user', payload.value)
}

// Lifecycle
onMounted(() => {
  if (props.user) {
    const role = constants.ROLES.includes(props.user.role as (typeof constants.ROLES)[number])
      ? (props.user.role as (typeof constants.ROLES)[number])
      : 'editor'

    // Initialize custom scope with user's current scope if role is custom
    let customScope = ''
    if (role === 'custom' && props.user.scope) {
      customScope = JSON.stringify(props.user.scope, null, 2)
    }

    form.value = {
      email: props.user.email,
      role,
      password: genPassword(),
      customScope,
    }
  }
})
</script>
