<template>
  <div>
    <!-- Error Message for permissions -->
    <ErrorMessage :message="error" v-if="error" />

    <!-- Content only shown if user has permission -->
    <div v-show="canRestore">
      <RecipesBaseView :archived="true" :route-name="'archived-recipes'" :can-request-tasks="false">
        <template #actions="{ selectedRecipes, restoringText, handleRestoreRecipes }">
          <RestoreSelectionButton
            v-if="canRestore"
            :can-restore="canRestore"
            :restoring-text="restoringText"
            :count="selectedRecipes.length"
            @restore-recipes="handleRestoreRecipes"
          />
        </template>
      </RecipesBaseView>
    </div>
  </div>
</template>

<script setup lang="ts">
import ErrorMessage from '@/components/ErrorMessage.vue'
import RestoreSelectionButton from '@/components/RestoreSelectionButton.vue'
import RecipesBaseView from '@/components/RecipesBaseView.vue'
import { useAuthStore } from '@/stores/auth'
import { computed, onMounted, ref } from 'vue'

// Stores
const authStore = useAuthStore()

// Reactive data
const error = ref<string | null>(null)

// Computed properties
const canRestore = computed(() => authStore.hasPermission('recipes', 'archive'))

// Lifecycle
onMounted(() => {
  if (!canRestore.value) {
    error.value = 'You do not have permission to view archived recipes.'
  }
})
</script>
