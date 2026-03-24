<template>
  <v-card elevation="2" class="h-100 d-flex flex-column border">
    <v-card-title class="d-flex flex-column align-start pa-4">
      <div class="d-flex align-center flex-wrap w-100">
        <div class="text-subtitle-1 text-truncate flex-grow-1">
          {{ displayName }}
        </div>

        <div v-if="file.info === undefined" class="text-caption text-grey ml-2">
          Loading metadata...
        </div>
      </div>

      <div v-if="file.info?.metadata" class="d-flex align-center flex-wrap mt-2 ga-2">
        <v-chip v-if="file.info.metadata.Flavour" size="small" variant="tonal" color="primary">
          {{ file.info.metadata.Flavour }}
        </v-chip>

        <v-chip v-if="file.info.metadata.Date" size="small" variant="outlined">
          <v-icon start size="small">mdi-calendar</v-icon>
          {{ file.info.metadata.Date }}
        </v-chip>
      </div>
    </v-card-title>

    <v-divider />

    <v-card-text class="pa-4">
      <div class="d-flex flex-column ga-2">
        <div class="d-flex justify-space-between align-center">
          <div class="text-body-2 font-weight-medium">Size</div>
          <div class="text-body-2 font-weight-medium">
            {{ formattedBytesSize(file.size) }}
          </div>
        </div>

        <div class="d-flex justify-space-between align-center">
          <div class="text-body-2 font-weight-medium">Created After</div>
          <v-tooltip :text="formatDt(file.created_timestamp)">
            <template #activator="{ props: tooltipProps }">
              <div v-bind="tooltipProps" class="text-body-2 font-weight-medium">
                {{ createdAfterTime }}
              </div>
            </template>
          </v-tooltip>
        </div>

        <div class="d-flex justify-space-between align-center">
          <div class="text-body-2 font-weight-medium">Upload Duration</div>
          <v-tooltip v-if="file.uploaded_timestamp" :text="formatDt(file.uploaded_timestamp)">
            <template #activator="{ props: tooltipProps }">
              <div v-bind="tooltipProps" class="text-body-2 font-weight-medium">
                {{ uploadDurationTime }}
              </div>
            </template>
          </v-tooltip>
          <div v-else class="text-body-2 text-grey">-</div>
        </div>

        <div class="d-flex justify-space-between align-center">
          <div class="text-body-2 font-weight-medium">Quality Check</div>
          <div v-if="file.check_result !== undefined" class="d-flex align-center">
            <v-tooltip :text="`Return code: ${file.check_result}`">
              <template #activator="{ props: tooltipProps }">
                <v-icon
                  v-bind="tooltipProps"
                  :color="file.check_result === 0 ? 'success' : 'error'"
                  size="small"
                >
                  {{ file.check_result === 0 ? 'mdi-check-circle' : 'mdi-close-circle' }}
                </v-icon>
              </template>
            </v-tooltip>
            <v-btn
              v-if="file.check_filename"
              variant="text"
              size="x-small"
              class="ml-1 pa-0"
              :href="checksUrl"
              target="_blank"
              rel="noopener noreferrer"
              icon
              density="compact"
            >
              <v-icon size="small">mdi-download</v-icon>
            </v-btn>
          </div>
          <div v-else class="text-body-2 text-grey">-</div>
        </div>
      </div>
    </v-card-text>

    <v-divider />

    <v-card-actions class="pa-3 justify-end">
      <v-menu v-if="file.info" location="bottom" :close-on-content-click="false">
        <template #activator="{ props: menuProps }">
          <v-tooltip location="top">
            <template #activator="{ props: tooltipProps }">
              <v-btn v-bind="{ ...menuProps, ...tooltipProps }" variant="text" size="small" icon>
                <v-icon>mdi-information</v-icon>
              </v-btn>
            </template>
            <span>File Info</span>
          </v-tooltip>
        </template>
        <FileInfoTable :file-info="file.info" />
      </v-menu>

      <ZimUrlButtons v-if="file.zim_urls && file.zim_urls.length > 0" :urls="file.zim_urls" />
      <v-tooltip v-else location="top">
        <template #activator="{ props: tooltipProps }">
          <v-btn
            v-bind="tooltipProps"
            :href="fallbackDownloadUrl"
            target="_blank"
            variant="text"
            icon
            size="small"
          >
            <v-icon>mdi-download</v-icon>
          </v-btn>
        </template>
        <span>Download</span>
      </v-tooltip>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import FileInfoTable from '@/components/FileInfoTable.vue'
import ZimUrlButtons from '@/components/ZimUrlButtons.vue'
import type { Task, TaskFile } from '@/types/tasks'
import { formatDt, formatDurationBetween, formattedBytesSize } from '@/utils/format'
import { checkUrl } from '@/utils/offliner'
import { getTimestampStringForStatus } from '@/utils/timestamp'
import { computed } from 'vue'

// Props
interface Props {
  file: TaskFile
  task: Task
  kiwixDownloadUrl: string
  smAndDown: boolean
}

const props = defineProps<Props>()

const displayName = computed(() => {
  return props.file.info?.metadata?.Name || props.file.name
})

const createdAfterTime = computed(() => {
  return formatDurationBetween(
    getTimestampStringForStatus(props.task.timestamp, 'scraper_started'),
    props.file.created_timestamp,
  )
})

const uploadDurationTime = computed(() => {
  if (!props.file.uploaded_timestamp) return '-'
  return formatDurationBetween(props.file.created_timestamp, props.file.uploaded_timestamp)
})

const checksUrl = computed(() => {
  if (!props.file.check_filename) return ''
  return checkUrl(props.task, props.file.check_filename)
})

const fallbackDownloadUrl = computed(() => {
  return `${props.kiwixDownloadUrl}${props.task.config.warehouse_path}/${props.file.name}`
})
</script>
