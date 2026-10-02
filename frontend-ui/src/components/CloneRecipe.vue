<template>
  <div>
    <p class="text-body-1 mb-4">
      You are about to <strong>create a new recipe</strong> by cloning <code>{{ from }}</code
      >.
    </p>

    <v-form @submit.prevent="submit">
      <v-row dense>
        <v-col cols="12">
          <v-text-field
            v-model="formName"
            label="Recipe name"
            placeholder="Type a unique recipe name"
            variant="outlined"
            density="compact"
            autofocus
            :rules="[rules.required, rules.unique]"
            hide-details="auto"
          />
        </v-col>

        <v-col v-if="isTeamUser" cols="12">
          <v-select
            v-if="userTeams.length > 1"
            v-model="formTeams"
            :items="userTeams"
            label="Team(s)"
            placeholder="Select team(s)"
            variant="outlined"
            density="compact"
            multiple
            chips
            closable-chips
            :rules="[rules.teamsRequired]"
            hide-details="auto"
            persistent-hint
            hint="The cloned recipe will belong to the selected team(s)"
          />
          <v-text-field
            v-else
            :model-value="userTeams[0] ?? ''"
            label="Team"
            variant="outlined"
            density="compact"
            readonly
            persistent-hint
            hint="The cloned recipe will belong to this team"
          />
        </v-col>

        <v-col cols="12" class="d-flex justify-end">
          <v-btn type="submit" :disabled="!ready" color="primary" :loading="loading">
            create recipe
          </v-btn>
        </v-col>
      </v-row>
    </v-form>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import type { CloneRecipePayload } from '@/types/recipe'

// Props
const props = defineProps({
  from: {
    type: String,
    required: true,
  },
})

const emit = defineEmits<{
  (e: 'clone', payload: CloneRecipePayload): void
}>()

const authStore = useAuthStore()

// Reactive data
const formName = ref('')
const formTeams = ref<string[]>([])
const loading = ref(false)

const userTeams = computed(() => authStore.user?.teams ?? [])
const role = computed(() => authStore.user?.role ?? '')
const isTeamUser = computed(() => (constants.TEAM_ROLES as readonly string[]).includes(role.value))

watch(
  () => [isTeamUser.value, userTeams.value] as const,
  () => {
    if (isTeamUser.value && userTeams.value.length === 1) {
      formTeams.value = [userTeams.value[0]]
    }
  },
  { immediate: true },
)

// Validation rules
const rules = {
  required: (value: string) => !!value || 'Recipe name is required',
  unique: (value: string) =>
    value !== props.from || 'Recipe name must be different from the original',
  teamsRequired: (value: string[]) => value.length > 0 || 'Select at least one team',
}

// Computed
const ready = computed(() => {
  const name = formName.value.trim()
  if (!props.from || !name || props.from === name) return false
  if (isTeamUser.value && formTeams.value.length === 0) return false
  return true
})

const submit = () => {
  if (!ready.value) return
  emit('clone', {
    name: formName.value.trim(),
    teams: isTeamUser.value ? formTeams.value : undefined,
  })
}
</script>
