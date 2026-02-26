<template>
  <div>
    <!-- Update User Form -->
    <v-card class="mb-4">
      <v-card-text>
        <v-form @submit.prevent="updateUser">
          <v-row class="justify-end">
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.username"
                label="Username"
                hint="Username for authentication"
                placeholder="username"
                variant="outlined"
                density="compact"
                persistent-hint
                :error-messages="usernameError ? [usernameError] : []"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.display_name"
                label="Display Name"
                hint="User's display name"
                placeholder="Display Name"
                variant="outlined"
                density="compact"
                persistent-hint
                :error-messages="displayNameError ? [displayNameError] : []"
                required
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-select
                v-model="form.role"
                :items="roles"
                label="Role"
                variant="outlined"
                density="compact"
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.idp_sub"
                label="IDP Sub (UUID)"
                hint="Identifier issued by external identity provider."
                placeholder="00000000-0000-0000-0000-000000000000"
                variant="outlined"
                density="compact"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" md="6">
              <v-btn type="submit" color="primary" variant="elevated" :disabled="!payload" block>
                Update User Profile
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

    <!-- Change Password Form (only if user has username) -->
    <v-card v-if="props.user.username" class="mb-4">
      <v-card-text>
        <v-form
          @submit.prevent="
            emit('change-password', form.password.trim() ? form.password.trim() : null)
          "
        >
          <v-row>
            <v-col cols="12" sm="8" md="6">
              <v-text-field
                v-model="form.password"
                label="Password"
                placeholder="Enter new password or leave empty to clear"
                variant="outlined"
                density="compact"
                hide-details
              />
            </v-col>
            <v-col>
              <v-btn type="submit" color="primary" variant="elevated" block>
                Change Password
              </v-btn>
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
    </v-card>

    <!-- Add SSH Key Form (only for workers with username) -->
    <v-card v-if="props.user.username && form.role === 'worker'">
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
import type { User } from '@/types/user'

// Stores and services
const notificationStore = useNotificationStore()

// Props
interface Props {
  user: User
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (
    e: 'update-user',
    payload: {
      username?: string | null
      display_name?: string
      role?: (typeof constants.ROLES)[number]
      scope?: Record<string, Record<string, boolean>>
      idp_sub?: string | null
    },
  ): void
  (e: 'change-password', password: string | null): void
  (e: 'add-key', keyPayload: { name: string; key: string }): void
}>()

const roles = constants.ROLES

// Reactive data
const form = ref({
  username: '',
  display_name: '',
  role: '' as (typeof constants.ROLES)[number],
  password: '',
  customScope: '',
  idp_sub: '',
})

const keyForm = ref({
  name: '',
  key: '',
})

const keyFile = ref<File | null>(null)
const keyInputMode = ref<'file' | 'text'>('file')

// Computed properties
const isCustomRole = computed(() => form.value.role === 'custom')

const usernameError = computed(() => {
  // If user has password or SSH keys, username cannot be empty
  if ((props.user.has_password || props.user.has_ssh_keys) && !form.value.username.trim()) {
    return 'Username is required for users with password or SSH keys'
  }
  return null
})

const displayNameError = computed(() => {
  if (!form.value.display_name.trim()) {
    return 'Display name is required'
  }
  return null
})

const payload = computed(() => {
  const result: {
    username?: string | null
    display_name?: string
    role?: (typeof constants.ROLES)[number]
    scope?: Record<string, Record<string, boolean>>
    idp_sub?: string | null
  } = {}

  // Only include username if it has changed
  if (form.value.username !== (props.user.username || '')) {
    if (usernameError.value) {
      return null
    }
    result.username = form.value.username.trim() ? form.value.username.trim() : null
  }

  if (form.value.display_name !== props.user.display_name) {
    if (displayNameError.value) {
      return null
    }
    result.display_name = form.value.display_name
  }

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
    // For non-custom roles, send the role only if it changed
    if (form.value.role !== props.user.role) {
      result.role = form.value.role
    }
  }

  // Only include idp_sub if it has changed
  if (form.value.idp_sub !== (props.user.idp_sub || '')) {
    result.idp_sub = form.value.idp_sub.trim() ? form.value.idp_sub : null
  }

  if (Object.keys(result).length === 0) {
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

const initializeForm = () => {
  if (!props.user) return

  const role = constants.ROLES.includes(props.user.role as (typeof constants.ROLES)[number])
    ? (props.user.role as (typeof constants.ROLES)[number])
    : 'editor'

  let customScope = ''
  if (role === 'custom' && props.user.scope) {
    customScope = JSON.stringify(props.user.scope, null, 2)
  }

  form.value = {
    username: props.user.username || '',
    display_name: props.user.display_name || '',
    role,
    password: genPassword(),
    customScope,
    idp_sub: props.user.idp_sub || '',
  }
}

// Watch for user changes to reinitialize form
watch(
  () => props.user,
  () => {
    initializeForm()
  },
  { deep: true },
)

onMounted(() => {
  initializeForm()
})
</script>
