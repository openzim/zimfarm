<!-- Sign-in button that transforms into a user menu
  - send to sign-in if not logged-in
  - copy token to clipboard
  - send to change-password (TBI)
  - log-out -->

<template>
  <div>
    <!-- User Menu (when logged in) -->
    <v-menu v-if="isLoggedIn" location="bottom end" offset-y>
      <template v-slot:activator="{ props }">
        <v-btn
          v-bind="props"
          variant="outlined"
          color="white"
          size="small"
          prepend-icon="mdi-account-circle"
        >
          {{ username }}
        </v-btn>
      </template>

      <v-list>
        <v-list-item @click="copyToken" prepend-icon="mdi-key">
          <v-list-item-title>Copy token</v-list-item-title>
        </v-list-item>

        <v-list-item prepend-icon="mdi-wrench">
          <v-list-item-title>Change password</v-list-item-title>
        </v-list-item>

        <v-divider></v-divider>

        <v-list-item @click="$emit('sign-out')" prepend-icon="mdi-logout">
          <v-list-item-title>Sign-out</v-list-item-title>
        </v-list-item>
      </v-list>
    </v-menu>

    <!-- Sign-in Button (when not logged in) -->
    <v-btn
      v-else
      variant="outlined"
      color="white"
      size="small"
      prepend-icon="mdi-login"
      :to="{ name: 'sign-in' }"
    >
      Sign-in
    </v-btn>
  </div>
</template>

<script setup lang="ts">
defineOptions({
  name: 'UserButton',
})

const props = defineProps<{
  username: string | null
  isLoggedIn: boolean
  accessToken: string | null
}>()

defineEmits<{
  'sign-out': []
}>()

const copyToken = async () => {
  try {
    if (props.accessToken) {
      await navigator.clipboard.writeText(props.accessToken)
      // You might want to add a toast notification here
      console.log('Token copied to clipboard!')
    }
  } catch (error) {
    console.error('Failed to copy token:', error)
    // Fallback: show token in alert or modal
    if (props.accessToken) {
      alert(`Token: ${props.accessToken}`)
    }
  }
}
</script>
