<!-- Form to update a team's name, visibility and history comment -->
<template>
  <v-card class="mb-4">
    <v-card-text>
      <v-form @submit.prevent="submitForm">
        <v-row>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="form.name"
              label="Name"
              hint="Team's name"
              placeholder="Team name"
              variant="outlined"
              density="compact"
              persistent-hint
              :error-messages="nameError ? [nameError] : []"
              required
            />
          </v-col>

          <v-col cols="12" md="6">
            <SwitchButton
              v-model="form.is_private"
              label="Private team"
              details="Only team members and users with global roles can view or edit private team recipes."
              density="compact"
            />
          </v-col>

          <v-col cols="12">
            <v-text-field
              v-model="form.comment"
              label="Comment"
              hint="Reason for this change"
              placeholder="Optional comment"
              variant="outlined"
              density="compact"
              persistent-hint
            />
          </v-col>
        </v-row>

        <v-row class="mt-4">
          <v-col cols="12">
            <v-btn type="submit" color="primary" variant="elevated" :disabled="!hasChanges" block>
              Update Team
            </v-btn>
          </v-col>
        </v-row>
      </v-form>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import SwitchButton from '@/components/SwitchButton.vue'
import type { Team, TeamUpdateSchema } from '@/types/team'

interface Props {
  team: Team
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update-team', payload: TeamUpdateSchema): void
}>()

const form = ref({
  name: '',
  is_private: false,
  comment: '',
})

const nameError = computed(() => {
  if (!form.value.name.trim()) {
    return 'Name is required'
  }
  if (form.value.name.trim().length < 3) {
    return 'Name must be at least 3 characters long'
  }
  return null
})

const payload = computed<TeamUpdateSchema | null>(() => {
  const result: TeamUpdateSchema = {}

  if (form.value.name.trim() !== props.team.name) {
    if (nameError.value) {
      return null
    }
    result.name = form.value.name.trim()
  }

  if (form.value.is_private !== props.team.is_private) {
    result.is_private = form.value.is_private
  }

  // A comment only makes sense alongside an actual change
  if (Object.keys(result).length === 0) {
    return null
  }

  if (form.value.comment.trim()) {
    result.comment = form.value.comment.trim()
  }

  return result
})

const hasChanges = computed(() => payload.value !== null)

const submitForm = () => {
  if (payload.value) {
    emit('update-team', payload.value)
  }
}

const initializeForm = () => {
  form.value = {
    name: props.team.name,
    is_private: props.team.is_private,
    comment: '',
  }
}

watch(
  () => props.team,
  () => {
    initializeForm()
  },
  { deep: true },
)

onMounted(() => {
  initializeForm()
})
</script>
