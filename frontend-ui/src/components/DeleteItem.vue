<template>
  <v-alert type="error" variant="tonal" class="mb-4 mx-auto" width="auto">
    <div class="text-body-1 mb-2">
      You are about to <strong>permanently delete</strong> {{ description }} <code>{{ name }}</code
      >.
    </div>

    <v-form @submit.prevent="confirmDelete">
      <v-row dense>
        <v-col cols="12">
          <span class="text-body-2">
            Please type its <em>{{ property }}</em> to confirm:
          </span>
        </v-col>

        <v-col cols="12" sm="6">
          <v-text-field
            v-model="formName"
            :placeholder="`Type ${property} here`"
            density="compact"
            variant="outlined"
            hide-details
            autofocus
          />
        </v-col>

        <v-col cols="12" sm="6">
          <v-btn type="submit" :disabled="!ready" color="error" variant="elevated">
            delete {{ description }}
          </v-btn>
        </v-col>
      </v-row>
    </v-form>

    <!-- Confirmation Dialog -->
    <ConfirmDialog
      v-model="showConfirmDialog"
      :title="`Delete ${description}`"
      :message="`Are you absolutely sure you want to permanently delete ${description} '${name}'? This action cannot be undone.`"
      confirm-text="DELETE"
      cancel-text="CANCEL"
      confirm-color="error"
      icon="mdi-delete"
      icon-color="error"
      @confirm="handleConfirmDelete"
      @cancel="showConfirmDialog = false"
    />
  </v-alert>
</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { computed, ref } from 'vue'

// Props
const props = defineProps<{
  name: string
  description: string
  property: string
}>()

const emit = defineEmits<{
  (e: 'delete-item'): void
}>()

// Reactive data
const formName = ref('')
const showConfirmDialog = ref(false)

// Computed properties
const ready = computed(() => props.name && formName.value && props.name === formName.value)

// Methods
const confirmDelete = () => {
  if (ready.value) {
    showConfirmDialog.value = true
  }
}

const handleConfirmDelete = () => {
  emit('delete-item')
  showConfirmDialog.value = false
}
</script>
