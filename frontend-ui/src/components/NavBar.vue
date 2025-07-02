<template>
  <v-app-bar color="primary" dark elevation="2">
    <!-- Logo and Brand -->
    <v-app-bar-nav-icon @click="drawer = !drawer" class="d-md-none"></v-app-bar-nav-icon>

    <v-app-bar-title class="d-flex align-center">
      <div class="branding d-flex align-center">
        <div class="icon position-relative">
          <img src="/assets/logo.svg" width="32" height="32" alt="Zimfarm Logo" class="logo-img" />
          <Loading :should-display="isLoading" :loading-text="loadingText" />
        </div>
        <span class="ml-2">Zimfarm</span>
      </div>
    </v-app-bar-title>
    <!-- Navigation Links -->
    <v-tabs
      :model-value="activeTab"
      @update:model-value="handleTabChange"
      class="d-none d-md-flex"
      color="white"
      slider-color="white"
    >
      <v-tab
        v-for="item in navigationItems"
        :key="item.name"
        :disabled="item.disabled"
        :value="item.name"
        class="text-none"
      >
        {{ item.label }}
      </v-tab>
    </v-tabs>

    <v-spacer class="d-none d-sm-flex"></v-spacer>

    <!-- Support Us Button -->
    <v-btn
      variant="outlined"
      color="white"
      size="small"
      class="mr-2 d-none d-sm-flex"
      :to="{ name: 'support' }"
    >
      <v-icon size="small" class="mr-1">mdi-heart</v-icon>
      Support us
    </v-btn>

    <!-- User Button -->
    <div class="user-button-container">
      <UserButton
        :username="username"
        :is-logged-in="isLoggedIn"
        :access-token="accessToken"
        @sign-out="$emit('sign-out')"
      />
    </div>
  </v-app-bar>

  <!-- Mobile Navigation Drawer -->
  <v-navigation-drawer v-model="drawer" temporary location="left" class="d-md-none">
    <v-list>
      <v-list-item
        v-for="item in navigationItems"
        :key="item.name"
        :disabled="item.disabled"
        :prepend-icon="item.icon"
        :to="{ name: item.name }"
      >
        <v-list-item-title>{{ item.label }}</v-list-item-title>
      </v-list-item>
    </v-list>

    <template v-slot:append>
      <v-divider></v-divider>
      <v-list>
        <v-list-item :to="{ name: 'support' }" prepend-icon="mdi-heart">
          <v-list-item-title>Support us</v-list-item-title>
        </v-list-item>
      </v-list>
    </template>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import UserButton from '@/components/UserButton.vue'
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

// Props
export interface NavigationItem {
  name: string
  label: string
  route: string
  icon: string
  disabled: boolean
  show: boolean
}

defineProps<{
  navigationItems: NavigationItem[]
  username: string | null
  isLoggedIn: boolean
  accessToken: string | null
  isLoading: boolean
  loadingText: string
}>()

defineEmits<{
  'sign-out': []
}>()

const route = useRoute()
const router = useRouter()

// Reactive data
const drawer = ref(false)
const activeTab = ref(route.name)

// Watch for route changes and update activeTab
watch(
  () => route.name,
  (newRouteName) => {
    activeTab.value = newRouteName
  },
)

// Handle tab changes
const handleTabChange = (value: unknown) => {
  const routeName = value as string
  if (routeName && routeName !== route.name) {
    router.push({ name: routeName })
  }
}
</script>

<style scoped>
.branding {
  font-weight: 500;
}

.icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.logo-img {
  width: 32px;
  height: 32px;
  object-fit: contain;
  display: block;
}

.user-button-container {
  margin-right: 8px;
}

/* Ensure the loading spinner appears on top of the logo */
.icon :deep(#main-loader) {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 1;
}
</style>
