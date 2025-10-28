<!-- User management view:
  - Detail
  - change role
  - change password -->

<template>
  <v-container>
    <!-- Loading state when data hasn't been loaded yet -->
    <div v-if="!dataLoaded && loadingStore.isLoading" class="text-center pa-8">
      <v-progress-circular indeterminate size="64" />
      <div class="mt-4 text-body-1">{{ loadingStore.loadingText }}</div>
    </div>

    <!-- Content only shown when data is loaded -->
    <div v-if="dataLoaded">
      <v-row>
        <v-col cols="12">
          <h2 class="text-h4 mb-4">
            <code>{{ username }}</code>
            <span v-if="user">
              (<code>{{ user.role }}</code
              >)</span
            >
          </h2>

          <div v-if="!error && user">
            <!-- Tabs -->
            <v-tabs v-model="selectedTab" color="primary" class="mb-4">
              <v-tab value="details" :to="{ name: 'user-detail', params: { username: username } }">
                Profile
              </v-tab>
              <v-tab
                value="edit"
                :to="{
                  name: 'user-detail-tab',
                  params: { username: username, selectedTab: 'edit' },
                }"
              >
                Edit
              </v-tab>
              <v-tab
                v-if="canDeleteUser"
                value="delete"
                :to="{
                  name: 'user-detail-tab',
                  params: { username: username, selectedTab: 'delete' },
                }"
                color="error"
              >
                Delete
              </v-tab>
            </v-tabs>

            <!-- Tab Content -->
            <v-window v-model="selectedTab">
              <!-- Details Tab -->
              <v-window-item value="details">
                <v-card flat>
                  <v-card-text>
                    <!-- Email -->
                    <p v-if="user.email" class="mb-4">
                      <a :href="'mailto:' + user.email" class="text-decoration-none text-primary">
                        {{ user.email }}
                      </a>
                    </p>

                    <!-- Permissions List -->
                    <v-card class="mb-4" variant="outlined">
                      <v-card-title class="text-subtitle-1">
                        <v-icon class="mr-2">mdi-shield-account</v-icon>
                        Permissions
                      </v-card-title>
                      <v-card-text>
                        <div
                          v-if="Object.keys(scope).length === 0"
                          class="text-body-2 text-medium-emphasis"
                        >
                          No permissions assigned
                        </div>
                        <v-list v-else density="compact" class="pa-0">
                          <v-list-item
                            v-for="(namespacePermissions, namespace) in scope"
                            :key="namespace"
                          >
                            <template #prepend>
                              <v-icon color="primary" size="small">
                                {{ getNamespaceIcon(namespace) }}
                              </v-icon>
                            </template>

                            <v-list-item-title class="text-body-1 font-weight-medium">
                              {{ formatNamespaceName(namespace) }}
                            </v-list-item-title>

                            <v-list-item-subtitle>
                              <div class="d-flex flex-wrap ga-1 mt-2">
                                <v-chip
                                  v-for="permissionName in getAllPermissionsForNamespace(namespace)"
                                  :key="permissionName"
                                  :color="
                                    namespacePermissions[permissionName] ? 'primary' : 'dark-grey'
                                  "
                                  :variant="
                                    namespacePermissions[permissionName] ? 'flat' : 'outlined'
                                  "
                                  size="x-small"
                                  class="text-caption text-uppercase"
                                >
                                  {{ formatPermissionName(permissionName) }}
                                </v-chip>
                              </div>
                            </v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>

                    <!-- SSH Keys Table -->
                    <v-card v-if="user.ssh_keys && user.ssh_keys.length" variant="outlined">
                      <v-card-title class="text-subtitle-1">
                        <v-icon class="mr-2">mdi-key</v-icon>
                        SSH Keys
                      </v-card-title>
                      <v-card-text>
                        <v-table density="compact">
                          <thead>
                            <tr>
                              <th>SSH Key</th>
                              <th>Fingerprint</th>
                              <th v-if="canSSHKeyUsers">Actions</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr v-for="sshKey in user.ssh_keys" :key="sshKey.name">
                              <td>{{ sshKey.name }}</td>
                              <td>
                                <code>{{ sshKey.fingerprint }}</code>
                              </td>
                              <td v-if="canSSHKeyUsers">
                                <v-btn
                                  color="error"
                                  size="small"
                                  variant="outlined"
                                  @click="confirmDelete(sshKey)"
                                >
                                  <v-icon size="small" class="mr-1">mdi-delete</v-icon>
                                  Delete
                                </v-btn>
                              </td>
                            </tr>
                          </tbody>
                        </v-table>
                      </v-card-text>
                    </v-card>
                  </v-card-text>
                </v-card>
              </v-window-item>

              <!-- Edit Tab -->
              <v-window-item value="edit">
                <UpdateUser
                  :user="user"
                  v-if="user"
                  @update-user="updateUser"
                  @change-password="changePassword"
                  @add-key="addKey"
                />
              </v-window-item>

              <!-- Delete Tab -->
              <v-window-item value="delete">
                <DeleteItem
                  :name="user.username"
                  description="user account"
                  property="username"
                  @delete-item="deleteUser"
                />
              </v-window-item>
            </v-window>
          </div>

          <!-- Error Message -->
          <ErrorMessage :message="error" v-if="error" />
        </v-col>
      </v-row>

      <!-- Confirmation Dialog -->
      <ConfirmDialog
        v-model="showConfirmDialog"
        :title="confirmDialogTitle"
        :message="confirmDialogMessage"
        confirm-text="DELETE"
        cancel-text="CANCEL"
        confirm-color="error"
        icon="mdi-delete"
        icon-color="error"
        @confirm="handleConfirmDelete"
        @cancel="handleCancelDelete"
      />
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DeleteItem from '@/components/DeleteItem.vue'
import ErrorMessage from '@/components/ErrorMessage.vue'
import UpdateUser from '@/components/UpdateUser.vue'
import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useUserStore } from '@/stores/user'
import type { UserWithSshKeys } from '@/types/user'

// Props
interface Props {
  username: string
  selectedTab?: string
}

const props = withDefaults(defineProps<Props>(), {
  selectedTab: 'details',
})

// Route and stores
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loadingStore = useLoadingStore()
const notificationStore = useNotificationStore()
const userStore = useUserStore()

// Confirmation dialog state
const showConfirmDialog = ref(false)
const confirmDialogTitle = ref('')
const confirmDialogMessage = ref('')
let pendingSshKey: { name: string; fingerprint: string } | null = null

// Reactive data
const error = ref<string | null>(null)
const user = ref<UserWithSshKeys | null>(null)
const selectedTab = ref(props.selectedTab)
const dataLoaded = ref(false)

// Computed properties
const scope = computed(() => user.value?.scope || {})

const canDeleteUser = computed(() => authStore.hasPermission('users', 'delete'))

const canSSHKeyUsers = computed(() => authStore.hasPermission('users', 'ssh_keys'))

const getNamespaceIcon = (namespace: string): string => {
  const iconMap: Record<string, string> = {
    tasks: 'mdi-clipboard-list',
    schedules: 'mdi-calendar-clock',
    requested_tasks: 'mdi-clipboard-check',
    users: 'mdi-account-group',
    workers: 'mdi-server',
    zim: 'mdi-package-variant',
  }
  return iconMap[namespace] || 'mdi-folder'
}

const formatNamespaceName = (namespace: string): string => {
  const nameMap: Record<string, string> = {
    tasks: 'Tasks',
    schedules: 'Schedules',
    requested_tasks: 'Requested Tasks',
    users: 'Users',
    workers: 'Workers',
    zim: 'ZIM Files',
  }
  return nameMap[namespace] || namespace.charAt(0).toUpperCase() + namespace.slice(1)
}

const formatPermissionName = (permission: string): string => {
  const nameMap: Record<string, string> = {
    read: 'Read',
    create: 'Create',
    update: 'Update',
    delete: 'Delete',
    cancel: 'Cancel',
    archive: 'Archive',
    request: 'Request',
    unrequest: 'Unrequest',
    secrets: 'Secrets',
    change_password: 'Change Password',
    ssh_keys: 'SSH Keys',
    upload: 'Upload',
    checkin: 'Check-in',
  }
  return nameMap[permission] || permission.charAt(0).toUpperCase() + permission.slice(1)
}

const getAllPermissionsForNamespace = (namespace: string): string[] => {
  if (scope.value[namespace]) {
    return Object.keys(scope.value[namespace])
  }
  return []
}

// Methods
const confirmDelete = (sshKey: { name: string; fingerprint: string }) => {
  pendingSshKey = sshKey
  confirmDialogTitle.value = 'Delete SSH Key'
  confirmDialogMessage.value = `Are you sure you want to delete SSH Key "${sshKey.name}"?`
  showConfirmDialog.value = true
}

const handleConfirmDelete = async () => {
  if (pendingSshKey) {
    await deleteKey(pendingSshKey)
    pendingSshKey = null
  }
}

const handleCancelDelete = () => {
  pendingSshKey = null
}

const deleteKey = async (sshKey: { name: string; fingerprint: string }) => {
  loadingStore.startLoading('Deleting key...')

  try {
    const success = await userStore.deleteSshKey(props.username, sshKey.fingerprint)
    if (success) {
      notificationStore.showSuccess(`Key Removed! SSH Key "${sshKey.name}" has been removed.`)
      await loadUser()
    } else {
      for (const error of userStore.errors) {
        notificationStore.showError(error)
      }
    }
  } catch (err) {
    console.error('Error deleting SSH key:', err)
    notificationStore.showError('Failed to delete SSH key')
  } finally {
    loadingStore.stopLoading()
  }
}

const changePassword = async (password: string) => {
  loadingStore.startLoading('Changing password...')

  const success = await userStore.changePassword(props.username, { new: password })
  if (success) {
    notificationStore.showSuccess(
      `Password for ${props.username} has been changed to ${password}.`,
      10000,
    )
  } else {
    for (const error of userStore.errors) {
      notificationStore.showError(error)
    }
  }
  loadingStore.stopLoading()
}

const updateUser = async (payload: {
  role?: string
  email?: string
  scope?: Record<string, Record<string, boolean>>
}) => {
  if (!(payload.role || payload.email || payload.scope)) return

  loadingStore.startLoading('updating user…')
  const success = await userStore.updateUser(props.username, payload)
  if (success) {
    notificationStore.showSuccess(`User account ${props.username} has been updated.`)
    router.push({ name: 'users-list' })
  } else {
    for (const error of userStore.errors) {
      notificationStore.showError(error)
    }
  }
  loadingStore.stopLoading()
}

const addKey = async (payload: { name: string; key: string }) => {
  loadingStore.startLoading('Adding key...')
  const success = await userStore.addSshKey(props.username, payload)
  if (success) {
    notificationStore.showSuccess(`Key added! SSH Key "${payload.name}" has been added.`)
    router.push({ name: 'users-list' })
  } else {
    for (const error of userStore.errors) {
      notificationStore.showError(error)
    }
  }
  loadingStore.stopLoading()
}

const deleteUser = async () => {
  loadingStore.startLoading('Deleting user...')
  const success = await userStore.deleteUser(props.username)
  if (success) {
    notificationStore.showSuccess(`User account ${props.username} has been deleted.`)
    router.push({ name: 'users-list' })
  } else {
    for (const error of userStore.errors) {
      notificationStore.showError(error)
    }
  }
  loadingStore.stopLoading()
}

const loadUser = async () => {
  loadingStore.startLoading('Fetching user...')

  try {
    const userData = await userStore.fetchUser(props.username)
    if (userData) {
      error.value = null
      user.value = userData
      dataLoaded.value = true
    } else {
      error.value = 'Failed to load user data'
      for (const err of userStore.errors) {
        notificationStore.showError(err)
      }
    }
  } catch (err) {
    console.error('Error loading user:', err)
    error.value = 'Failed to load user data'
  } finally {
    loadingStore.stopLoading()
  }
}

// Watch for route changes to update selected tab
watch(
  () => route.params.selectedTab,
  (newTab) => {
    if (newTab && typeof newTab === 'string') {
      selectedTab.value = newTab
    }
  },
  { immediate: true },
)

// Lifecycle
onMounted(async () => {
  loadingStore.startLoading('Fetching user...')
  await loadUser()
  loadingStore.stopLoading()
})
</script>
