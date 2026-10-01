<template>
  <div>
    <v-card v-if="!errors.length" :class="{ loading: loading }" flat>
      <v-card-title
        v-if="showSelection || $slots.actions"
        class="d-flex flex-sm-wrap flex-grow-1 flex-column-reverse flex-sm-row align-sm-center justify-sm-start ga-2"
      >
        <slot name="actions" />
        <v-btn
          v-if="showSelection"
          size="small"
          variant="elevated"
          :color="selectedRecipes.length === 0 ? undefined : 'warning'"
          :disabled="selectedRecipes.length === 0"
          @click="promptClearSelections"
        >
          <v-icon size="small" class="mr-1">mdi-checkbox-multiple-blank-outline</v-icon>
          clear selections
        </v-btn>

        <ConfirmDialog
          v-model="showClearConfirm"
          title="Confirm Clear Selections"
          message="Are you sure you want to clear your current selection?"
          confirm-text="Proceed"
          cancel-text="Abort"
          confirm-color="warning"
          icon="mdi-help-circle"
          icon-color="warning"
          @confirm="clearSelections"
          @cancel="showClearConfirm = false"
        />
      </v-card-title>

      <v-data-table-server
        :headers="headers"
        :items="recipes"
        :loading="loading"
        :page="paginator.page"
        :items-per-page="paginator.limit"
        :items-length="paginator.count"
        :items-per-page-options="limits"
        class="elevation-1"
        item-value="name"
        :show-select="showSelection"
        :item-selectable="isRecipeInEditScope"
        :row-props="recipeRowProps"
        :model-value="selectedRecipes"
        @update:model-value="handleSelectionChange"
        @update:options="onUpdateOptions"
        :hide-default-footer="props.paginator.count === 0"
        :hide-default-header="props.paginator.count === 0"
        :mobile="smAndDown"
        :density="smAndDown ? 'compact' : 'comfortable'"
      >
        <template #loading>
          <div class="d-flex flex-column align-center justify-center pa-8">
            <v-progress-circular indeterminate size="64" />
            <div class="mt-4 text-body-1">{{ loadingText || 'Fetching recipes...' }}</div>
          </div>
        </template>

        <template #[`item.name`]="{ item }">
          <router-link :to="{ name: 'recipe-detail', params: { recipeName: item.name } }">
            <span class="['d-flex' 'align-center', { 'justify-end': smAndDown">
              {{ item.name }}
              <v-icon v-if="!item.enabled" size="small" color="orange" class="ml-1">
                mdi-pause
              </v-icon>
              <v-icon
                v-if="!isRecipeInEditScope(item)"
                size="small"
                color="grey"
                class="ml-1"
                title="Read-only recipe: belongs to a team you are not a member of"
              >
                mdi-lock-outline
              </v-icon>
            </span>
          </router-link>
        </template>

        <template #[`item.language`]="{ item }">
          {{ item.language.name }}
        </template>

        <template #[`item.offliner`]="{ item }">
          {{ item.config.offliner || 'Unknown' }}
        </template>

        <template #[`item.requested`]="{ item }">
          <v-icon v-if="item.is_requested" size="small" color="success"> mdi-check </v-icon>
        </template>

        <template #[`item.last_task`]="{ item }">
          <StatusDisplay
            v-if="item.most_recent_task"
            :status="item.most_recent_task.status"
            :timestamp="item.most_recent_task.timestamp"
            :updated-at="item.most_recent_task.updated_at"
            :task-id="item.most_recent_task.id"
            :layout="smAndDown ? 'column' : 'row'"
          />
          <span v-else>-</span>
        </template>

        <template #no-data>
          <div class="text-center pa-4">
            <v-icon size="x-large" class="mb-2">mdi-format-list-bulleted</v-icon>
            <div class="text-h6 text-grey-darken-1 mb-2">No recipes found</div>
          </div>
        </template>
      </v-data-table-server>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import StatusDisplay from '@/components/StatusDisplay.vue'
import type { Paginator } from '@/types/base'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import type { RecipeLight } from '@/types/recipe'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useDisplay } from 'vuetify'

// Props
interface Props {
  headers: { title: string; value: string }[]
  recipes: RecipeLight[]
  paginator: Paginator
  loading: boolean
  errors: string[]
  loadingText: string
  filters?: {
    name: string
    languages: string[]
    tags: string[]
  }
  selectedRecipes?: string[]
  showSelection?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  filters: () => ({ name: '', languages: [], tags: [] }),
  selectedRecipes: () => [],
  showSelection: true,
})

const router = useRouter()
const route = useRoute()
const { smAndDown } = useDisplay()
const authStore = useAuthStore()

// Define emits
const emit = defineEmits<{
  limitChanged: [limit: number]
  loadData: [limit: number, skip: number]
  selectionChanged: [selectedRecipes: string[]]
}>()

const limits = [10, 20, 50, 100]

const selectedRecipes = computed(() => props.selectedRecipes)
const showClearConfirm = ref(false)

// Team-scoped accounts can only act on recipes owned by one of their teams. Global
// roles (i.e. not in TEAM_ROLES) can act on any recipe.
const userTeams = computed(() => authStore.user?.teams ?? [])
const isTeamScopedUser = computed(() =>
  (constants.TEAM_ROLES as readonly string[]).includes(authStore.user?.role ?? ''),
)

function isRecipeInEditScope(recipe: RecipeLight): boolean {
  if (!isTeamScopedUser.value) return true
  return recipe.teams?.some((team) => userTeams.value.includes(team.name)) ?? false
}

function recipeRowProps({
  internalItem,
  item,
}: {
  internalItem?: { raw?: RecipeLight }
  item?: RecipeLight
}): Record<string, unknown> {
  const recipe = internalItem?.raw ?? item
  if (recipe && !isRecipeInEditScope(recipe)) {
    return { class: 'recipe-readonly-row' }
  }
  return {}
}

function onUpdateOptions(options: { page: number; itemsPerPage: number }) {
  const query = { ...route.query }
  if (options.page > 1) {
    query.page = options.page.toString()
  } else {
    delete query.page
  }

  router.push({ query })

  // Emit limit change when it actually changes as the query would be the
  // same and we need to reload the data.
  if (options.itemsPerPage != props.paginator.limit) {
    emit('limitChanged', options.itemsPerPage)
  }
}

function handleSelectionChange(selection: string[]) {
  // Team-scoped accounts can only act on recipes owned by one of their teams, so
  // drop the non-editable names of the current page from the selection.
  const readOnlyNames = new Set(
    props.recipes.filter((recipe) => !isRecipeInEditScope(recipe)).map((recipe) => recipe.name),
  )
  emit(
    'selectionChanged',
    selection.filter((name) => !readOnlyNames.has(name)),
  )
}

function promptClearSelections() {
  showClearConfirm.value = true
}

function clearSelections() {
  emit('selectionChanged', [])
  showClearConfirm.value = false
}
</script>

<style scoped>
.recipe-succeeded {
  color: #4caf50;
}

.recipe-failed {
  color: #f44336;
}

.recipe-running {
  color: #ff9800;
}

:deep(.v-data-table__tr--mobile > td) {
  grid-template-columns: 1fr 3fr !important;
}

:deep(.recipe-readonly-row) {
  opacity: 0.6;
}
</style>
