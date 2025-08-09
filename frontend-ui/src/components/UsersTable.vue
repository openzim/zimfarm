<template>
  <div>
    <v-card v-if="!errors.length" :class="{ 'loading': loading }" flat>
      <v-card-title v-if="paginator.count > 0" class="d-flex align-center justify-space-between">
        <span class="text-subtitle-1 d-flex align-center">
          <v-icon class="mr-2">mdi-account-group</v-icon>
          Showing max.
          <v-select
            v-model="selectedLimit"
            :items="limits"
            hide-details
            density="compact"
            @update:modelValue="emit('limitChanged', $event)"
          />
          out of <strong class="ml-1 mr-1">{{ props.paginator.count }}</strong> users
        </span>
      </v-card-title>
      <v-data-table-server
        :headers="headers"
        :items="users"
        :loading="loading"
        :items-per-page="selectedLimit"
        :items-length="props.paginator.count"
        :items-per-page-options="limits"
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
          <v-chip
            :color="getRoleColor(item.role)"
            size="small"
            variant="tonal"
          >
            {{ item.role }}
          </v-chip>
        </template>

        <template #[`item.email`]="{ item }">
          <a
            :href="`mailto:${item.email}`"
            class="text-decoration-none text-primary"
          >
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
import ErrorMessage from '@/components/ErrorMessage.vue';
import type { Paginator } from '@/types/base';
import type { User } from '@/types/user';
import { ref, watch } from 'vue';

const props = defineProps<{
  headers: { title: string; key: string; sortable?: boolean }[]
  users: User[]
  paginator: Paginator
  loading: boolean
  errors: string[]
  loadingText: string
}>()

const emit = defineEmits<{
  'limitChanged': [limit: number]
  'loadData': [limit: number, skip: number]
}>()

const limits = [10, 20, 50, 100]
const selectedLimit = ref(props.paginator.limit)

function onUpdateOptions(options: { page: number, itemsPerPage: number }) {
  // Calculate the skip for the request
  const page = options.page > 1 ? options.page - 1 : 0
  emit('loadData', options.itemsPerPage, page * options.itemsPerPage)
}

watch(() => props.paginator, (newPaginator) => {
  selectedLimit.value = newPaginator.limit
}, { immediate: true })

const getRoleColor = (role: string): string => {
  const colorMap: Record<string, string> = {
    admin: 'error',
    editor: 'primary',
    'editor-requester': 'info',
    manager: 'warning',
    processor: 'success',
    worker: 'secondary'
  }
  return colorMap[role] || 'default'
}
</script>
