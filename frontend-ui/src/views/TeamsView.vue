<!-- Teams management view:
  - list of teams accessible to the current account
  - create a team (requires "teams:create" permission) -->

<template>
  <div>
    <v-card class="mb-4" flat>
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" sm="4">
            <v-text-field
              v-model="searchName"
              label="Search team"
              placeholder="Enter team name to search"
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
              @blur="handleSearchChange"
              @keyup.enter="handleSearchChange"
              @click:clear="handleSearchChange"
            />
          </v-col>
          <v-col cols="12" sm="4">
            <v-select
              v-model="privacyFilter"
              :items="privacyOptions"
              label="Visibility"
              variant="outlined"
              density="compact"
              hide-details
              @update:model-value="handlePrivacyChange"
            />
          </v-col>
          <v-col cols="12" sm="4">
            <v-btn
              v-if="canCreateTeams"
              color="primary"
              variant="elevated"
              block
              @click="showCreateDialog = true"
            >
              <v-icon class="mr-2">mdi-account-multiple-plus</v-icon>
              Create Team
            </v-btn>
          </v-col>
        </v-row>

        <v-row v-if="hasActiveFilters" class="mt-2">
          <v-col cols="12" class="d-flex flex-sm-row flex-column align-sm-center">
            <v-btn size="small" variant="outlined" @click="handleClearFilters">
              <v-icon size="small" class="mr-1">mdi-close-circle</v-icon>
              clear filters
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <TeamsTable
      :headers="headers"
      :teams="teams"
      :paginator="paginator"
      :loading="loadingStore.isLoading"
      :loading-text="loadingStore.loadingText"
      :errors="teamStore.errors"
      @limit-changed="handleLimitChange"
    />

    <!-- Create Team Dialog -->
    <v-dialog v-model="showCreateDialog" max-width="600" persistent>
      <v-card>
        <v-card-title class="text-h6 bg-primary">
          <v-icon class="mr-2">mdi-account-multiple-plus</v-icon>
          Create New Team
        </v-card-title>

        <v-card-text class="pt-4">
          <v-form @submit.prevent="createTeam" ref="formRef">
            <v-row>
              <v-col cols="12">
                <v-text-field
                  v-model="form.name"
                  label="Name"
                  placeholder="Enter team name"
                  variant="outlined"
                  density="compact"
                  hide-details="auto"
                  :validate-on="'blur'"
                  :rules="[rules.required, rules.minLength(3)]"
                />
              </v-col>

              <v-col cols="12">
                <v-switch
                  v-model="form.is_private"
                  label="Private team"
                  hint="Only team members and users with global roles can view or edit private team recipes."
                  persistent-hint
                  color="primary"
                  hide-details="auto"
                />
              </v-col>
            </v-row>
          </v-form>
        </v-card-text>

        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="closeCreateDialog" :disabled="isCreating"> Cancel </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
            :disabled="!isFormValid || isCreating"
            :loading="isCreating"
            @click="createTeam"
          >
            <v-icon class="mr-2">mdi-account-multiple-plus</v-icon>
            Create Team
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import TeamsTable from '@/components/TeamsTable.vue'
import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useTeamStore } from '@/stores/team'
import type { TeamLight } from '@/types/team'

type PrivacyFilter = 'all' | 'public' | 'private'

// Router and stores
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const loadingStore = useLoadingStore()
const notificationStore = useNotificationStore()
const teamStore = useTeamStore()

// Form ref
const formRef = ref()

// Reactive data
const teams = ref<TeamLight[]>([])
const isCreating = ref(false)
const searchName = ref<string>('')
const privacyFilter = ref<PrivacyFilter>('all')
const showCreateDialog = ref(false)

const paginator = ref({
  page: Number(route.query.page) || 1,
  page_size: teamStore.defaultLimit,
  skip: 0,
  limit: teamStore.defaultLimit,
  count: 0,
})

const form = ref<{ name: string | null; is_private: boolean }>({
  name: '',
  is_private: false,
})

// Computed properties
const canCreateTeams = computed(() => authStore.hasPermission('teams', 'create'))

const isFormValid = computed(() => (form.value.name ?? '').trim().length >= 3)

const hasActiveFilters = computed(
  () => searchName.value.trim() !== '' || privacyFilter.value !== 'all',
)

const privacyOptions = [
  { title: 'All', value: 'all' },
  { title: 'Public', value: 'public' },
  { title: 'Private', value: 'private' },
]

// Table headers
const headers = [
  { title: 'Name', key: 'name', sortable: false },
  { title: 'Visibility', key: 'is_private', sortable: false },
]

// Form validation rules
const rules = {
  required: (value: string) => !!value || 'This field is required',
  minLength: (min: number) => (value: string | null) =>
    (value?.length ?? 0) >= min || `This field must be at least ${min} characters long`,
}

// Methods
const createTeam = async () => {
  const { valid } = await formRef.value?.validate()
  if (!valid) return

  isCreating.value = true
  loadingStore.startLoading('Creating team...')

  const response = await teamStore.createTeam({
    name: (form.value.name ?? '').trim(),
    is_private: form.value.is_private,
  })

  if (response) {
    notificationStore.showSuccess(`Team "${response.name}" has been created.`)

    formRef.value?.reset()
    form.value = { name: '', is_private: false }
    showCreateDialog.value = false

    await loadData(paginator.value.limit, paginator.value.skip)
  } else {
    for (const error of teamStore.errors) {
      notificationStore.showError(error)
    }
  }
  isCreating.value = false
  loadingStore.stopLoading()
}

const loadData = async (limit: number, skip: number) => {
  loadingStore.startLoading('Fetching teams...')

  const response = await teamStore.fetchTeams({
    skip,
    limit,
    name: searchName.value || undefined,
    is_private: privacyFilter.value === 'all' ? undefined : privacyFilter.value === 'private',
  })
  if (response) {
    teams.value = response
    paginator.value = { ...teamStore.paginator }
    teamStore.savePaginatorLimit(limit)
  } else {
    for (const error of teamStore.errors) {
      notificationStore.showError(error)
    }
  }
  loadingStore.stopLoading()
}

const handleSearchChange = () => {
  const query = { ...route.query }
  if (searchName.value) {
    query.name = searchName.value
  } else {
    delete query.name
  }
  delete query.page
  router.push({ query })
}

const handlePrivacyChange = () => {
  const query = { ...route.query }
  if (privacyFilter.value === 'all') {
    delete query.is_private
  } else {
    query.is_private = privacyFilter.value === 'private' ? 'true' : 'false'
  }
  delete query.page
  router.push({ query })
}

const handleClearFilters = () => {
  searchName.value = ''
  privacyFilter.value = 'all'
  const query = { ...route.query }
  delete query.name
  delete query.is_private
  delete query.page
  router.push({ query })
}

const closeCreateDialog = () => {
  formRef.value?.reset()
  form.value = { name: '', is_private: false }
  showCreateDialog.value = false
}

const handleLimitChange = async (newLimit: number) => {
  teamStore.savePaginatorLimit(newLimit)
  if (paginator.value.page != 1) {
    paginator.value = {
      ...paginator.value,
      limit: newLimit,
      page: 1,
      skip: 0,
    }
  } else {
    await loadData(newLimit, 0)
  }
}

// Reload data whenever the query changes
watch(
  () => router.currentRoute.value.query,
  async () => {
    const query = router.currentRoute.value.query
    let page = 1
    if (query.page && typeof query.page === 'string') {
      const parsedPage = parseInt(query.page, 10)
      if (!isNaN(parsedPage) && parsedPage > 1) {
        page = parsedPage
      }
    }
    if (query.name && typeof query.name === 'string') {
      searchName.value = query.name
    } else if (!query.name) {
      searchName.value = ''
    }
    if (query.is_private === 'true') {
      privacyFilter.value = 'private'
    } else if (query.is_private === 'false') {
      privacyFilter.value = 'public'
    } else {
      privacyFilter.value = 'all'
    }
    const newSkip = (page - 1) * paginator.value.limit
    await loadData(paginator.value.limit, newSkip)
  },
  { deep: true, immediate: true },
)
</script>
