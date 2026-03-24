<template>
  <v-form @submit.prevent="handleSubmit" v-if="recipe">
    <div class="d-flex flex-column flex-sm-row justify-end ga-2 recipe-actions">
      <v-btn
        :disabled="!canSubmit"
        :color="canSubmit ? 'primary' : undefined"
        type="submit"
        variant="elevated"
      >
        Update Offliner details
      </v-btn>
      <v-btn type="button" :disabled="!hasChanges" variant="outlined" @click="handleReset">
        Reset
      </v-btn>
    </div>

    <v-divider class="my-4" />

    <v-row>
      <v-col cols="9">
        <h2>Content settings</h2>
      </v-col>
      <v-col cols="3" class="text-right">
        <v-btn
          href="https://github.com/openzim/zimfarm/wiki/Recipe-configuration-%E2%80%90-Content-settings"
          target="_blank"
          color="primary"
          variant="outlined"
        >
          Help
        </v-btn>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="4">
        <v-text-field
          v-model.trim="editRecipe.name"
          label="Recipe Name"
          hint="Recipe's identifier."
          placeholder="wikipedia_fr_all"
          required
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editRecipe.language.code"
          :items="languagesOptions"
          label="Language"
          hint="Use API if wanted language not present."
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editRecipe.tags"
          :items="tags"
          label="Tags"
          hint="Recipe tags, not ZIM tags. Use API to create others."
          multiple
          chips
          closable-chips
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editRecipe.category"
          :items="categoriesOptions"
          label="Category"
          density="compact"
          variant="outlined"
        />
      </v-col>
      <v-col cols="12" sm="4" v-if="!appConfig.DISABLE_WAREHOUSE_PATH">
        <v-select
          v-model="editRecipe.config.warehouse_path"
          :items="warehousePathsOptions"
          label="Warehouse Path"
          hint="Where to upload files. Usually matches category."
          required
          placeholder="Warehouse Path"
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <SwitchButton
          v-model="editRecipe.enabled"
          label="Status"
          density="compact"
          details="Disabled recipes are not scheduled, but can be run manually."
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editRecipe.periodicity"
          :items="periodicityOptions"
          label="Periodicity"
          hint="How often to automatically request recipe"
          required
          placeholder="Periodicity"
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-combobox
          v-model.trim="editRecipe.context"
          :items="contexts"
          label="Context"
          hint="Execute recipe only on workers associated with this context"
          placeholder="Context"
          :clearable="!!editRecipe.context"
          density="compact"
          variant="outlined"
          persistent-hint
          :menu-props="{ maxHeight: '200px' }"
          :custom-filter="(value, query) => fuzzyFilter(value, query, contexts)"
        />
      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <v-row>
      <v-col cols="9">
        <h2>Task settings</h2>
      </v-col>
      <v-col cols="3" class="text-right">
        <v-btn
          href="https://github.com/openzim/zimfarm/wiki/Recipe-configuration-%E2%80%90-Task-settings"
          target="_blank"
          color="primary"
          variant="outlined"
        >
          Help
        </v-btn>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editRecipe.config.offliner.offliner_id"
          :items="offlinersOptions"
          label="Offliner"
          hint="The kind of task to be run"
          density="compact"
          variant="outlined"
          @update:model-value="handleOfflinerChange"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editRecipe.config.platform"
          :items="platformsOptions"
          label="Platform"
          hint="The platform targetted by the offliner"
          clearable
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editRecipe.version"
          :items="offlinerVersions"
          label="Offliner Definition"
          hint="Version of the offliner definition flags to use"
          placeholder="Version"
          density="compact"
          variant="outlined"
          persistent-hint
          @update:model-value="
            handleOfflinerVersionChange(editRecipe.config.offliner.offliner_id, editRecipe.version)
          "
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="4">
        <v-text-field
          v-model.trim="editRecipe.config.image.name"
          label="Image Name"
          hint="Image name without tag (docker_repo/name)"
          placeholder="openzim/mwoffliner"
          required
          density="compact"
          variant="outlined"
          @update:model-value="debouncedImageNameChange"
          @blur="() => handleImageNameBlur(editRecipe.config.image.name)"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <v-select
          v-model="editRecipe.config.image.tag"
          :items="imageTagOptions"
          label="Image Tag"
          hint="Set image name first to get existing values"
          required
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="4">
        <SwitchButton
          v-model="editRecipe.config.monitor"
          details="Attach a monitoring companion to scraper"
          density="compact"
          label="Monitoring"
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" sm="3">
        <v-text-field
          v-model.trim="editRecipe.config.resources.cpu"
          label="CPU"
          hint="Number of CPU shares to use"
          type="number"
          min="1"
          max="100"
          required
          placeholder="3"
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="3">
        <v-select
          v-model="editRecipe.config.resources.memory"
          :items="memoryOptions"
          label="Memory"
          hint="Required memory. Use API for custom value."
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="3">
        <v-select
          v-model="editRecipe.config.resources.disk"
          :items="diskOptions"
          label="Disk"
          hint="Required disk space. Use API for custom value."
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
      <v-col cols="12" sm="3">
        <v-select
          v-model="editRecipe.config.resources.shm"
          :items="memoryOptions"
          label="RAM fs"
          hint="Amount of RAM to mount as /dev/shm. Constrained by RAM & Offliner."
          density="compact"
          variant="outlined"
          persistent-hint
        />
      </v-col>
    </v-row>

    <v-row>
      <v-col>
        <v-textarea
          v-model.trim="editRecipe.config.artifacts_globs_str"
          label="Artifacts"
          hint="! Experts only ! Beware to not include your ZIM files and logs ! Globs of artifacts to archive, one glob expression per line."
          variant="outlined"
          auto-grow
          persistent-hint
        />
      </v-col>
    </v-row>

    <v-divider class="my-4" />

    <template v-if="editRecipe.notification">
      <v-row>
        <v-col cols="12">
          <h2>Notification Settings</h2>
        </v-col>
      </v-row>

      <NotificationEventFields
        v-model="editRecipe.notification.requested"
        event-title="Requested Event"
      />

      <NotificationEventFields
        v-model="editRecipe.notification.started"
        event-title="Started Event"
      />

      <NotificationEventFields v-model="editRecipe.notification.ended" event-title="Ended Event" />
    </template>

    <v-divider class="my-4" />

    <v-row v-if="flagsFields.length > 0">
      <v-col cols="9">
        <h2>
          Scraper settings: <code>{{ taskName }}</code> command flags
        </h2>
      </v-col>
      <v-col cols="3" class="text-right">
        <v-btn :href="helpUrl" target="_blank" color="primary" variant="outlined"> Help </v-btn>
      </v-col>
    </v-row>

    <div v-if="flagsFields.length > 0">
      <v-row v-for="field in flagsFields" :key="field.dataKey" no-gutters class="py-2">
        <v-col
          cols="12"
          md="3"
          :class="[
            'align-self-start',
            'pt-2',
            {
              'd-none d-md-block':
                [
                  'text',
                  'number',
                  'url',
                  'email',
                  'blob',
                  'select',
                  'multiselect',
                  'textarea',
                  'color',
                ].includes(field.component) || field.component === undefined,
            },
          ]"
        >
          <div class="text-subtitle-2">
            {{ field.label }}
            <span v-if="field.required" class="text-red font-weight-bold text-subtitle-1">*</span>
          </div>
        </v-col>
        <v-col cols="12" md="9">
          <SwitchButton
            v-if="field.component === 'switch'"
            v-model="editFlags[field.dataKey]"
            density="compact"
            :details="field.description ?? undefined"
            persistent-hint
          />
          <v-select
            v-else-if="field.component === 'multiselect'"
            v-model="editFlags[field.dataKey]"
            :items="field.options"
            multiple
            chips
            closable-chips
            density="compact"
            variant="outlined"
            :label="smAndDown ? field.label + (field.required ? ' *' : '') : undefined"
            :placeholder="field.placeholder"
            :clearable="!field.required"
            :rules="getFieldRules(field)"
            :hide-details="'auto'"
            :validate-on="'eager blur'"
            :hint="field.description ?? undefined"
            persistent-hint
          />
          <v-select
            v-else-if="field.component === 'select'"
            v-model="editFlags[field.dataKey]"
            :items="field.options"
            density="compact"
            variant="outlined"
            :label="smAndDown ? field.label + (field.required ? ' *' : '') : undefined"
            :placeholder="field.placeholder"
            :required="field.required"
            :clearable="!field.required"
            :rules="getFieldRules(field)"
            :hide-details="'auto'"
            :validate-on="'blur'"
            :hint="field.description ?? undefined"
            persistent-hint
          />
          <v-text-field
            v-else-if="field.component === 'number'"
            v-model.trim="editFlags[field.dataKey]"
            type="number"
            density="compact"
            variant="outlined"
            :label="smAndDown ? field.label + (field.required ? ' *' : '') : undefined"
            :placeholder="field.placeholder"
            :required="field.required"
            :step="field.step"
            :rules="getFieldRules(field)"
            :hide-details="'auto'"
            :validate-on="'blur'"
            :hint="field.description ?? undefined"
            persistent-hint
          />
          <v-text-field
            v-else-if="field.component === 'url'"
            v-model.trim="editFlags[field.dataKey]"
            type="url"
            density="compact"
            variant="outlined"
            :label="smAndDown ? field.label + (field.required ? ' *' : '') : undefined"
            :placeholder="field.placeholder"
            :required="field.required"
            :rules="getFieldRules(field)"
            :hide-details="'auto'"
            :validate-on="'blur'"
            :hint="field.description ?? undefined"
            persistent-hint
          />
          <v-text-field
            v-else-if="field.component === 'email'"
            v-model.trim="editFlags[field.dataKey]"
            type="email"
            density="compact"
            variant="outlined"
            :label="smAndDown ? field.label + (field.required ? ' *' : '') : undefined"
            :placeholder="field.placeholder"
            :required="field.required"
            :rules="getFieldRules(field)"
            :hide-details="'auto'"
            :validate-on="'blur'"
            :hint="field.description ?? undefined"
            persistent-hint
          />
          <v-color-input
            v-else-if="field.component === 'color'"
            color-pip
            pip-variant="flat"
            v-model.trim="editFlags[field.dataKey]"
            density="compact"
            variant="outlined"
            mode="hex"
            :modes="['hex']"
            :label="smAndDown ? field.label + (field.required ? ' *' : '') : undefined"
            :placeholder="field.placeholder"
            :required="field.required"
            :rules="getFieldRules(field)"
            :hide-details="'auto'"
            :validate-on="'blur'"
            :hint="field.description ?? undefined"
            persistent-hint
          />
          <v-textarea
            v-else-if="field.component === 'textarea'"
            :model-value="editFlags[field.dataKey]"
            @update:model-value="(value) => handleInputWithGraphemeLimit(field, value)"
            density="compact"
            variant="outlined"
            :label="smAndDown ? field.label + (field.required ? ' *' : '') : undefined"
            :placeholder="field.placeholder"
            :required="field.required"
            auto-grow
            :rules="getFieldRules(field)"
            :hide-details="'auto'"
            :validate-on="'blur'"
            :hint="field.description ?? undefined"
            persistent-hint
          >
            <template v-if="field.max_length" #counter>
              {{ getGraphemeCount(editFlags[field.dataKey]) }}/{{ field.max_length }}
            </template>
          </v-textarea>
          <BlobEditor
            v-else-if="field.component === 'blob'"
            v-model="editFlags[field.dataKey]"
            :label="field.label"
            :kind="field.kind"
            :required="field.required"
            :description="field.description ?? undefined"
            :recipe-name="recipe.name"
            :flag-key="field.key"
          />
          <v-text-field
            v-else
            :model-value="editFlags[field.dataKey]"
            @update:model-value="(value) => handleInputWithGraphemeLimit(field, value)"
            density="compact"
            variant="outlined"
            :label="smAndDown ? field.label + (field.required ? ' *' : '') : undefined"
            :placeholder="field.placeholder"
            :required="field.required"
            :rules="getFieldRules(field)"
            :hide-details="'auto'"
            :validate-on="'blur'"
            :hint="field.description ?? undefined"
            persistent-hint
          >
            <template v-if="field.max_length" #counter>
              {{ getGraphemeCount(editFlags[field.dataKey]) }}/{{ field.max_length }}
            </template>
          </v-text-field>
          <div v-if="showYoutubeLinks && isIdentField(field)" class="mt-1">
            <div class="d-flex flex-wrap align-center" style="gap: 6px">
              <template v-for="item in youtubeLinkItems" :key="`${item.raw}-${item.kind}`">
                <v-tooltip v-if="item.url" location="top">
                  <template #activator="{ props: tooltipProps }">
                    <v-chip
                      v-bind="tooltipProps"
                      :href="item.url"
                      target="_blank"
                      rel="noopener noreferrer"
                      variant="tonal"
                      size="small"
                      :color="getYoutubeLinkColor(item.kind)"
                      :prepend-icon="getYoutubeLinkIcon(item.kind)"
                      class="youtube-link-chip"
                    >
                      {{
                        item.kind === 'handle'
                          ? item.raw
                          : item.raw.substring(0, 12) + (item.raw.length > 12 ? '...' : '')
                      }}
                    </v-chip>
                  </template>
                  <div class="text-caption">
                    {{ item.url }}
                  </div>
                </v-tooltip>
                <v-tooltip v-else location="top">
                  <template #activator="{ props: tooltipProps }">
                    <v-chip
                      v-bind="tooltipProps"
                      disabled
                      variant="outlined"
                      size="small"
                      color="grey"
                      prepend-icon="mdi-help-circle"
                      class="youtube-link-chip"
                    >
                      {{ item.raw.substring(0, 12) + (item.raw.length > 12 ? '...' : '') }}
                    </v-chip>
                  </template>
                  <span class="text-caption">Unknown YouTube ID format</span>
                </v-tooltip>
              </template>
            </div>
          </div>
        </v-col>
        <v-divider class="mt-1"></v-divider>
      </v-row>
    </div>

    <div class="d-flex flex-column flex-sm-row justify-end ga-2">
      <v-btn
        :disabled="!canSubmit"
        :color="canSubmit ? 'primary' : undefined"
        type="submit"
        variant="elevated"
      >
        Update Offliner details
      </v-btn>
      <v-btn type="button" :disabled="!hasChanges" variant="outlined" @click="handleReset">
        Reset
      </v-btn>
    </div>
  </v-form>
  <p v-else>Loading…</p>

  <!-- Recipe Update Confirmation Dialog -->
  <ConfirmDialog
    v-model="showConfirmDialog"
    title="Confirm Recipe Update"
    confirm-text="Save Changes"
    cancel-text="Cancel"
    confirm-color="primary"
    icon="mdi-pencil"
    icon-color="primary"
    :max-width="600"
    :loading="isSubmitting"
    @confirm="handleConfirmUpdate"
    @cancel="handleCancelUpdate"
  >
    <template #content>
      <div class="mb-4">
        <h3 class="text-h6 mb-2">Changes Summary</h3>
        <p class="text-body-2 text-medium-emphasis mb-3">
          Please review the changes below and optionally add a comment describing what you've
          modified.
        </p>
      </div>

      <!-- Similar Recipes Information -->
      <div v-if="loadingSimilarRecipes" class="mb-4">
        <v-alert type="info" variant="tonal" density="compact">
          <template #prepend>
            <v-progress-circular indeterminate size="16" />
          </template>
          Checking for similar recipes...
        </v-alert>
      </div>

      <div v-else-if="similarRecipesCount !== null && similarRecipesCount > 0" class="mb-4">
        <v-alert type="warning" variant="tonal" density="compact">
          <template #prepend>
            <v-icon>mdi-information</v-icon>
          </template>
          There are {{ similarRecipesCount }} similar recipe(s) to this recipe.
        </v-alert>
      </div>

      <!-- Diff Viewer -->
      <div class="mb-4">
        <DiffViewer :differences="recipeDifferences" />
      </div>

      <!-- Comment Input -->
      <div>
        <v-textarea
          v-model.trim="pendingComment"
          label="Comment (optional)"
          variant="outlined"
          auto-grow
          rows="3"
          persistent-hint
        />
      </div>
    </template>
  </ConfirmDialog>
</template>

<script setup lang="ts">
import BlobEditor from '@/components/BlobEditor.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DiffViewer from '@/components/DiffViewer.vue'
import type { Config } from '@/config'
import NotificationEventFields from '@/components/NotificationEventFields.vue'
import SwitchButton from '@/components/SwitchButton.vue'
import constants from '@/constants'
import { useNotificationStore } from '@/stores/notification'
import { useRecipeStore } from '@/stores/recipe'
import type { Resources } from '@/types/base'

import type { Language } from '@/types/language'
import type { OfflinerDefinition } from '@/types/offliner'
import type {
  EventNotification,
  Recipe,
  RecipeConfig,
  RecipeNotification,
  RecipeUpdateSchema,
} from '@/types/recipe'
import { fuzzyFilter, stringArrayEqual } from '@/utils/cmp'
import { formattedBytesSize } from '@/utils/format'
import { buildYoutubeLinks, type YoutubeLinkKind } from '@/utils/youtube'
import diff from 'deep-diff'
import { byGrapheme } from 'split-by-grapheme'
import { computed, onUnmounted, ref, watch, inject } from 'vue'
import { useDisplay } from 'vuetify'

interface FlagField {
  label: string
  dataKey: string
  required: boolean
  description: string | null
  placeholder: string
  component: string
  options?: Array<{ title: string; value: string | undefined }>
  step?: number | null
  min: number | null
  max: number | null
  min_length: number | null
  max_length: number | null
  pattern: string | null
  kind?: 'image' | 'illustration' | 'css' | 'html' | 'txt'
}

export interface Props {
  recipe: Recipe
  languages: Language[]
  tags: string[]
  contexts: string[]
  offliners: string[]
  platforms: string[]
  offlinerVersions: string[]
  flagsDefinition: OfflinerDefinition[]
  helpUrl: string
  imageTags: string[]
}

interface Emits {
  (e: 'submit', payload: RecipeUpdateSchema): void
  (e: 'image-name-change', imageName: string): void
  (e: 'offliner-change', offliner: string): void
  (e: 'offliner-version-change', offliner: string, version: string): void
}

// Config
const appConfig = inject<Config>(constants.config)
if (!appConfig) {
  throw new Error('Config is not defined')
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

// Stores
const recipeStore = useRecipeStore()
const notificationStore = useNotificationStore()
const { smAndDown } = useDisplay()
const editRecipe = ref<Recipe>(JSON.parse(JSON.stringify(props.recipe)))

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const editFlags = ref<Record<string, any>>(JSON.parse(JSON.stringify(props.recipe.config.offliner)))

// Confirmation dialog state
const showConfirmDialog = ref(false)
const isSubmitting = ref(false)
const pendingComment = ref('')
const similarRecipesCount = ref<number | null>(null)
const loadingSimilarRecipes = ref(false)

// Debounced image name change handler
let imageNameChangeTimeout: number | null = null
const lastEmittedImageName = ref<string>('')

const debouncedImageNameChange = (imageName: string) => {
  // Clear existing timeout
  if (imageNameChangeTimeout) {
    clearTimeout(imageNameChangeTimeout)
  }

  // Set new timeout to emit after 1s of no typing
  imageNameChangeTimeout = setTimeout(() => {
    if (imageName !== lastEmittedImageName.value) {
      lastEmittedImageName.value = imageName
      emit('image-name-change', imageName)
    }
  }, 1000)
}

const handleImageNameBlur = (imageName: string) => {
  // Clear any pending timeout
  if (imageNameChangeTimeout) {
    clearTimeout(imageNameChangeTimeout)
    imageNameChangeTimeout = null
  }

  // Immediately emit if the value has changed
  if (imageName !== lastEmittedImageName.value) {
    lastEmittedImageName.value = imageName
    emit('image-name-change', imageName)
  }
}

// Initialize edit data when recipe changes
watch(
  () => props.recipe,
  (newRecipe) => {
    if (newRecipe) {
      editRecipe.value = JSON.parse(JSON.stringify(newRecipe))
      editFlags.value = JSON.parse(JSON.stringify(newRecipe.config.offliner))
      // Initialize lastEmittedImageName with current recipe's image name
      lastEmittedImageName.value = newRecipe.config.image.name
    }
  },
  { deep: true, immediate: true },
)

watch(
  () => props.flagsDefinition,
  () => {
    const validDataKeys = new Set(props.flagsDefinition.map((field) => field.data_key))
    const sourceFlags: Record<string, unknown> = props.recipe.config.offliner
    const updatedFlags: Record<string, unknown> = {
      offliner_id: editRecipe.value.config.offliner.offliner_id,
    }

    for (const [key, value] of Object.entries(sourceFlags)) {
      if (validDataKeys.has(key)) {
        updatedFlags[key] = value
      }
    }
    editFlags.value = updatedFlags
  },
  { deep: true },
)

const handleOfflinerChange = (offliner: string) => {
  emit('offliner-change', offliner)
}

const handleOfflinerVersionChange = (offliner: string, version: string) => {
  if (version) {
    emit('offliner-version-change', offliner, version)
  }
}

// When parent provides new offliner versions, pick a default and emit version change
watch(
  () => props.offlinerVersions,
  (versions) => {
    if (!versions || !versions.length) return
    // offliner versions are updated when the offliner changes or the version dropdown
    // is changed
    if (editRecipe.value.config.offliner.offliner_id == props.recipe.config.offliner.offliner_id) {
      // offliner is changed, revert back to the original version
      editRecipe.value.version = props.recipe.version
    } else {
      // offliner is different, set the preferred version as the image tag
      // or the original version the recipe had. If none exist in new versions,
      // use the most recent version. This allows one to change from a different offliner
      // to the original and be on the same version as the original recipe.
      const preferred = versions.includes(editRecipe.value.config.image.tag)
        ? editRecipe.value.config.image.tag
        : props.recipe.version

      // if the preferred version is not in the new versions, use the most recent version
      editRecipe.value.version = versions.includes(preferred) ? preferred : versions[0]
    }
    handleOfflinerVersionChange(
      editRecipe.value.config.offliner.offliner_id,
      editRecipe.value.version,
    )
  },
  { deep: true },
)

// when the image tag changes, update the version if the recipe has the version
watch(
  () => editRecipe.value.config.image.tag,
  (newImageTag) => {
    if (newImageTag !== editRecipe.value.version && props.offlinerVersions.includes(newImageTag)) {
      editRecipe.value.version = newImageTag
      handleOfflinerVersionChange(editRecipe.value.config.offliner.offliner_id, newImageTag)
    }
  },
)
// Cleanup timeout on component unmount
onUnmounted(() => {
  if (imageNameChangeTimeout) {
    clearTimeout(imageNameChangeTimeout)
  }
})

const taskName = computed(() => {
  return editRecipe.value.config.offliner.offliner_id || props.recipe.config.offliner.offliner_id
})

// Helper function to compare event notifications
const eventNotificationsEqual = (
  a: EventNotification | null,
  b: EventNotification | null,
): boolean => {
  // Both null or undefined
  if (!a && !b) return true
  // One is null, other is not
  if (!a || !b) return false

  const arraysEqual = (arr1: string[] | null, arr2: string[] | null): boolean => {
    const a = arr1 && arr1.length > 0 ? arr1 : []
    const b = arr2 && arr2.length > 0 ? arr2 : []
    if (a.length === 0 && b.length === 0) return true
    return stringArrayEqual(a, b)
  }

  return (
    arraysEqual(a.mailgun, b.mailgun) &&
    arraysEqual(a.webhook, b.webhook) &&
    arraysEqual(a.slack, b.slack)
  )
}

// Helper function to compare recipe notifications
const notificationsEqual = (
  a: RecipeNotification | null,
  b: RecipeNotification | null,
): boolean => {
  // Both null or undefined
  if (!a && !b) return true
  // One is null, other is not
  if (!a || !b) return false

  return (
    eventNotificationsEqual(a.requested, b.requested) &&
    eventNotificationsEqual(a.started, b.started) &&
    eventNotificationsEqual(a.ended, b.ended)
  )
}

// Helper function to clean notification payload (convert empty arrays to null)
const cleanNotificationPayload = (
  notification: RecipeNotification | null,
): RecipeNotification | null => {
  if (!notification) return null

  const cleanEventNotification = (event: EventNotification | null): EventNotification | null => {
    if (!event) return null

    return {
      mailgun: event.mailgun && event.mailgun.length > 0 ? event.mailgun : null,
      webhook: event.webhook && event.webhook.length > 0 ? event.webhook : null,
      slack: event.slack && event.slack.length > 0 ? event.slack : null,
    }
  }

  return {
    requested: cleanEventNotification(notification.requested),
    started: cleanEventNotification(notification.started),
    ended: cleanEventNotification(notification.ended),
  }
}

// Helper function to validate a single field value against its rules
const validateFieldValue = (field: FlagField, value: unknown): boolean => {
  const rules = getFieldRules(field)

  for (const rule of rules) {
    const result = rule(value)
    if (result !== true) {
      return false // Validation failed
    }
  }

  return true // All rules passed
}

// Check if all flag fields are valid
const areAllFieldsValid = computed(() => {
  if (!flagsFields.value.length) return true

  for (const field of flagsFields.value) {
    const value = editFlags.value[field.dataKey]
    if (!validateFieldValue(field, value)) {
      return false
    }
  }

  return true
})

// Generate differences for the diff viewer
const recipeDifferences = computed(() => {
  if (!(props.recipe && editRecipe.value)) return undefined

  // Create a copy of the current recipe with the edited flags
  const currentRecipe = JSON.parse(JSON.stringify(props.recipe))
  const editedRecipe = JSON.parse(JSON.stringify(editRecipe.value))

  // Update the offliner config with the edited flags
  editedRecipe.config.offliner = JSON.parse(JSON.stringify(editFlags.value))

  // Generate diff
  return diff(currentRecipe, editedRecipe)
})

const canSubmit = computed(() => {
  return hasChanges.value && areAllFieldsValid.value
})

const hasChanges = computed<boolean>(() => {
  if (!(props.recipe && editRecipe.value)) return false

  // Check basic recipe properties
  const basicProps: Array<keyof Recipe> = ['category', 'name', 'enabled', 'periodicity']
  for (const prop of basicProps) {
    if (editRecipe.value[prop] !== props.recipe[prop]) return true
  }

  // Check version
  if (
    editRecipe.value.version &&
    props.recipe.version &&
    editRecipe.value.version !== props.recipe.version
  )
    return true

  // Check context with null/empty string equivalence
  const originalContext = props.recipe.context
  const editedContext = editRecipe.value.context
  if (originalContext !== editedContext) {
    // Consider null and empty string as equivalent
    if (
      !(
        (originalContext === null || originalContext === '') &&
        (editedContext === null || editedContext === '')
      )
    ) {
      return true
    }
  }

  // Check tags
  if (!stringArrayEqual(editRecipe.value.tags, props.recipe.tags)) return true

  // Check language
  if (editRecipe.value.language.code !== props.recipe.language.code) return true

  // Check config properties
  const configProps: Array<keyof RecipeConfig> = ['warehouse_path', 'platform', 'monitor']
  for (const prop of configProps) {
    if (editRecipe.value.config[prop] !== props.recipe.config[prop]) return true
  }

  // Check image
  if (
    editRecipe.value.config.image.name !== props.recipe.config.image.name ||
    editRecipe.value.config.image.tag !== props.recipe.config.image.tag
  )
    return true

  // Check resources
  const resourceProps: Array<keyof Resources> = ['cpu', 'memory', 'disk', 'shm']
  for (const prop of resourceProps) {
    if (editRecipe.value.config.resources[prop] !== props.recipe.config.resources[prop]) return true
  }

  // check offliner id
  if (editRecipe.value.config.offliner.offliner_id !== props.recipe.config.offliner.offliner_id)
    return true

  // Check artifacts globs
  const artifacts_globs = processArtifactsGlobs(editRecipe.value.config.artifacts_globs_str)

  if (!stringArrayEqual(artifacts_globs, props.recipe.config.artifacts_globs || [])) return true

  // Check notifications
  if (!notificationsEqual(editRecipe.value.notification, props.recipe.notification)) return true

  let changes = diff(props.recipe.config.offliner, editFlags.value)

  if (!changes) return false

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  changes = changes.filter(function (change: any) {
    // Filter out empty changes (new empty fields or fields changed to empty)
    if (
      change.kind === 'N' &&
      (change.rhs === '' || change.rhs === undefined || change.rhs === null)
    ) {
      return false
    }
    if (change.kind === 'E') {
      // if we are toggling a switch to false and it's a null on the original object,
      // then it's not a change
      if (change.lhs === null && change.rhs === false) return false
      // If changing from null/empty to null/empty, it's not a change
      if (
        (change.lhs === null || change.lhs === '') &&
        (change.rhs === undefined || change.rhs === null || change.rhs === '')
      ) {
        return false
      }
    }
    return true
  })
  return changes.length > 0
})

const flagsFields = computed(() => {
  if (!props.flagsDefinition) return []

  return props.flagsDefinition.map((field) => {
    let component = 'text'
    let options: Array<{ title: string; value: string | undefined }> | undefined = undefined
    let step = null

    if (field.type === 'color') {
      component = 'color'
    } else if (field.type === 'url') {
      component = 'url'
    } else if (field.type === 'email') {
      component = 'email'
    } else if (field.type === 'integer') {
      component = 'number'
      step = 1
    } else if (field.type === 'float') {
      component = 'number'
      step = 0.1
    } else if (field.type === 'list-of-string-enum') {
      component = 'multiselect'
      options =
        field.choices?.map((choice) => ({
          title: choice.title,
          value: choice.value,
        })) || undefined
    } else if (field.type === 'boolean') {
      component = 'switch'
    } else if (field.type === 'string-enum') {
      component = 'select'
      options =
        field.choices?.map((choice) => ({
          title: choice.title,
          value: choice.value,
        })) || undefined
    } else if (field.type === 'long-text') {
      component = 'textarea'
    } else if (field.type === 'blob') {
      component = 'blob'
    }

    return {
      label: field.label || field.data_key,
      dataKey: field.data_key,
      key: field.key,
      required: field.required,
      description: field.description,
      min: field.min,
      max: field.max,
      min_length: field.min_length,
      max_length: field.max_length,
      pattern: field.pattern,
      placeholder: 'Not set',
      component,
      options,
      step,
      kind: field.kind,
    }
  })
})

const isYoutubeOffliner = computed(() => {
  const selected = editRecipe.value.config.offliner.offliner_id
  const fallback = props.recipe.config.offliner.offliner_id
  return (selected || fallback) === 'youtube'
})

const youtubeIdentField = computed(() => {
  if (!isYoutubeOffliner.value) return null
  return flagsFields.value.find((field) => field.key === 'ident' || field.dataKey === 'id') || null
})

const youtubeIdentValue = computed(() => {
  const field = youtubeIdentField.value
  if (!field) return ''
  const value = editFlags.value[field.dataKey]
  return typeof value === 'string' ? value : ''
})

const youtubeLinkItems = computed(() => buildYoutubeLinks(youtubeIdentValue.value))

const showYoutubeLinks = computed(() => {
  return (
    isYoutubeOffliner.value &&
    !!youtubeIdentField.value &&
    youtubeIdentValue.value.trim().length > 0 &&
    youtubeLinkItems.value.length > 0
  )
})

const isIdentField = (field: FlagField) => {
  return field === youtubeIdentField.value
}

const getYoutubeLinkColor = (kind: YoutubeLinkKind): string => {
  switch (kind) {
    case 'channel':
      return 'red'
    case 'playlist':
      return 'blue'
    case 'video':
      return 'green'
    case 'handle':
      return 'purple'
    case 'unknown':
      return 'grey'
  }
}

const getYoutubeLinkIcon = (kind: YoutubeLinkKind): string => {
  switch (kind) {
    case 'channel':
      return 'mdi-account-circle'
    case 'playlist':
      return 'mdi-playlist-play'
    case 'video':
      return 'mdi-play-circle'
    case 'handle':
      return 'mdi-at'
    case 'unknown':
      return 'mdi-help-circle'
  }
}

const getFieldRules = (field: FlagField) => {
  const rules: Array<(value: unknown) => boolean | string> = []

  if (field.required) {
    rules.push((value: unknown) => {
      if (!value || value === '' || value === undefined || value === null) {
        return 'This field is required'
      }
      return true
    })
  }

  // Add type-specific validation
  if (field.component === 'url') {
    rules.push((value: unknown) => {
      if (value && typeof value === 'string' && value !== '') {
        try {
          new URL(value)
          return true
        } catch {
          return 'Please enter a valid URL'
        }
      }
      return true
    })
  }

  if (field.component === 'email') {
    rules.push((value: unknown) => {
      if (value && typeof value === 'string' && value !== '') {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
        if (!emailRegex.test(value)) {
          return 'Please enter a valid email address'
        }
      }
      return true
    })
  }

  if (field.component === 'number') {
    rules.push((value: unknown) => {
      if (value && value !== '') {
        const num = Number(value)
        if (isNaN(num)) {
          return 'Please enter a valid number'
        }
      }
      return true
    })
  }

  // Add validation for min, max, min_length, and pattern constraints
  const shouldValidate = (value: unknown) => {
    return value !== null && value !== undefined && value !== ''
  }

  // Min length validation
  if (field.min_length !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value) && typeof value === 'string') {
        if (value.split(byGrapheme).length < field.min_length!) {
          return `Minimum length is ${field.min_length} characters`
        }
      }
      return true
    })
  }

  // Max length validation
  if (field.max_length !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value) && typeof value === 'string') {
        if (value.split(byGrapheme).length > field.max_length!) {
          return `Maximum length is ${field.max_length} characters`
        }
      }
      return true
    })
  }

  // Min value validation (for numbers)
  if (field.min !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value)) {
        const num = Number(value)
        if (!isNaN(num) && num < field.min!) {
          return `Minimum value is ${field.min}`
        }
      }
      return true
    })
  }

  // Max value validation (for numbers)
  if (field.max !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value)) {
        const num = Number(value)
        if (!isNaN(num) && num > field.max!) {
          return `Maximum value is ${field.max}`
        }
      }
      return true
    })
  }

  // Pattern validation (regex)
  if (field.pattern !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value) && typeof value === 'string') {
        try {
          // construct the regex from the pattern string
          const regex = new RegExp(field.pattern!)
          if (!regex.test(value)) {
            return `Value must match pattern: ${field.pattern}`
          }
        } catch {
          // If regex is invalid, skip validation
          console.warn(`Invalid regex pattern for field ${field.dataKey}:`, field.pattern)
        }
      }
      return true
    })
  }

  return rules
}

const getGraphemeCount = (value: unknown): number => {
  if (typeof value === 'string') {
    return value.split(byGrapheme).length
  }
  return 0
}

const truncateToMaxGraphemes = (value: string, maxLength: number): string => {
  const graphemes = value.split(byGrapheme)
  if (graphemes.length <= maxLength) {
    return value
  }
  return graphemes.slice(0, maxLength).join('')
}

const handleInputWithGraphemeLimit = (field: FlagField, value: string) => {
  const trimmedValue = value?.trim() || value
  if (field.max_length && typeof trimmedValue === 'string') {
    const truncatedValue = truncateToMaxGraphemes(trimmedValue, field.max_length)
    editFlags.value[field.dataKey] = truncatedValue
  } else {
    editFlags.value[field.dataKey] = trimmedValue
  }
}

const languagesOptions = computed(() => {
  return props.languages.map((language) => ({
    title: language.name,
    value: language.code,
  }))
})

const categoriesOptions = computed(() => {
  return constants.CATEGORIES.map((category) => ({
    title: category,
    value: category,
  }))
})

const warehousePathsOptions = computed(() => {
  return constants.WAREHOUSE_PATHS.map((path) => ({
    title: path,
    value: path,
  }))
})

const offlinersOptions = computed(() => {
  return props.offliners.map((offliner) => ({
    title: offliner,
    value: offliner,
  }))
})

const platformsOptions = computed(() => {
  const values: Array<{ title: string; value: string | undefined }> = props.platforms.map(
    (platform) => ({
      title: platform,
      value: platform,
    }),
  )
  return values
})

const periodicityOptions = computed(() => {
  return constants.PERIODICITIES.map((periodicity) => ({
    title: periodicity,
    value: periodicity,
  }))
})

const memoryOptions = computed(() => {
  const values = [...constants.MEMORY_VALUES]
  if (values.indexOf(editRecipe.value.config.resources.memory) === -1) {
    values.push(editRecipe.value.config.resources.memory)
  }
  values.sort((a, b) => a - b)
  return values.map((value) => ({ title: formattedBytesSize(value), value }))
})

const diskOptions = computed(() => {
  const values = [...constants.DISK_VALUES]
  if (values.indexOf(editRecipe.value.config.resources.disk) === -1) {
    values.push(editRecipe.value.config.resources.disk)
  }
  values.sort((a, b) => a - b)
  return values.map((value) => ({ title: formattedBytesSize(value), value }))
})

const imageTagOptions = computed(() => {
  return [...props.imageTags].sort().map((tag) => ({ title: tag, value: tag }))
})

const fetchSimilarRecipesCount = async () => {
  if (!props.recipe) return

  loadingSimilarRecipes.value = true
  similarRecipesCount.value = null

  try {
    const response = await recipeStore.fetchSimilarRecipes(props.recipe.name, {
      limit: 1, // We only need the count
      skip: 0,
      archived: false,
    })

    if (response) {
      similarRecipesCount.value = response.meta.count
    }
  } catch (error) {
    console.error('Failed to fetch similar recipes count:', error)
    similarRecipesCount.value = 0
    for (const error of recipeStore.errors) {
      notificationStore.showError(error)
    }
  } finally {
    loadingSimilarRecipes.value = false
  }
}

const handleSubmit = async () => {
  if (!canSubmit.value) return

  // Fetch similar recipes count before showing confirmation dialog
  await fetchSimilarRecipesCount()

  // Show confirmation dialog instead of directly submitting
  showConfirmDialog.value = true
}

const handleReset = () => {
  if (props.recipe) {
    editRecipe.value = JSON.parse(JSON.stringify(props.recipe))
    editFlags.value = JSON.parse(JSON.stringify(props.recipe.config.offliner))
    // reset the flags and fields
    handleOfflinerVersionChange(props.recipe.config.offliner.offliner_id, props.recipe.version)
  }
}

const handleConfirmUpdate = async () => {
  if (isSubmitting.value) return

  isSubmitting.value = true

  try {
    const payload = buildPayload()
    if (payload) {
      emit('submit', payload)
    }
  } finally {
    isSubmitting.value = false
    showConfirmDialog.value = false
    pendingComment.value = ''
    similarRecipesCount.value = null
    loadingSimilarRecipes.value = false
  }
}

const handleCancelUpdate = () => {
  showConfirmDialog.value = false
  pendingComment.value = ''
  similarRecipesCount.value = null
  loadingSimilarRecipes.value = false
}

const processArtifactsGlobs = (artifactsGlobsStr: string | undefined): string[] => {
  return artifactsGlobsStr
    ? artifactsGlobsStr
        .split('\n')
        .map((line) => line.trim())
        .filter((line) => line !== '')
    : []
}

const buildPayload = (): RecipeUpdateSchema | null => {
  const payload: Partial<RecipeUpdateSchema> = {}

  payload.name = editRecipe.value.name.trim()

  // Basic properties
  const basicProps: Array<keyof Recipe> = ['name', 'category', 'enabled', 'periodicity']
  for (const prop of basicProps) {
    if (editRecipe.value[prop] !== props.recipe[prop]) {
      if (prop === 'name') {
        payload.name = editRecipe.value[prop]
      } else if (prop === 'category') {
        payload.category = editRecipe.value[prop]
      } else if (prop === 'enabled') {
        payload.enabled = editRecipe.value[prop]
      } else if (prop === 'periodicity') {
        payload.periodicity = editRecipe.value[prop]
      }
    }
  }

  // Context with null/empty string equivalence
  const originalContext = props.recipe.context
  const editedContext = editRecipe.value.context
  if (originalContext !== editedContext) {
    // Consider null and empty string as equivalent
    if (
      !(
        (originalContext === null || originalContext === '') &&
        (editedContext === null || editedContext === '')
      )
    ) {
      // If edited context is null (because the user cleared the field), set it to an
      // empty string as the API expects a string. Null values are considered as unset.
      payload.context = editedContext || ''
    }
  }

  // Comment
  if (pendingComment.value?.trim()) {
    payload.comment = pendingComment.value.trim()
  }

  // Tags
  if (!stringArrayEqual(editRecipe.value.tags, props.recipe.tags)) {
    payload.tags = editRecipe.value.tags
  }

  // Language
  if (editRecipe.value.language.code !== props.recipe.language.code) {
    payload.language = editRecipe.value.language.code
  }

  // Config properties
  const configProps: Array<keyof RecipeConfig> = ['warehouse_path', 'platform', 'monitor']
  for (const prop of configProps) {
    if (editRecipe.value.config[prop] !== props.recipe.config[prop]) {
      if (prop === 'warehouse_path') {
        payload.warehouse_path = editRecipe.value.config[prop]
      } else if (prop === 'platform') {
        payload.platform = editRecipe.value.config[prop]
      } else if (prop === 'monitor') {
        payload.monitor = editRecipe.value.config[prop]
      }
    }
  }

  // Offliner name
  if (editRecipe.value.config.offliner.offliner_id !== props.recipe.config.offliner.offliner_id) {
    payload.offliner = editRecipe.value.config.offliner.offliner_id as string
  }

  // Image
  if (
    editRecipe.value.config.image.name !== props.recipe.config.image.name ||
    editRecipe.value.config.image.tag !== props.recipe.config.image.tag
  ) {
    payload.image = editRecipe.value.config.image
  }

  // Resources
  const resourceProps: Array<keyof Resources> = ['cpu', 'memory', 'disk', 'shm']
  const resourcesChanged = resourceProps.some(
    (prop) => editRecipe.value.config.resources[prop] !== props.recipe.config.resources[prop],
  )
  if (resourcesChanged) {
    payload.resources = editRecipe.value.config.resources
  }

  // Artifacts
  const artifacts_globs = processArtifactsGlobs(editRecipe.value.config.artifacts_globs_str)

  if (!stringArrayEqual(artifacts_globs, props.recipe.config.artifacts_globs || [])) {
    payload.artifacts_globs = artifacts_globs
  }

  // Notifications
  if (!notificationsEqual(editRecipe.value.notification, props.recipe.notification)) {
    payload.notification = cleanNotificationPayload(editRecipe.value.notification)
  }

  // Flags
  const flags = cleanFlagsPayload(JSON.parse(JSON.stringify(editFlags.value)))
  // remove the offliner_id from the flags as it is not used by the server and the schema is strict
  // server-side
  delete flags.offliner_id
  if (Object.keys(flags).length > 0) {
    payload.flags = flags
  }

  if (Object.keys(payload).length === 0) {
    return null
  }

  // Version
  payload.version = editRecipe.value.version

  return payload as RecipeUpdateSchema
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const cleanFlagsPayload = (flags: Record<string, any>) => {
  const cleaned = JSON.parse(JSON.stringify(flags))

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const recursivelyCleanup = (obj: any) => {
    for (const key in obj) {
      if (typeof obj[key] === 'object' && obj[key] !== null) {
        recursivelyCleanup(obj[key])
      } else if (
        !Array.isArray(obj) &&
        (obj[key] === '' || obj[key] === undefined || obj[key] === null)
      ) {
        // if an object is set to empty string, we update it to null as it should
        // be on the backend since fields are either set or not set and fields that
        // are set shouldn't be empty
        if (obj[key] == '') {
          obj[key] = null
        } else {
          delete obj[key]
        }
      }
    }
  }

  recursivelyCleanup(cleaned)
  return cleaned
}
</script>

<style type="text/css" scoped>
.align-top {
  align-self: start;
}

.youtube-link-chip {
  font-size: 0.8125rem;
  height: 24px;
}

.youtube-link-chip:hover {
  opacity: 0.85;
}
</style>
