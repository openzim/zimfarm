<template>
  <v-alert
    :type="isArchived ? 'info' : 'warning'"
    variant="tonal"
    class="mb-4 mx-auto"
    width="auto"
  >
    <div class="text-body-1 mb-2">
      <template v-if="isArchived">
        You are about to <strong>restore</strong> recipe <code>{{ name }}</code
        >. This will make it available again for normal use.
      </template>
      <template v-else>
        You are about to <strong>archive</strong> recipe <code>{{ name }}</code
        >. This will hide it from the main recipe list but preserve all data.
      </template>
    </div>

    <v-form @submit.prevent="confirmAction">
      <v-row dense>
        <v-col cols="12">
          <span class="text-body-2"> Please type the recipe name to confirm: </span>
        </v-col>

        <v-col cols="12" sm="6">
          <v-text-field
            v-model="formName"
            placeholder="Type recipe name here"
            density="compact"
            variant="outlined"
            hide-details
            autofocus
          />
        </v-col>

        <v-col cols="12" sm="6">
          <v-btn
            type="submit"
            :disabled="!ready"
            :color="isArchived ? 'info' : 'warning'"
            variant="elevated"
            class="mr-2"
          >
            {{ isArchived ? 'Restore' : 'Archive' }} recipe
          </v-btn>
        </v-col>
      </v-row>
    </v-form>

    <!-- Archive/Restore Comment Dialog -->
    <ConfirmDialog
      v-model="showConfirmDialog"
      :title="`${isArchived ? 'Restore' : 'Archive'} recipe`"
      :confirm-text="isArchived ? 'Restore' : 'Archive'"
      cancel-text="Cancel"
      :confirm-color="isArchived ? 'info' : 'warning'"
      :icon="isArchived ? 'mdi-archive-arrow-up' : 'mdi-archive'"
      :max-width="600"
      :icon-color="isArchived ? 'info' : 'warning'"
      @confirm="handleConfirmAction"
      @cancel="showConfirmDialog = false"
    >
      <template #content>
        <div class="mb-4">
          <p class="text-body-2 text-medium-emphasis mb-3">
            {{
              isArchived
                ? `You are about to restore recipe '${name}'. This will make it available again for normal use. Please add an optional comment to track this action.`
                : `You are about to archive recipe '${name}'. This will hide it from the main recipe list but preserve all data. Please add an optional comment to track this action.`
            }}
          </p>
        </div>

        <!-- Comment Input -->
        <div>
          <v-textarea
            v-model="comment"
            label="Comment (optional)"
            :hint="
              isArchived
                ? 'Describe the reason for restoring this recipe'
                : 'Describe the reason for archiving this recipe'
            "
            placeholder="e.g., Archived due to maintenance, Restored after review, etc."
            variant="outlined"
            auto-grow
            rows="3"
            persistent-hint
          />
        </div>
      </template>
    </ConfirmDialog>
  </v-alert>
</template>

<script setup lang="ts">
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { computed, ref } from 'vue'

// Props
const props = defineProps<{
  name: string
  isArchived: boolean
}>()

const emit = defineEmits<{
  (e: 'archive-item', comment?: string): void
  (e: 'restore-item', comment?: string): void
}>()

// Reactive data
const formName = ref('')
const showConfirmDialog = ref(false)
const comment = ref('')

// Computed properties
const ready = computed(() => props.name && formName.value && props.name === formName.value)

// Methods
const confirmAction = () => {
  if (ready.value) {
    showConfirmDialog.value = true
  }
}

const handleConfirmAction = () => {
  if (props.isArchived) {
    emit('restore-item', comment.value.trim() || undefined)
  } else {
    emit('archive-item', comment.value.trim() || undefined)
  }
  showConfirmDialog.value = false
  comment.value = '' // Reset comment for next use
  formName.value = '' // Reset form name for next use
}
</script>
