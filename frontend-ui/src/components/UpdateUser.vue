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
                required
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
                required
              />
            </v-col>
            <v-col cols="12" sm="6" md="4" class="d-flex align-end">
              <v-btn
                type="submit"
                color="primary"
                variant="elevated"
                :disabled="!payload"
                block
              >
                Update User
              </v-btn>
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
            <v-col cols="8" sm="8" md="6">
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
            <v-col cols="8" sm="8" md="6">
              <v-file-input
                ref="keyFile"
                v-model="keyFile"
                label="RSA Public Key"
                placeholder="Select an RSA public key file (.pub)"
                hint="Choose an RSA public key file (usually ends with .pub)"
                accept=".pub,text/plain"
                variant="outlined"
                density="compact"
                @update:model-value="keyFileSelected"
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
import { computed, onMounted, ref } from 'vue'

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
    role: string
  }
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update-user', payload: { role: typeof constants.ROLES[number]; email?: string }): void
  (e: 'change-password', password: string): void
  (e: 'add-key', keyPayload: { name: string; key: string }): void
}>()


const roles = constants.ROLES

// Reactive data
const form = ref({
  email: '',
  role: '' as typeof constants.ROLES[number],
  password: '',
})

const keyForm = ref({
  name: '',
  key: '',
})

const keyFile = ref<File | null>(null)

// Computed properties
const payload = computed(() => {
  const payload: { role: typeof constants.ROLES[number]; email?: string } = { role: form.value.role }
  if (form.value.email !== props.user.email) {
    payload.email = form.value.email
  }
  return payload
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

// Methods
const keyFileSelected = () => {
  keyForm.value.key = ''
  keyForm.value.name = ''

  const file = keyFile.value as File
  if (!file) {
    return
  }

  if (file.size > 1024) {
    notificationStore.showError(
      `File ${file.name} doesn't appear to be an RSA public file (too large). ${file.size}`
    )
    // Clear the file input on error
    keyFile.value = null
    return
  }

  const reader = new FileReader()
  reader.onerror = (evt) => {
    notificationStore.showError(
      `File ${file.name} failed to read: ${evt}`
    )
    // Clear the file input on error
    keyFile.value = null
  }
  reader.onload = (evt) => {
    const result = evt.target?.result as string
    const parts = result.trim().split(/\s/)
    if (parts.length !== 3) {
      notificationStore.showError(
        `File ${file.name} doesn't appear to be an RSA public file (format).`
      )
      // Clear the file input on error
      keyFile.value = null
      return
    }

    if (parts[0].toLowerCase().indexOf('rsa') === -1) {
      notificationStore.showError(
        `File ${file.name} doesn't appear to be an RSA public file (no RSA prefix).`
      )
      // Clear the file input on error
      keyFile.value = null
      return
    }
    keyForm.value.key = result.trim()
    keyForm.value.name = parts[2].trim()
  }
  reader.readAsText(file, 'UTF-8')
}



const addKey = () => {
  if (!keyPayload.value.name || !keyPayload.value.key) return
  emit('add-key', keyPayload.value)
}

const updateUser = () => {
  if (!(payload.value.role || payload.value.email)) return
  emit('update-user', payload.value)
}

// Lifecycle
onMounted(() => {
  if (props.user) {
    const role = constants.ROLES.includes(props.user.role as typeof constants.ROLES[number])
      ? props.user.role as typeof constants.ROLES[number]
      : 'editor'

    form.value = {
      email: props.user.email,
      role,
      password: genPassword(),
    }
  }
})
</script>
