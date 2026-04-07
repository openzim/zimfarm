<template>
  <div>
    <v-card v-if="!errors.length" :class="{ loading: loading }" flat>
      <v-card-title class="d-flex align-center justify-end">
        <v-btn
          size="small"
          variant="outlined"
          color="secondary"
          class="text-none"
          @click="$emit('toggleUsersList')"
        >
          {{ toggleText }}
        </v-btn>
      </v-card-title>

      <v-data-table-server
        :headers="headers"
        :items="users"
        :loading="loading"
        :page="paginator.page"
        :items-per-page="paginator.limit"
        :items-length="paginator.count"
        :items-per-page-options="limits"
        class="elevation-1"
        item-key="id"
        @update:options="onUpdateOptions"
        :hide-default-footer="props.paginator.count === 0"
        :hide-default-header="props.paginator.count === 0"
        :mobile="smAndDown"
        :density="smAndDown ? 'compact' : 'comfortable'"
      >
        <template #loading>
          <div class="d-flex flex-column align-center justify-center pa-8">
            <v-progress-circular indeterminate size="64" />
            <div class="mt-4 text-body-1">{{ loadingText || 'Fetching users...' }}</div>
          </div>
        </template>

        <template #[`item.display_name`]="{ item }">
          <router-link
            :to="{ name: 'account-detail', params: { userId: item.id } }"
            class="text-decoration-none text-primary"
          >
            {{ item.display_name }}
          </router-link>
        </template>

        <template #[`item.role`]="{ item }">
          <v-chip :color="getRoleColor(item.role)" size="small" variant="tonal">
            {{ item.role }}
          </v-chip>
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
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'

const props = defineProps<{
  headers: { title: string; key: string; sortable?: boolean }[]
  users: User[]
  paginator: Paginator
  loading: boolean
  errors: string[]
  loadingText: string
  toggleText: string
}>()

const emit = defineEmits<{
  limitChanged: [limit: number]
  toggleUsersList: []
}>()

const limits = [10, 20, 50, 100]
const router = useRouter()
const route = useRoute()
const { smAndDown } = useDisplay()

function onUpdateOptions(options: { page: number; itemsPerPage: number }) {
  const query = { ...route.query }

  if (options.page > 1) {
    query.page = options.page.toString()
  } else {
    delete query.page
  }

  router.push({ query })

  if (options.itemsPerPage != props.paginator.limit) {
    emit('limitChanged', options.itemsPerPage)
  }
}

const getRoleColor = (role: string): string => {
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
