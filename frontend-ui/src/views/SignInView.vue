<!-- Authentication Page

  - gets username and password
  - athenticates on the API
  - retrieve and store token in store
  - handles own login/error
  - supports Ory.sh OAuth2 authentication -->

<template>
  <v-container class="fill-height">
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card class="elevation-12">
          <v-card-text class="text-center pa-4">
            <!-- Logo -->
            <div class="mb-3">
              <img src="/assets/logo.svg" alt="Zimfarm Logo" width="48" height="48" />
            </div>

            <h1 class="text-h5 mb-4 font-weight-medium">Please sign in</h1>

            <!-- Sign In Form -->
            <v-form @submit.prevent="authenticate" ref="form">
              <!-- Error Snackbar -->
              <v-alert
                v-for="error in errors"
                :key="error"
                type="error"
                variant="tonal"
                class="mb-3"
              >
                {{ error }}
              </v-alert>

              <!-- Loading Alert -->
              <v-alert v-if="working" type="info" variant="tonal" class="mb-3" density="compact">
                <template v-slot:prepend>
                  <v-progress-circular indeterminate size="16" />
                </template>
                Signing you in...
              </v-alert>
              <v-text-field
                v-model="username"
                label="Username"
                prepend-inner-icon="mdi-account"
                variant="outlined"
                :rules="[rules.required, rules.minLength(3)]"
                required
                autofocus
                class="mb-3"
                density="compact"
                hide-details="auto"
                validate-on="blur lazy"
              />

              <v-text-field
                v-model="password"
                label="Password"
                prepend-inner-icon="mdi-lock"
                variant="outlined"
                type="password"
                :rules="[rules.required, rules.minLength(3)]"
                required
                class="mb-3"
                density="compact"
                hide-details="auto"
                validate-on="blur lazy"
              />

              <v-checkbox
                v-model="remember"
                label="Remember me"
                class="mb-3"
                density="compact"
                hide-details
              />

              <!-- Sign In Button -->
              <v-btn
                type="submit"
                color="primary"
                size="default"
                block
                :loading="working"
                :disabled="working"
                class="mb-3"
              >
                Sign in with Username
              </v-btn>
            </v-form>

            <v-divider class="my-4">
              <span class="text-medium-emphasis px-2">OR</span>
            </v-divider>

            <v-btn
              variant="outlined"
              color="primary"
              size="large"
              block
              class="mb-4 kiwix-btn"
              @click="signInWithKiwix"
            >
              <span class="flex-grow-1">Sign in with Kiwix</span>
              <img src="/assets/kiwix-icon.svg" alt="Kiwix" class="kiwix-icon" />
            </v-btn>

            <!-- Contact Email -->
            <div class="text-caption text-medium-emphasis">
              <a :href="`mailto:${contactEmail}`" class="text-decoration-none">
                {{ contactEmail }}
              </a>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import type { Config } from '@/config'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { getKiwixAuthConfig, initiateKiwixLogin } from '@/services/auth/kiwix'
import { computed, inject, ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

// Inject config
const config = inject<Config>(constants.config)
if (!config) {
  throw new Error('Config is not defined')
}

// Router and stores
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

// Form ref
const form = ref()

// Reactive data
const username = ref('')
const password = ref('')
const remember = ref(true)
const working = ref(false)
const errors = ref<string[]>([])

// Computed properties
const contactEmail = computed(() => {
  // You might want to move this to config or constants
  return 'contact@kiwix.org'
})

// Form validation rules
const rules = {
  required: (value: string) => !!value || 'This field is required',
  minLength: (minLength: number) => (value: string) =>
    value.length >= minLength || `This field must be at least ${minLength} characters long`,
}

// Watch for input changes to clear errors
watch([username, password], () => {
  if (errors.value.length > 0) {
    errors.value = []
  }
})

// Methods
const authenticate = async () => {
  const { valid } = await form.value?.validate()
  if (!valid) return

  working.value = true
  errors.value = []

  try {
    const success = await authStore.authenticate(username.value, password.value)

    if (success && authStore.isLoggedIn) {
      router.back()
    } else {
      // Copy errors from auth store to component errors
      errors.value = [...authStore.errors]
    }
  } catch (err) {
    console.error('Authentication error:', err)
    errors.value =
      authStore.errors.length > 0 ? [...authStore.errors] : ['An unexpected error occurred']
  } finally {
    working.value = false
  }
}

const signInWithKiwix = async () => {
  // Store current route for redirect after authentication
  const redirect = route.query.redirect as string
  if (redirect) {
    sessionStorage.setItem('auth_redirect', redirect)
  }

  // Get Kiwix auth configuration and initiate OAuth2 flow
  const kiwixAuthConfig = getKiwixAuthConfig(config)
  await initiateKiwixLogin(kiwixAuthConfig)
}
</script>

<style scoped>
.v-card {
  border-radius: 8px;
}

.v-text-field {
  border-radius: 6px;
}

.v-btn {
  border-radius: 6px;
  text-transform: none;
  font-weight: 500;
}

.v-divider {
  color: rgba(var(--v-theme-on-surface), 0.12);
}

.kiwix-icon {
  width: 24px;
  height: 24px;
  margin-left: 8px;
}
</style>
