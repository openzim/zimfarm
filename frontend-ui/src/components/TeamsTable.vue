<!-- Teams table: paginated list of teams -->
<template>
  <div>
    <v-card v-if="!errors.length" :class="{ loading: loading }" flat>
      <v-data-table-server
        :headers="headers"
        :items="teams"
        :loading="loading"
        :page="paginator.page"
        :items-per-page="paginator.limit"
        :items-length="paginator.count"
        :items-per-page-options="limits"
        class="elevation-1"
        item-key="name"
        @update:options="onUpdateOptions"
        :hide-default-footer="props.paginator.count === 0"
        :hide-default-header="props.paginator.count === 0"
        :mobile="smAndDown"
        :density="smAndDown ? 'compact' : 'comfortable'"
      >
        <template #loading>
          <div class="d-flex flex-column align-center justify-center pa-8">
            <v-progress-circular indeterminate size="64" />
            <div class="mt-4 text-body-1">{{ loadingText || 'Fetching teams...' }}</div>
          </div>
        </template>

        <template #[`item.name`]="{ item }">
          <router-link
            :to="{ name: 'team-detail', params: { teamName: item.name } }"
            class="text-decoration-none text-primary"
          >
            {{ item.name }}
          </router-link>
        </template>

        <template #[`item.is_private`]="{ item }">
          <v-chip :color="item.is_private ? 'warning' : 'success'" size="small" variant="tonal">
            {{ item.is_private ? 'Private' : 'Public' }}
          </v-chip>
        </template>

        <template #no-data>
          <div class="text-center pa-4">
            <v-icon size="large" class="mb-2">mdi-account-group-outline</v-icon>
            <div class="text-body-1">No teams found</div>
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
import type { TeamLight } from '@/types/team'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'

const props = defineProps<{
  headers: { title: string; key: string; sortable?: boolean }[]
  teams: TeamLight[]
  paginator: Paginator
  loading: boolean
  errors: string[]
  loadingText: string
}>()

const emit = defineEmits<{
  limitChanged: [limit: number]
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
</script>
