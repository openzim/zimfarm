<template>
  <div>
    <p>You are about to <strong>create a new recipe</strong> by cloning <code>{{ from }}</code>.</p>
    <p>Enter a (unique) <em>name</em> for this new recipe:</p>

    <v-form @submit.prevent="emit('clone', formName)">
      <v-row no-gutters class="mt-3">
        <v-col cols="auto" class="mr-2">
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
        <v-col cols="auto">
          <v-btn
            type="submit"
            :disabled="!ready"
            color="primary"
            :loading="loading"
          >
            create recipe
          </v-btn>
        </v-col>
      </v-row>
    </v-form>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

// Props
const props = defineProps({
  from: {
    type: String,
    required: true
  }
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
  unique: (value: string) => value !== props.from || 'Recipe name must be different from the original'
}

// Computed
const ready = computed(() => {
  return props.from &&
         formName.value.trim() &&
         props.from !== formName.value.trim()
})
</script>
