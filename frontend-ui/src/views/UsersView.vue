<!-- Users management view:
  - list of users
  - user profile (TBI) -->

<template>
  <div>
    <!-- Error Message for permissions -->
    <ErrorMessage :message="error" v-if="error" />

    <!-- Content only shown if user has permission -->
    <div v-show="canReadUsers">
      <!-- Create User Form -->
      <v-card v-show="canCreateUsers" class="mb-6" flat>
        <v-card-title class="text-h6">
          <v-icon class="mr-2">mdi-account-plus</v-icon>
          Create New User
        </v-card-title>

        <v-card-text>
          <v-form @submit.prevent="createUser" ref="formRef">
            <v-row>
              <v-col cols="12" sm="6" md="3">
                <v-text-field
                  v-model="form.username"
                  label="Username"
                  placeholder="Enter username"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                  :rules="[rules.required, rules.minLength(3)]"
                />
              </v-col>

              <v-col cols="12" sm="6" md="3">
                <v-text-field
                  v-model="form.email"
                  label="Email"
                  type="email"
                  placeholder="Enter email"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                  :rules="[rules.required, rules.email]"
                />
              </v-col>

              <v-col cols="12" sm="6" md="3">
                <v-select
                  v-model="form.role"
                  :items="roles"
                  label="Role"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                  :rules="[rules.required]"
                />
              </v-col>

              <v-col cols="12" sm="6" md="3" class="d-flex align-end">
                <v-btn
                  type="submit"
                  color="primary"
                  variant="elevated"
                  :disabled="!isFormValid || isCreating"
                  :loading="isCreating"
                  block
                >
                  <v-icon class="mr-2">mdi-account-plus</v-icon>
                  Create User
                </v-btn>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>
      </v-card>

      <UsersTable
        :headers="headers"
        :users="users"
        :paginator="paginator"
        :loading="loadingStore.isLoading"
        :loading-text="loadingStore.loadingText"
        :errors="userStore.errors"
        @limit-changed="handleLimitChange"
        @load-data="loadData"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import ErrorMessage from '@/components/ErrorMessage.vue'
import UsersTable from '@/components/UsersTable.vue'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useUserStore } from '@/stores/user'
import type { User } from '@/types/user'
import { generatePassword } from '@/utils/browsers'

const roles = constants.ROLES

// Simple password generator function
const genPassword = () => generatePassword(8)

// Router and stores
const router = useRouter()
const authStore = useAuthStore()
const loadingStore = useLoadingStore()
const notificationStore = useNotificationStore()
const userStore = useUserStore()

// Form ref
const formRef = ref()

// Reactive data
const users = ref<User[]>([])
const isCreating = ref(false)
const error = ref<string | null>(null)

// Paginator state (from store)
const paginator = computed(() => userStore.paginator)

// Form data
const form = ref({
  username: '',
  email: '',
  role: 'editor' as const
})

// Computed properties
const canReadUsers = computed(() =>
  authStore.hasPermission('users', 'read')
)

const canCreateUsers = computed(() =>
  authStore.hasPermission('users', 'create')
)

const isFormValid = computed(() => {
  return form.value.username &&
         form.value.email &&
         form.value.role
})

// Table headers
const headers = [
  { title: 'Username', key: 'username' },
  { title: 'Role', key: 'role' },
  { title: 'Email', key: 'email' }
]

// Form validation rules
const rules = {
  required: (value: string) => !!value || 'This field is required',
  email: (value: string) => {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return pattern.test(value) || 'Please enter a valid email address'
  },
  minLength: (min: number) => (value: string) =>
    value.length >= min || `This field must be at least ${min} characters long`
}

// Methods
const createUser = async () => {
  const { valid } = await formRef.value?.validate()
  if (!valid) return

  isCreating.value = true
  loadingStore.startLoading('Creating user...')

  const password = genPassword()

  const response = await userStore.createUser(form.value.username, form.value.email, form.value.role, password)

  if (response) {
    // Show success notification
    notificationStore.showSuccess(
      `User "${response.username}" has been created with password "${password}".`,
      8000
    )

    // Reset form
    form.value = {
      username: '',
      email: '',
      role: 'editor' as const
    }
    formRef.value?.reset()

    // Reload users list
    await loadData(paginator.value.limit, paginator.value.skip)
  } else {
    for (const error of userStore.errors) {
      notificationStore.showError(error)
    }
  }
  isCreating.value = false
  loadingStore.stopLoading()
}

const loadData = async (limit: number, skip: number) => {
  if (!canReadUsers.value) {
    notificationStore.showError('You do not have permission to read users.')
    router.push({ name: 'home' })
    return
  }

  loadingStore.startLoading('Fetching users...')

  const response = await userStore.fetchUsers(skip, limit)
  if (response) {
    users.value = response
    userStore.savePaginatorLimit(limit)
  } else {
    for (const error of userStore.errors) {
      notificationStore.showError(error)
    }
  }
  loadingStore.stopLoading()
}

const handleLimitChange = async (newLimit: number) => {
  userStore.savePaginatorLimit(newLimit)
}

// Lifecycle
onMounted(async () => {
  if (!canReadUsers.value) {
    error.value = 'You do not have permission to view users.'
    return
  }
})
</script>
