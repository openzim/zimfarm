<!-- Users management view:
  - list of users
  - user profile (TBI) -->

<template>
  <div>
    <!-- Error Message for permissions -->
    <ErrorMessage :message="error" v-if="error" />

    <!-- Content only shown if user has permission -->
    <div v-show="canReadUsers">
      <v-card class="mb-4" flat>
        <v-card-text>
          <v-row align="center">
            <v-col cols="12" sm="8">
              <v-text-field
                v-model="searchUsername"
                label="Search user"
                placeholder="Enter username to search"
                variant="outlined"
                density="compact"
                prepend-inner-icon="mdi-magnify"
                clearable
                hide-details
                @blur="handleSearchChange"
                @keyup.enter="handleSearchChange"
                @click:clear="handleSearchChange"
              />
            </v-col>
            <v-col cols="12" sm="4">
              <v-btn
                v-if="canCreateUsers"
                color="primary"
                variant="elevated"
                block
                @click="showCreateDialog = true"
              >
                <v-icon class="mr-2">mdi-account-plus</v-icon>
                Create User
              </v-btn>
            </v-col>
          </v-row>
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
      />
    </div>

    <!-- Create User Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="600" persistent>
      <v-card>
        <v-card-title class="text-h6 bg-primary">
          <v-icon class="mr-2">mdi-account-plus</v-icon>
          Create New User
        </v-card-title>

        <v-card-text class="pt-4">
          <v-form @submit.prevent="createUser" ref="formRef">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="form.username"
                  label="Username"
                  placeholder="Enter username"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                  :validate-on="'blur'"
                  :rules="[rules.required, rules.minLength(3)]"
                />
              </v-col>

              <v-col cols="12">
                <v-text-field
                  v-model="form.email"
                  label="Email"
                  type="email"
                  placeholder="Enter email"
                  variant="outlined"
                  density="compact"
                  :validate-on="'blur'"
                  hide-details="auto"
                  :rules="[rules.required, rules.email]"
                />
              </v-col>

              <v-col cols="12">
                <v-select
                  v-model="form.role"
                  :items="roles"
                  label="Role"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                  :validate-on="'blur'"
                  :rules="[rules.required]"
                />
              </v-col>

              <v-col cols="12">
                <v-text-field
                  v-model="form.password"
                  label="Password"
                  placeholder="Enter password or generate one"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                  :type="showPassword ? 'text' : 'password'"
                  :rules="[rules.required, rules.minLength(8)]"
                >
                  <template #append-inner>
                    <v-btn
                      icon
                      size="small"
                      variant="text"
                      @click="showPassword = !showPassword"
                      tabindex="-1"
                    >
                      <v-icon>{{ showPassword ? 'mdi-eye-off' : 'mdi-eye' }}</v-icon>
                    </v-btn>
                  </template>
                </v-text-field>
              </v-col>

              <v-col cols="12">
                <v-btn variant="outlined" color="primary" block @click="generateNewPassword">
                  <v-icon class="mr-2">mdi-refresh</v-icon>
                  Generate New Password
                </v-btn>
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeCreateDialog" :disabled="isCreating"> Cancel </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            :disabled="!isFormValid || isCreating"
            :loading="isCreating"
            @click="createUser"
          >
            <v-icon class="mr-2">mdi-account-plus</v-icon>
            Create User
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

import ErrorMessage from '@/components/ErrorMessage.vue'
import UsersTable from '@/components/UsersTable.vue'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useUserStore } from '@/stores/user'
import type { User } from '@/types/user'
import { generatePassword } from '@/utils/browsers'

const roles = constants.ROLES.filter((role) => role !== 'custom')

// Simple password generator function
const genPassword = () => generatePassword(8)

// Router and stores
const router = useRouter()
const route = useRoute()
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
const searchUsername = ref<string>('')
const showCreateDialog = ref(false)

const paginator = ref({
  page: Number(route.query.page) || 1,
  page_size: userStore.defaultLimit,
  skip: 0,
  limit: userStore.defaultLimit,
  count: 0,
})

// Form data
const form = ref({
  username: '',
  email: '',
  role: 'editor' as const,
  password: '',
})

const showPassword = ref(false)

// Computed properties
const canReadUsers = computed(() => authStore.hasPermission('users', 'read'))

const canCreateUsers = computed(() => authStore.hasPermission('users', 'create'))

const isFormValid = computed(() => {
  return form.value.username && form.value.email && form.value.role && form.value.password
})

// Table headers
const headers = [
  { title: 'Username', key: 'username', sortable: false },
  { title: 'Role', key: 'role', sortable: false },
  { title: 'Email', key: 'email', sortable: false },
]

// Form validation rules
const rules = {
  required: (value: string) => !!value || 'This field is required',
  email: (value: string) => {
    const pattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return pattern.test(value) || 'Please enter a valid email address'
  },
  minLength: (min: number) => (value: string) =>
    value.length >= min || `This field must be at least ${min} characters long`,
}

// Methods
const createUser = async () => {
  const { valid } = await formRef.value?.validate()
  if (!valid) return

  isCreating.value = true
  loadingStore.startLoading('Creating user...')

  const response = await userStore.createUser(
    form.value.username,
    form.value.email,
    form.value.role,
    form.value.password,
  )

  if (response) {
    // Show success notification
    notificationStore.showSuccess(
      `User "${response.username}" has been created with password "${form.value.password}".`,
      8000,
    )

    // Reset form
    form.value = {
      username: '',
      email: '',
      role: 'editor' as const,
      password: '',
    }
    formRef.value?.reset()
    showPassword.value = false

    showCreateDialog.value = false

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

  const response = await userStore.fetchUsers(skip, limit, searchUsername.value || undefined)
  if (response) {
    users.value = response
    paginator.value = { ...userStore.paginator }
    userStore.savePaginatorLimit(limit)
  } else {
    for (const error of userStore.errors) {
      notificationStore.showError(error)
    }
  }
  loadingStore.stopLoading()
}

const handleSearchChange = async () => {
  const query: Record<string, string> = {}
  if (searchUsername.value) {
    query.name = searchUsername.value
  }
  router.push({
    query: Object.keys(query).length > 0 ? query : undefined,
  })
}

const closeCreateDialog = () => {
  showCreateDialog.value = false
  form.value = {
    username: '',
    email: '',
    role: 'editor' as const,
    password: '',
  }
  formRef.value?.reset()
  showPassword.value = false
}

const generateNewPassword = () => {
  form.value.password = genPassword()
  showPassword.value = true
}

const handleLimitChange = async (newLimit: number) => {
  userStore.savePaginatorLimit(newLimit)
  if (paginator.value.page != 1) {
    paginator.value = {
      ...paginator.value,
      limit: newLimit,
      page: 1,
      skip: 0,
    }
  } else {
    await loadData(newLimit, 0)
  }
}

// Lifecycle
onMounted(async () => {
  if (!canReadUsers.value) {
    error.value = 'You do not have permission to view users.'
    return
  }
})

// Watch for dialog open to generate password
watch(showCreateDialog, (newValue) => {
  if (newValue) {
    generateNewPassword()
  }
})

watch(
  () => router.currentRoute.value.query,
  async () => {
    const query = router.currentRoute.value.query
    let page = 1
    if (query.page && typeof query.page === 'string') {
      const parsedPage = parseInt(query.page, 10)
      if (!isNaN(parsedPage) && parsedPage > 1) {
        page = parsedPage
      }
    }
    // Sync search from URL
    if (query.name && typeof query.name === 'string') {
      searchUsername.value = query.name
    } else {
      searchUsername.value = ''
    }
    const newSkip = (page - 1) * paginator.value.limit
    await loadData(paginator.value.limit, newSkip)
  },
  { deep: true, immediate: true },
)
</script>
