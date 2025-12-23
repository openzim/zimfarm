<!-- OAuth2 Callback Handler

  - Receives authorization code from Kiwix auth
  - Validates state parameter for CSRF protection
  - Exchanges code for token using PKCE verifier
  - Fetches user info from Kiwix auth
  - Redirects to appropriate page after successful authentication -->

<template>
  <v-container class="fill-height">
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card class="elevation-12">
          <v-card-text class="text-center pa-8">
            <!-- Loading State -->
            <div v-if="loading">
              <v-progress-circular indeterminate size="64" color="primary" class="mb-4" />
              <h2 class="text-h6 mb-2">Completing sign in...</h2>
              <p class="text-body-2 text-medium-emphasis">Please wait while we authenticate you.</p>
            </div>

            <!-- Error State -->
            <div v-else-if="error">
              <v-icon size="64" color="error" class="mb-4">mdi-alert-circle</v-icon>
              <h2 class="text-h6 mb-2">Authentication Failed</h2>
              <v-alert type="error" variant="tonal" class="mb-4 text-left">
                {{ error }}
              </v-alert>
              <v-btn color="primary" :to="{ name: 'sign-in' }"> Back to Sign In </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(true)
const error = ref<string | null>(null)

onMounted(async () => {
  try {
    const success = await authStore.handleCallBack('oauth', window.location.href)
    if (!success) {
      throw new Error(authStore.errors.join(', ') || 'Authentication failed')
    }

    // Redirect to home or previous page
    const redirect = sessionStorage.getItem('auth_redirect') || '/'
    sessionStorage.removeItem('auth_redirect')
    router.push(redirect)
  } catch (err) {
    console.error('OAuth callback error:', err)
    error.value = err instanceof Error ? err.message : 'An unknown error occurred'
    loading.value = false
  }
})
</script>

<style scoped>
.v-card {
  border-radius: 8px;
}
</style>
