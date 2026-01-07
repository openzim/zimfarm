<template>
  <div>
    <v-card v-if="!errors.length" :class="{ loading: loading }" flat>
      <v-data-table-server
        :headers="headers"
        :items="users"
        :loading="loading"
        :items-per-page="selectedLimit"
        :items-length="props.paginator.count"
        :items-per-page-options="limits"
        v-model:page="currentPage"
        class="elevation-1"
        item-key="username"
        @update:options="onUpdateOptions"
        :hide-default-footer="props.paginator.count === 0"
        :hide-default-header="props.paginator.count === 0"
      >
        <template #loading>
          <div class="d-flex flex-column align-center justify-center pa-8">
            <v-progress-circular indeterminate size="64" />
            <div class="mt-4 text-body-1">{{ loadingText || 'Fetching users...' }}</div>
          </div>
        </template>

        <template #[`item.username`]="{ item }">
          <router-link
            :to="{ name: 'user-detail', params: { username: item.username } }"
            class="text-decoration-none text-primary"
          >
            {{ item.username }}
          </router-link>
        </template>

        <template #[`item.role`]="{ item }">
          <v-chip :color="getRoleColor(item.role)" size="small" variant="tonal">
            {{ item.role }}
          </v-chip>
        </template>

        <template #[`item.email`]="{ item }">
          <a :href="`mailto:${item.email}`" class="text-decoration-none text-primary">
            {{ item.email }}
          </a>
        </template>

        <template #no-data>
          <div class="text-center pa-4">
            <v-icon size="large" class="mb-2">mdi-account-group-outline</v-icon>
            <div class="text-body-1">No users found</div>
          </div>
        </template>
      </v-data-table-server>
      <ErrorMessage v-for="error in errors" :key="error" :message="error" />
    </v-card>
  </div>
</template>

<script setup lang="ts">
import ErrorMessage from '@/components/ErrorMessage.vue'
import type { Paginator } from '@/types/base'
import type { User } from '@/types/user'
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const props = defineProps<{
  headers: { title: string; key: string; sortable?: boolean }[]
  users: User[]
  paginator: Paginator
  loading: boolean
  errors: string[]
  loadingText: string
}>()

const emit = defineEmits<{
  limitChanged: [limit: number]
  loadData: [limit: number, skip: number]
}>()

const router = useRouter()
const route = useRoute()

const limits = [10, 20, 50, 100]
const selectedLimit = ref(Number(route.query.limit) || props.paginator.limit)
const currentPage = ref(Number(route.query.page) || 1)

function onUpdateOptions(options: { page: number; itemsPerPage: number }) {
  // Only update if the values actually changed to avoid infinite loops
  if (
    Number(route.query.page) === options.page &&
    Number(route.query.limit) === options.itemsPerPage
  ) {
    return
  }
  router.replace({
    query: { ...route.query, limit: options.itemsPerPage.toString(), page: options.page.toString() }
  })
}

// Sync with route query changes to emit loadData once
watch(
  () => route.query,
  (newQuery) => {
    const limit = Number(newQuery.limit) || props.paginator.limit
    const page = Number(newQuery.page) || 1
    const skip = (page - 1) * limit

    currentPage.value = page
    selectedLimit.value = limit

    emit('loadData', limit, skip)
  },
  { immediate: true }
)

function getRoleColor(role: string): string {
  const colorMap: Record<string, string> = {
    admin: 'error',
    editor: 'primary',
    'editor-requester': 'info',
    manager: 'warning',
    processor: 'success',
    worker: 'secondary',
  }
  return colorMap[role] || 'default'
}
</script>
