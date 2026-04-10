<template>
  <v-card class="mb-4">
    <v-card-text>
      <v-form @submit.prevent="submitForm">
        <v-row>
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
        </v-row>

        <template v-if="hasLocalAuth">
          <v-divider class="my-4"></v-divider>
          <div class="text-subtitle-1 mb-2 font-weight-bold">Local Authentication</div>
          <v-row>
            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.username"
                label="Username"
                hint="Username for local authentication"
                placeholder="username"
                variant="outlined"
                density="compact"
                persistent-hint
                :error-messages="usernameError ? [usernameError] : []"
              />
            </v-col>

            <v-col cols="12" md="6">
              <v-text-field
                v-model="form.password"
                label="New Password"
                hint="Password for local authentication (leave unchanged to keep current, clear to remove)"
                placeholder="Enter new password"
                variant="outlined"
                density="compact"
                persistent-hint
                append-inner-icon="mdi-refresh"
                @click:append-inner="generateNewPassword"
              />
            </v-col>
          </v-row>
        </template>

        <template v-if="hasOauth">
          <v-divider class="my-4"></v-divider>
          <div class="text-subtitle-1 mb-2 font-weight-bold">External Identity Provider</div>
          <v-row>
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
          </v-row>
        </template>

        <v-row v-if="isCustomRole">
          <v-col cols="12">
            <v-textarea
              v-model="form.customScope"
              label="Custom Scope (JSON)"
              placeholder='{"tasks": {"read": true, "create": false}, "recipes": {"read": true}}'
              hint="Enter the custom scope as JSON. Include all namespaces (tasks, recipes, accounts, workers, zim, requested_tasks, offliners) with their permissions."
              persistent-hint
              :error-messages="customScopeError ? [customScopeError] : []"
              variant="outlined"
              density="compact"
              rows="10"
              auto-grow
            />
          </v-col>
        </v-row>

        <v-row class="mt-4">
          <v-col cols="12">
            <v-btn type="submit" color="primary" variant="elevated" :disabled="!hasChanges" block>
              Update User Profile
            </v-btn>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref, watch } from 'vue'

import type { Config } from '@/config'
import constants from '@/constants'
import { generatePassword } from '@/utils/browsers'
import type { User } from '@/types/user'

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
}>()

const roles = constants.ROLES
const config = inject<Config>(constants.config)

const hasLocalAuth = computed(
  () => config?.LOGIN_MODES.includes('local') || !!props.user.username || props.user.has_password,
)

const hasOauth = computed(() => config?.LOGIN_MODES.includes('oauth') || !!props.user.idp_sub)

const PASSWORD_PLACEHOLDER = '******'

// Reactive data
const form = ref({
  username: '',
  display_name: '',
  role: '' as (typeof constants.ROLES)[number],
  password: '',
  customScope: '',
  idp_sub: '',
})

// Computed properties
const isCustomRole = computed(() => form.value.role === 'custom')

const usernameError = computed(() => {
  // If user has password, username cannot be empty
  if (props.user.has_password && !form.value.username.trim()) {
    return 'Username is required for users with password'
  }
  return null
})

const displayNameError = computed(() => {
  if (!form.value.display_name.trim()) {
    return 'Display name is required'
  }
  return null
})

const passwordChanged = computed(() => {
  return form.value.password !== (props.user.has_password ? PASSWORD_PLACEHOLDER : '')
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

const generateNewPassword = () => {
  form.value.password = generatePassword(8)
}

// Watchers
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
const hasChanges = computed(() => {
  return payload.value !== null || passwordChanged.value
})

const submitForm = () => {
  if (payload.value) {
    emit('update-user', payload.value)
  }
  if (passwordChanged.value) {
    emit('change-password', form.value.password.trim() ? form.value.password.trim() : null)
  }
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
    password: props.user.has_password ? PASSWORD_PLACEHOLDER : '',
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
