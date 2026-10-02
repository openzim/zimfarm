<!-- Team management view:
  - detail
  - history
  - edit name / visibility -->

<template>
  <v-container>
    <!-- Loading state when data hasn't been loaded yet -->
    <div v-if="!dataLoaded && loadingStore.isLoading" class="text-center pa-8">
      <v-progress-circular indeterminate size="64" />
      <div class="mt-4 text-body-1">{{ loadingStore.loadingText }}</div>
    </div>

    <!-- Content only shown when data is loaded -->
    <div v-if="dataLoaded">
      <v-row>
        <v-col cols="12">
          <h2 class="text-h6 text-md-h4">
            <code>{{ team?.name }}</code>
          </h2>

          <div v-if="!error && team">
            <!-- Tabs -->
            <v-tabs v-model="selectedTab" color="primary" class="mb-4">
              <v-tab value="details" :to="{ name: 'team-detail', params: { teamName: teamName } }">
                View
              </v-tab>
              <v-tab
                value="history"
                :to="{
                  name: 'team-detail-tab',
                  params: { teamName: teamName, selectedTab: 'history' },
                }"
              >
                History
              </v-tab>
              <v-tab
                v-if="canUpdateTeams"
                value="edit"
                :to="{
                  name: 'team-detail-tab',
                  params: { teamName: teamName, selectedTab: 'edit' },
                }"
              >
                Edit
              </v-tab>
            </v-tabs>

            <!-- Tab Content -->
            <v-window v-model="selectedTab">
              <!-- Details Tab -->
              <v-window-item value="details">
                <v-card flat>
                  <v-card-text class="pa-0">
                    <div class="ml-4 mr-4 mt-2 mb-2">
                      <v-row no-gutters class="py-2">
                        <v-col cols="12" md="4">
                          <div class="text-subtitle-2">API</div>
                        </v-col>
                        <v-col cols="12" md="8">
                          <a
                            target="_blank"
                            :href="webApiUrl + '/teams/' + team.name"
                            class="text-decoration-none"
                          >
                            document
                            <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
                          </a>
                        </v-col>
                      </v-row>
                      <v-divider class="my-2"></v-divider>

                      <v-row no-gutters class="py-2">
                        <v-col cols="12" md="4">
                          <div class="text-subtitle-2">Name</div>
                        </v-col>
                        <v-col cols="12" md="8">
                          <code>{{ team.name }}</code>
                        </v-col>
                      </v-row>
                      <v-divider class="my-2"></v-divider>

                      <v-row no-gutters class="py-2">
                        <v-col cols="12" md="4">
                          <div class="text-subtitle-2">Visibility</div>
                        </v-col>
                        <v-col cols="12" md="8">
                          <v-chip
                            :color="team.is_private ? 'warning' : 'success'"
                            size="small"
                            variant="tonal"
                          >
                            {{ team.is_private ? 'Private' : 'Public' }}
                          </v-chip>
                        </v-col>
                      </v-row>
                      <v-divider class="my-2"></v-divider>

                      <v-row no-gutters class="py-2">
                        <v-col cols="12" md="4">
                          <div class="text-subtitle-2">Recipes</div>
                        </v-col>
                        <v-col cols="12" md="8">
                          <router-link
                            :to="{ name: 'recipes', query: { team: team.name } }"
                            class="text-decoration-none"
                          >
                            View recipes
                          </router-link>
                        </v-col>
                      </v-row>
                    </div>
                  </v-card-text>
                </v-card>
              </v-window-item>

              <!-- History Tab -->
              <v-window-item value="history">
                <TeamHistory
                  :history="teamHistoryStore.history"
                  :has-more="canLoadMoreHistory"
                  :loading="loadingHistory"
                  :paginator="teamHistoryStore.paginator"
                  :team-name="teamName"
                  @load="loadHistory"
                  @revert="handleRevert"
                />
              </v-window-item>

              <!-- Edit Tab -->
              <v-window-item value="edit">
                <UpdateTeam :team="team" v-if="team" @update-team="updateTeam" />
              </v-window-item>
            </v-window>
          </div>

          <!-- Error Message -->
          <ErrorMessage :message="error" v-if="error" />
        </v-col>
      </v-row>
    </div>
  </v-container>
</template>

<script setup lang="ts">
import { computed, inject, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import type { Config } from '@/config'
import ErrorMessage from '@/components/ErrorMessage.vue'
import TeamHistory from '@/components/TeamHistory.vue'
import UpdateTeam from '@/components/UpdateTeam.vue'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import { useLoadingStore } from '@/stores/loading'
import { useNotificationStore } from '@/stores/notification'
import { useTeamStore } from '@/stores/team'
import { useTeamHistoryStore } from '@/stores/teamHistory'
import type { Team, TeamUpdateSchema } from '@/types/team'

// Props
interface Props {
  teamName: string
  selectedTab?: string
}

const props = withDefaults(defineProps<Props>(), {
  selectedTab: 'details',
})

// Config
const appConfig = inject<Config>(constants.config)
if (!appConfig) {
  throw new Error('Config is not defined')
}

// Route and stores
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const loadingStore = useLoadingStore()
const notificationStore = useNotificationStore()
const teamStore = useTeamStore()
const teamHistoryStore = useTeamHistoryStore()

// Reactive data
const error = ref<string | null>(null)
const team = ref<Team | null>(null)
const selectedTab = ref(props.selectedTab)
const dataLoaded = ref(false)
const loadingHistory = ref(false)

// Computed properties
const webApiUrl = computed(() => appConfig.ZIMFARM_WEBAPI)
const canUpdateTeams = computed(() => authStore.hasPermission('teams', 'update'))
const canLoadMoreHistory = computed(() => {
  const { skip, limit, count } = teamHistoryStore.paginator
  return skip + limit < count
})

// Methods
const updateTeam = async (payload: TeamUpdateSchema) => {
  if (Object.keys(payload).length === 0) return

  loadingStore.startLoading('Updating team...')
  const success = await teamStore.updateTeam(props.teamName, payload)
  if (success) {
    notificationStore.showSuccess(`Team ${props.teamName} has been updated.`)
    await refreshData()
  } else {
    for (const error of teamStore.errors) {
      notificationStore.showError(error)
    }
  }
  loadingStore.stopLoading()
}

const loadTeam = async () => {
  loadingStore.startLoading('Fetching team...')

  try {
    const teamData = await teamStore.fetchTeam(props.teamName)
    if (teamData) {
      error.value = null
      team.value = teamData
      dataLoaded.value = true
    } else {
      error.value = 'Failed to load team data'
      for (const err of teamStore.errors) {
        notificationStore.showError(err)
      }
    }
  } catch (err) {
    console.error('Error loading team:', err)
    error.value = 'Failed to load team data'
  } finally {
    loadingStore.stopLoading()
  }
}

const refreshData = async () => {
  if (!team.value) {
    dataLoaded.value = false
  }
  await loadTeam()
}

// History-related methods
const loadHistory = async ({ limit, skip }: { limit: number; skip: number }) => {
  if (skip > 0 && !canLoadMoreHistory.value) return

  loadingHistory.value = true
  try {
    await teamHistoryStore.fetchHistory(props.teamName, limit, skip)
  } catch (error) {
    console.error('Failed to load team history items', error)
    notificationStore.showError(`Failed to ${skip > 0 ? 'load more' : 'load'} team history items`)
  } finally {
    loadingHistory.value = false
  }
}

const handleRevert = async (revertedTeam: Team) => {
  // A revert may rename the team, in which case the URL must follow
  if (revertedTeam.name !== props.teamName) {
    await router.replace({
      name: 'team-detail-tab',
      params: { teamName: revertedTeam.name, selectedTab: 'history' },
    })
    return
  }

  team.value = revertedTeam
  dataLoaded.value = true
  error.value = null
  teamHistoryStore.clearHistory()
  await loadHistory({ limit: teamHistoryStore.paginator.limit, skip: 0 })
}

watch(
  () => props.selectedTab,
  async (newTab) => {
    selectedTab.value = newTab
    // Refresh team data when switching tabs
    if (team.value) {
      await refreshData()
    }
    if (newTab === 'history') {
      teamHistoryStore.clearHistory()
      await loadHistory({ limit: teamHistoryStore.paginator.limit, skip: 0 })
    }
  },
)

// Watch for route params to update selected tab
watch(
  () => route.params.selectedTab,
  (newTab) => {
    if (newTab && typeof newTab === 'string') {
      selectedTab.value = newTab
    }
  },
  { immediate: true },
)

watch(
  () => props.teamName,
  async () => {
    // Reset data and reload the new team
    team.value = null
    dataLoaded.value = false
    await refreshData()
    if (selectedTab.value === 'history') {
      teamHistoryStore.clearHistory()
      await loadHistory({ limit: teamHistoryStore.paginator.limit, skip: 0 })
    }
  },
)

// Lifecycle
onMounted(async () => {
  await loadTeam()
  if (selectedTab.value === 'history') {
    await loadHistory({ limit: teamHistoryStore.paginator.limit, skip: 0 })
  }
})

onUnmounted(() => {
  // Clear team history to prevent accumulation of history items
  teamHistoryStore.clearHistory()
})
</script>
