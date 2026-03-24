<template>
  <v-alert type="info" variant="tonal" class="mb-4 mx-auto" width="auto">
    <p class="text-body-1 mb-2">
      You are about to <strong>create a new recipe</strong> by cloning <code>{{ from }}</code
      >.
    </p>

    <v-form @submit.prevent="emit('clone', formName)">
      <v-row dense>
        <v-col cols="12">
          <span class="text-body=2"> Enter a (unique) <em>name</em> for this new recipe: </span>
        </v-col>

        <v-col cols="12" sm="6">
          <v-text-field
            v-model="formName"
            placeholder="Type new recipe name"
            size="small"
            variant="outlined"
            density="compact"
            autofocus
            :rules="[rules.required, rules.unique]"
            hide-details="auto"
          />
        </v-col>

        <v-col cols="12" sm="6">
          <v-btn type="submit" :disabled="!ready" color="primary" :loading="loading">
            create recipe
          </v-btn>
        </v-col>
      </v-row>
    </v-form>
  </v-alert>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

// Props
const props = defineProps({
  from: {
    type: String,
    required: true,
  },
})

const emit = defineEmits<{
  (e: 'clone', name: string): void
}>()

// Reactive data
const formName = ref('')
const loading = ref(false)

// Validation rules
const rules = {
  required: (value: string) => !!value || 'Recipe name is required',
  unique: (value: string) =>
    value !== props.from || 'Recipe name must be different from the original',
}

// Computed
const ready = computed(() => {
  return props.from && formName.value.trim() && props.from !== formName.value.trim()
})
</script>
