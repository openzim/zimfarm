<script setup lang="ts">
import type { NavigationItem } from '@/components/NavBar.vue'
import NavBar from '@/components/NavBar.vue'
import NotificationSystem from '@/components/NotificationSystem.vue'
import { useAuthStore } from '@/stores/auth'
import { useContextStore } from '@/stores/context'
import { useLanguageStore } from '@/stores/language'
import { useLoadingStore } from '@/stores/loading'
import { useOfflinerStore } from '@/stores/offliner'
import { usePlatformStore } from '@/stores/platform'
import { useTagStore } from '@/stores/tag'
import { computed, onMounted, ref } from 'vue'
import { RouterView, useRouter } from 'vue-router'

// Store and router
const authStore = useAuthStore()
const languageStore = useLanguageStore()
const tagStore = useTagStore()
const contextStore = useContextStore()
const platformStore = usePlatformStore()
const loadingStore = useLoadingStore()
const offlinerStore = useOfflinerStore()

const router = useRouter()
const ready = ref(false)

onMounted(async () => {
  await authStore.loadToken()
  loadingStore.startLoading('Loading application data...')

  await languageStore.fetchLanguages()
  await tagStore.fetchTags()
  await contextStore.fetchContexts()
  await platformStore.fetchPlatforms()
  await offlinerStore.fetchOffliners()

  loadingStore.stopLoading()
  ready.value = true
})

// Navigation items logic
const canReadUsers = computed(() => {
  return authStore.hasPermission('users', 'read')
})

const navigationItems = computed<NavigationItem[]>(() => [
  {
    name: 'pipeline',
    label: 'Pipeline',
    route: 'pipeline',
    icon: 'mdi-pipe',
    disabled: false,
    show: true,
  },
  {
    name: 'schedules-list',
    label: 'Recipes',
    route: 'schedules',
    icon: 'mdi-book-open-variant',
    disabled: false,
    show: true,
  },
  {
    name: 'workers',
    label: 'Workers',
    route: 'workers',
    icon: 'mdi-server',
    disabled: false,
    show: true,
  },
  {
    name: 'users-list',
    label: 'Users',
    route: 'users',
    icon: 'mdi-account-group',
    disabled: false,
    show: canReadUsers.value,
  },
])

const handleSignOut = () => {
  authStore.logout()
  router.push({ name: 'home' })
}
</script>

<template>
  <v-app>
    <NotificationSystem />
    <header>
      <NavBar
        :navigation-items="navigationItems"
        :username="authStore.user?.username ?? null"
        :is-logged-in="authStore.isLoggedIn"
        :access-token="authStore.accessToken"
        :is-loading="loadingStore.isLoading"
        :loading-text="loadingStore.loadingText"
        @sign-out="handleSignOut"
      />
    </header>

    <v-main>
      <v-container>
        <RouterView v-if="ready" />
        <div v-else class="d-flex align-center justify-center" style="height: 80vh">
          <v-progress-circular indeterminate size="70" width="7" color="primary" />
        </div>
      </v-container>
    </v-main>
  </v-app>
</template>
