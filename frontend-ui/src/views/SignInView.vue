<!-- Authentication Page

  - gets username and password
  - athenticates on the API
  - retrieve and store token in store
  - handles own login/error
  - save token info in cookie if asked to remember -->

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
                :rules="[rules.required, rules.min(username, 3)]"
                required
                autofocus
                class="mb-3"
                density="compact"
                hide-details="auto"
                validate-on="blur"
              />

              <v-text-field
                v-model="password"
                label="Password"
                prepend-inner-icon="mdi-lock"
                variant="outlined"
                type="password"
                :rules="[rules.required, rules.min(password, 3)]"
                required
                class="mb-3"
                density="compact"
                hide-details="auto"
                validate-on="blur"
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
                Sign in
              </v-btn>
            </v-form>

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
import { computed, inject, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

// Inject config
const config = inject<Config>(constants.config)
if (!config) {
  throw new Error('Config is not defined')
}

// Router and stores
const router = useRouter()
const authStore = useAuthStore()

// Form ref
const form = ref()

// Reactive data
const username = ref('')
const password = ref('')
const remember = ref(true)
const working = ref(false)
const errors = computed(() => authStore.errors)

// Computed properties
const contactEmail = computed(() => {
  // You might want to move this to config or constants
  return 'contact@kiwix.org'
})

// Form validation rules
const rules = {
  required: (value: string) => !!value || 'This field is required',
  min: (value: string, minLength: number) =>
    value.length >= minLength || `This field must be at least ${minLength} characters long`,
}

// Watch for input changes to clear error
watch([username, password], () => {
  if (authStore.errors.length > 0) {
    authStore.errors = []
  }
})

// Methods
const authenticate = async () => {
  const { valid } = await form.value?.validate()
  if (!valid) return

  working.value = true

  await authStore.authenticate(username.value, password.value)
  working.value = false
  if (authStore.isLoggedIn) {
    router.back()
  }
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
</style>
