<script setup lang="ts">
import type { NavigationItem } from '@/components/NavBar.vue'
import NavBar from '@/components/NavBar.vue'
import NotificationSystem from '@/components/NotificationSystem.vue'
import { useAuthStore } from '@/stores/auth'
import { useLanguageStore } from '@/stores/language'
import { useLoadingStore } from '@/stores/loading'
import { useOfflinerStore } from '@/stores/offliner'
import { usePlatformStore } from '@/stores/platform'
import { useTagStore } from '@/stores/tag'
import type { OfflinerDefinitionResponse } from '@/types/offliner'
import { computed, onBeforeMount, onMounted } from 'vue'
import { RouterView, useRouter } from 'vue-router'

// Store and router
const authStore = useAuthStore()
const languageStore = useLanguageStore()
const tagStore = useTagStore()
const platformStore = usePlatformStore()
const loadingStore = useLoadingStore()
const offlinerStore = useOfflinerStore()

const router = useRouter()


onBeforeMount(async () => {
  await authStore.loadTokenFromCookie()
  // TODO: setup listener for 'on-schedule' event to load schedules
})

onMounted(async () => {
  // TODO: Call parent.alert[Danger|Success|Info|Warning] on error|response
  // TODO: Set up the AlertFeedback component to use the alert system
  await languageStore.fetchLanguages()
  await tagStore.fetchTags()
  await platformStore.fetchPlatforms()
  // load offliners and their definitions
  let offlinerDefinitionRequests: Promise<OfflinerDefinitionResponse | null>[] = []
  await offlinerStore.fetchOffliners()
  offlinerDefinitionRequests = offlinerStore.offliners.map(async (offliner) => {
    return offlinerStore.fetchOfflinerDefinition(offliner)
  })
  await Promise.all(offlinerDefinitionRequests)

  // TODO: Set up store to fetch schedules. Schema is a bit different from v1
  // because of switch to Pydantic and will need to do a db update to re-shape
  // the models as the config has changed shape.
})

// Navigation items logic
const canReadUsers = computed(() => {
  return authStore.hasPermission('users', 'read')
})

const navigationItems: NavigationItem[] = [
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
  {
    name: 'stats',
    label: 'Stats',
    route: 'stats',
    icon: 'mdi-chart-line',
    disabled: false,
    show: true,
  },
]

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
        <RouterView />
      </v-container>
    </v-main>
  </v-app>
</template>
