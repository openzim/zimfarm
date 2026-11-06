<template>
  <div>
    <SwitchButton
      v-if="field.component === 'switch'"
      :model-value="modelValue"
      :label="label"
      :details="showHint ? (field.description ?? undefined) : undefined"
      density="compact"
      @update:model-value="emit('update:modelValue', $event)"
    />

    <v-select
      v-else-if="field.component === 'multiselect'"
      :model-value="modelValue"
      :items="field.options"
      multiple
      chips
      closable-chips
      density="compact"
      variant="outlined"
      :label="label"
      :placeholder="field.placeholder"
      :clearable="!field.required"
      :rules="getFieldRules(field)"
      :hide-details="hideDetails"
      :validate-on="'eager blur'"
      :hint="showHint ? (field.description ?? undefined) : undefined"
      :persistent-hint="showHint"
      @update:model-value="emit('update:modelValue', $event)"
    />

    <v-select
      v-else-if="field.component === 'select'"
      :model-value="modelValue"
      :items="field.options"
      density="compact"
      variant="outlined"
      :label="label"
      :placeholder="field.placeholder"
      :required="field.required"
      :clearable="!field.required"
      :rules="getFieldRules(field)"
      :hide-details="hideDetails"
      :validate-on="'blur'"
      :hint="showHint ? (field.description ?? undefined) : undefined"
      :persistent-hint="showHint"
      @update:model-value="emit('update:modelValue', $event)"
    />

    <v-text-field
      v-else-if="field.component === 'number'"
      :model-value="modelValue"
      type="number"
      density="compact"
      variant="outlined"
      :label="label"
      :placeholder="field.placeholder"
      :required="field.required"
      :step="field.step"
      :rules="getFieldRules(field)"
      :hide-details="hideDetails"
      :validate-on="'blur'"
      :hint="showHint ? (field.description ?? undefined) : undefined"
      :persistent-hint="showHint"
      @update:model-value="updateText"
    />

    <v-text-field
      v-else-if="field.component === 'url'"
      :model-value="modelValue"
      type="url"
      density="compact"
      variant="outlined"
      :label="label"
      :placeholder="field.placeholder"
      :required="field.required"
      :rules="getFieldRules(field)"
      :hide-details="hideDetails"
      :validate-on="'blur'"
      :hint="showHint ? (field.description ?? undefined) : undefined"
      :persistent-hint="showHint"
      @update:model-value="updateText"
    />

    <v-text-field
      v-else-if="field.component === 'email'"
      :model-value="modelValue"
      type="email"
      density="compact"
      variant="outlined"
      :label="label"
      :placeholder="field.placeholder"
      :required="field.required"
      :rules="getFieldRules(field)"
      :hide-details="hideDetails"
      :validate-on="'blur'"
      :hint="showHint ? (field.description ?? undefined) : undefined"
      :persistent-hint="showHint"
      @update:model-value="updateText"
    />

    <v-color-input
      v-else-if="field.component === 'color'"
      color-pip
      pip-variant="flat"
      :model-value="modelValue"
      density="compact"
      variant="outlined"
      mode="hex"
      :modes="['hex']"
      :label="label"
      :placeholder="field.placeholder"
      :required="field.required"
      :rules="getFieldRules(field)"
      :hide-details="hideDetails"
      :validate-on="'blur'"
      :hint="showHint ? (field.description ?? undefined) : undefined"
      :persistent-hint="showHint"
      @update:model-value="updateText"
    />

    <v-textarea
      v-else-if="field.component === 'textarea'"
      :model-value="modelValue"
      density="compact"
      variant="outlined"
      :label="label"
      :placeholder="field.placeholder"
      :required="field.required"
      auto-grow
      :rules="getFieldRules(field)"
      :hide-details="hideDetails"
      :validate-on="'blur'"
      :hint="showHint ? (field.description ?? undefined) : undefined"
      :persistent-hint="showHint"
      @update:model-value="updateText"
    >
      <template v-if="field.max_graphemes" #counter>
        {{ getGraphemeCount(modelValue) }}/{{ field.max_graphemes }}
      </template>
    </v-textarea>

    <BlobEditor
      v-else-if="field.component === 'blob' && recipeName"
      :model-value="modelValue"
      :label="label"
      :kind="field.kind"
      :required="field.required"
      :allow-remote-url="field.allowRemoteUrl"
      :description="showHint ? field.description : undefined"
      :recipe-name="recipeName"
      :flag-key="field.key"
      @update:model-value="emit('update:modelValue', $event)"
    />

    <v-text-field
      v-else
      :model-value="modelValue"
      type="text"
      density="compact"
      variant="outlined"
      :label="label"
      :placeholder="field.placeholder"
      :required="field.required"
      :rules="getFieldRules(field)"
      :hide-details="hideDetails"
      :validate-on="'blur'"
      :hint="showHint ? (field.description ?? undefined) : undefined"
      :persistent-hint="showHint"
      @update:model-value="updateText"
    >
      <template v-if="field.max_graphemes" #counter>
        {{ getGraphemeCount(modelValue) }}/{{ field.max_graphemes }}
      </template>
    </v-text-field>

    <div v-if="showYoutubeLinks" class="mt-1">
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
            <div class="text-body-small">
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
            <span class="text-body-small">Unknown YouTube ID format</span>
          </v-tooltip>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import BlobEditor from '@/components/BlobEditor.vue'
import SwitchButton from '@/components/SwitchButton.vue'
import type { FlagField } from '@/utils/offlinerFlags'
import { applyGraphemeLimit, getFieldRules, getGraphemeCount } from '@/utils/offlinerFlags'
import { buildYoutubeLinks, type YoutubeLinkKind } from '@/utils/youtube'
import { computed } from 'vue'

interface Props {
  field: FlagField
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  modelValue?: any
  offliner?: string
  recipeName?: string | null
  label?: string
  hideDetails?: boolean | 'auto'
  showHint?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  offliner: undefined,
  recipeName: null,
  label: undefined,
  hideDetails: 'auto',
  showHint: true,
})

const emit = defineEmits<{
  'update:modelValue': [value: unknown]
}>()

const isYoutubeOffliner = computed(() => props.offliner === 'youtube')
const isIdentField = computed(() => props.field.key === 'ident' || props.field.dataKey === 'id')

const youtubeIdentValue = computed(() => {
  if (!isYoutubeOffliner.value || !isIdentField.value) return ''
  return typeof props.modelValue === 'string' ? props.modelValue : ''
})

const youtubeLinkItems = computed(() => buildYoutubeLinks(youtubeIdentValue.value))

const showYoutubeLinks = computed(
  () =>
    isYoutubeOffliner.value &&
    isIdentField.value &&
    youtubeIdentValue.value.trim().length > 0 &&
    youtubeLinkItems.value.length > 0,
)

function updateText(value: string) {
  emit('update:modelValue', applyGraphemeLimit(props.field, value))
}

function getYoutubeLinkColor(kind: YoutubeLinkKind): string {
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

function getYoutubeLinkIcon(kind: YoutubeLinkKind): string {
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
</script>

<style scoped>
.youtube-link-chip {
  font-size: 0.8125rem;
  height: 24px;
}

.youtube-link-chip:hover {
  opacity: 0.85;
}
</style>
