<script setup lang="ts">
import { computed } from 'vue'
import { RouterView, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import NavBar from '@/components/NavBar.vue'
import type { NavigationItem } from '@/components/NavBar.vue'

// Store and router
const userStore = useUserStore()

const router = useRouter()

// User object for passing to components
const user = computed(() => {
  if (!userStore.isLoggedIn) return null
  return {
    username: userStore.username,
    isLoggedIn: userStore.isLoggedIn,
    accessToken: userStore.accessToken
  }
})

// Navigation items logic
const canReadUsers = computed(() => {
  return userStore.hasPermission('users', 'read')
})

const navigationItems: NavigationItem[] = [
  {
    name: 'pipeline',
    label: 'Pipeline',
    route: 'pipeline',
    icon: 'mdi-pipe',
    disabled: false,
    show: true
  },
  {
    name: 'schedules-list',
    label: 'Recipes',
    route: 'schedules',
    icon: 'mdi-book-open-variant',
    disabled: false,
    show: true
  },
  {
    name: 'workers',
    label: 'Workers',
    route: 'workers',
    icon: 'mdi-server',
    disabled: false,
    show: true
  },
  {
    name: 'users-list',
    label: 'Users',
    route: 'users',
    icon: 'mdi-account-group',
    disabled: false,
    show: canReadUsers.value
  },
  {
    name: 'stats',
    label: 'Stats',
    route: 'stats',
    icon: 'mdi-chart-line',
    disabled: false,
    show: true
  }
]

const handleSignOut = () => {
  userStore.clearToken()
  router.push({ name: 'home' })
}
</script>

<template>
  <v-app>
    <header>
      <NavBar
        :navigation-items="navigationItems"
        :user="user"
        @sign-out="handleSignOut"
      />
    </header>

    <main>
      <RouterView />
    </main>
  </v-app>
</template>
