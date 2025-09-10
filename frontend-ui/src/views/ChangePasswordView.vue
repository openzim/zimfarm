<!-- Change Password Page

  - gets current and new password
  - send to API
  - handles own login/error -->

<template>
  <v-container class="fill-height">
    <v-row justify="center" align="center">
      <v-col cols="12" sm="8" md="6" lg="4">
        <v-card class="elevation-12">
          <v-card-title class="text-center text-h5 py-4"> Change Password </v-card-title>

          <v-card-text>
            <v-form @submit.prevent="changePassword" ref="form">
              <v-text-field
                v-model="currentPassword"
                :type="showCurrentPassword ? 'text' : 'password'"
                label="Current Password"
                prepend-inner-icon="mdi-lock"
                :append-inner-icon="showCurrentPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append-inner="showCurrentPassword = !showCurrentPassword"
                :rules="[rules.required]"
                required
                density="compact"
                autofocus
                variant="outlined"
                hide-details="auto"
                validate-on="blur"
                class="mb-3"
              />

              <v-text-field
                v-model="newPassword"
                :type="showNewPassword ? 'text' : 'password'"
                label="New Password"
                prepend-inner-icon="mdi-lock-plus"
                :append-inner-icon="showNewPassword ? 'mdi-eye' : 'mdi-eye-off'"
                @click:append-inner="showNewPassword = !showNewPassword"
                :rules="[rules.required, rules.minLength]"
                required
                density="compact"
                variant="outlined"
                hide-details="auto"
                validate-on="blur"
                class="mb-3"
              />

              <v-alert v-if="error" type="error" variant="tonal" class="mb-4">
                <div v-text="error" />
              </v-alert>

              <v-alert v-if="working" type="warning" variant="tonal" class="mb-4">
                <v-progress-circular indeterminate color="warning" size="20" class="me-2" />
                Changing your password…
              </v-alert>
            </v-form>
          </v-card-text>

          <v-card-actions>
            <v-btn
              block
              color="primary"
              size="default"
              variant="elevated"
              :loading="working"
              :disabled="working || !isFormValid"
              @click="changePassword"
            >
              Update Password
            </v-btn>
          </v-card-actions>

          <v-card-text class="text-center pt-0">
            <v-btn variant="text" color="primary" :href="`mailto:${contactEmail}`">
              {{ contactEmail }}
            </v-btn>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup lang="ts">
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { useUserStore } from '@/stores/user'
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import type { VForm } from 'vuetify/components'

// Composables and stores
const router = useRouter()
const authStore = useAuthStore()
const userStore = useUserStore()
const notificationStore = useNotificationStore()

// Reactive data
const currentPassword = ref('')
const newPassword = ref('')
const working = ref(false)
const error = ref<string | null>(null)
const showCurrentPassword = ref(false)
const showNewPassword = ref(false)
const form = ref<VForm | null>(null)
const isFormValid = ref(false)

// Validation rules
const rules = {
  required: (value: string) => !!value || 'This field is required',
  minLength: (value: string) => value.length >= 8 || 'Password must be at least 8 characters',
}

// Computed properties
const contactEmail = computed(() => constants.CONTACT_EMAIL)

// Methods
const changePassword = async () => {
  const validation = await form.value?.validate()
  if (!validation?.valid) return

  if (!authStore.username) {
    error.value = '<strong>Refused</strong>: You must be signed-in to change your password…'
    return
  }

  working.value = true
  error.value = null

  const success = await userStore.changePassword(authStore.username, {
    current: currentPassword.value,
    new: newPassword.value,
  })

  if (success) {
    notificationStore.showSuccess('Password changed successfully')
    if (window.history.length > 1) {
      router.back()
    } else {
      router.push({ name: 'home' })
    }
  } else {
    error.value = 'Failed to change password'
    for (const error of userStore.errors) {
      notificationStore.showError(error)
    }
  }

  working.value = false
}

// Watch for form validation
const validateForm = async () => {
  if (form.value) {
    const validation = await form.value.validate()
    isFormValid.value = validation?.valid || false
  }
}

// Watch for input changes to validate form
watch([currentPassword, newPassword], () => {
  validateForm()
})

// Lifecycle
onMounted(() => {
  if (!authStore.isLoggedIn) {
    router.push({ name: 'sign-in' })
  }
})
</script>

<style scoped></style>
