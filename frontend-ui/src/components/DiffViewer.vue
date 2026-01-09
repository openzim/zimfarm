<template>
  <div>
    <template v-if="hasAnyDifferences">
      <v-card flat variant="outlined">
        <v-card-text class="pa-0">
          <div class="diff-content">
            <!-- Non-blob differences -->
            <template v-if="nonBlobDiffs.length > 0">
              <div
                v-for="(diff, index) in nonBlobDiffs"
                :key="`non-blob-${index}`"
                class="diff-line"
              >
                <v-card :class="getDiffLineClass(diff.type)" flat class="mb-1">
                  <v-card-text class="pa-1 font-monospace">
                    <div class="d-flex flex-column flex-sm-row mb-1 align-items-sm-center">
                      <div style="min-width: 150px">
                        <span class="diff-symbol text-center mr-1 font-weight-bold">{{
                          getDiffSymbol(diff.type)
                        }}</span>
                        <span class="text-caption text-high-emphasis mr-4 text-break">{{
                          diff.path
                        }}</span>
                      </div>
                      <div class="text-body-2 text-break flex-grow-1">
                        <template v-if="diff.type === 'modified' && diff.oldValue">
                          <span class="text-error">{{ diff.oldValue }}</span>
                          <span class="mx-2 text-medium-emphasis">→</span>
                          <span class="text-success">{{ diff.value }}</span>
                        </template>
                        <template v-else>
                          {{ diff.value }}
                        </template>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </div>
            </template>

            <!-- Blob differences with custom rendering -->
            <template v-if="blobDiffs.length > 0">
              <div v-for="(item, index) in blobDiffs" :key="`blob-${index}`" class="diff-line">
                <v-card :class="getDiffLineClass(item.type)" flat class="mb-1">
                  <v-card-text class="pa-1 font-monospace">
                    <div class="d-flex flex-column flex-sm-row mb-1 align-items-sm-center">
                      <div style="min-width: 150px">
                        <span class="diff-symbol text-center mr-1 font-weight-bold">{{
                          getDiffSymbol(item.type)
                        }}</span>
                        <span class="text-caption text-high-emphasis mr-4 text-break">{{
                          item.path
                        }}</span>
                      </div>

                      <!-- Simple format for small screens -->
                      <div class="text-body-2 text-break flex-grow-1 d-flex d-sm-none">
                        <v-chip size="x-small" color="info" variant="tonal" class="mr-2">
                          {{ item.blobKind }}
                        </v-chip>
                        <template v-if="item.type === 'modified' && item.oldBlobUrl">
                          <span class="text-error text-break">{{ item.oldBlobUrl }}</span>
                          <span class="mx-2 text-medium-emphasis">→</span>
                          <span class="text-success text-break">{{ item.newBlobUrl }}</span>
                        </template>
                        <template v-else>
                          <span class="text-break">{{ item.newBlobUrl || item.oldBlobUrl }}</span>
                        </template>
                      </div>

                      <!-- Enhanced viewer for larger screens -->
                      <div class="text-body-2 flex-grow-1 d-none d-sm-block">
                        <v-chip size="x-small" color="info" variant="tonal" class="mr-2">
                          {{ item.blobKind }}
                        </v-chip>
                        <v-btn
                          size="small"
                          variant="text"
                          color="primary"
                          @click="toggleExpanded(index)"
                        >
                          <v-icon>{{
                            isExpanded(index) ? 'mdi-chevron-up' : 'mdi-chevron-down'
                          }}</v-icon>
                          {{ isExpanded(index) ? 'Hide' : 'Show' }} Blob Comparison
                        </v-btn>
                      </div>
                    </div>

                    <!-- Expanded blob comparison (only on larger screens) -->
                    <div v-if="isExpanded(index)" class="mt-2 d-none d-sm-block">
                      <BlobDiffViewer
                        :old-blob-url="item.oldBlobUrl"
                        :new-blob-url="item.newBlobUrl"
                        :kind="item.blobKind!"
                        :field-name="item.path"
                      />
                    </div>
                  </v-card-text>
                </v-card>
              </div>
            </template>
          </div>
        </v-card-text>
      </v-card>
    </template>

    <!-- No differences message -->
    <template v-else>
      <v-card flat class="d-flex align-center justify-center" height="200">
        <v-card-text class="text-center text-medium-emphasis">
          <v-icon size="large" color="success" class="mb-2">mdi-check-circle</v-icon>
          <div class="text-h6">No differences found</div>
          <div class="text-body-2">The configurations are identical</div>
        </v-card-text>
      </v-card>
    </template>
  </div>
</template>

<script setup lang="ts">
import type * as DeepDiff from 'deep-diff'
import { computed, ref } from 'vue'
import BlobDiffViewer from '@/components/BlobDiffViewer.vue'
import type { EnhancedDiff, FlattenedDiff } from '@/utils/diff'
import { flattenDifferences, processPath, getDiffSymbol, getDiffLineClass } from '@/utils/diff'
import type { BlobKind } from '@/utils/blob'

interface BlobDiffItem {
  type: 'added' | 'removed' | 'modified'
  path: string
  blobKind: BlobKind
  oldBlobUrl: string | null
  newBlobUrl: string | null
}

interface Props {
  differences?: DeepDiff.Diff<Record<string, unknown>, Record<string, unknown>>[] | EnhancedDiff[]
}

const props = withDefaults(defineProps<Props>(), {
  differences: () => [],
})

// Track expanded state for blob items
const expandedItems = ref<Set<number>>(new Set())

const toggleExpanded = (index: number) => {
  if (expandedItems.value.has(index)) {
    expandedItems.value.delete(index)
  } else {
    expandedItems.value.add(index)
  }
}

const isExpanded = (index: number): boolean => {
  return expandedItems.value.has(index)
}

// Check if any difference has blob metadata
const hasEnhancedDiffs = computed(() => {
  if (!props.differences || props.differences.length === 0) return false
  return props.differences.some((diff) => 'isBlob' in diff)
})

// Separate blob and non-blob differences
const nonBlobDifferences = computed((): EnhancedDiff[] => {
  if (!hasEnhancedDiffs.value) return []
  return (props.differences as EnhancedDiff[]).filter((diff) => !diff.isBlob)
})

// Flatten diffs for display
const nonBlobDiffs = computed((): FlattenedDiff[] => {
  if (hasEnhancedDiffs.value) {
    // For enhanced diffs, flatten only non-blob diffs
    return flattenDifferences(
      nonBlobDifferences.value as DeepDiff.Diff<Record<string, unknown>, Record<string, unknown>>[],
    )
  } else {
    // For regular diffs, flatten all differences
    return flattenDifferences(
      props.differences as DeepDiff.Diff<Record<string, unknown>, Record<string, unknown>>[],
    )
  }
})

// Extract blob diffs
const blobDiffs = computed((): BlobDiffItem[] => {
  if (!hasEnhancedDiffs.value) return []

  const items: BlobDiffItem[] = []

  const processDiff = (diff: EnhancedDiff, basePath: (string | number)[] = []): void => {
    // Only process blob diffs
    if (!diff.isBlob || !diff.blobKind) return

    // Build complete path by combining base path with diff's specific path
    const fullPath = diff.path ? [...basePath, ...diff.path] : basePath
    const pathStr = processPath(fullPath)

    // Handle different types of changes
    switch (diff.kind) {
      case 'N': // New property added
        items.push({
          type: 'added',
          path: pathStr,
          blobKind: diff.blobKind,
          oldBlobUrl: null,
          newBlobUrl: diff.rhs ? String(diff.rhs) : null,
        })
        break

      case 'D': // Property deleted
        items.push({
          type: 'removed',
          path: pathStr,
          blobKind: diff.blobKind,
          oldBlobUrl: diff.lhs ? String(diff.lhs) : null,
          newBlobUrl: null,
        })
        break

      case 'E': // Property edited/changed
        items.push({
          type: 'modified',
          path: pathStr,
          blobKind: diff.blobKind,
          oldBlobUrl: diff.lhs ? String(diff.lhs) : null,
          newBlobUrl: diff.rhs ? String(diff.rhs) : null,
        })
        break

      case 'A': // Array change
        if (diff.item) {
          const arrayPath = [...fullPath, diff.index]
          processDiff(diff.item, arrayPath)
        }
        break
    }
  }

  ;(props.differences as EnhancedDiff[]).forEach((diff) => processDiff(diff))
  return items
})

const hasAnyDifferences = computed(() => {
  return nonBlobDiffs.value.length > 0 || blobDiffs.value.length > 0
})
</script>

<style scoped>
.diff-content {
  max-height: 900px;
  overflow-y: auto;
}

.diff-symbol {
  width: 20px;
  min-width: 20px;
  font-weight: bold;
  flex-shrink: 0;
}

.diff-line-added {
  background-color: rgba(46, 160, 67, 0.1);
  border-left: 3px solid #2ea043;
}

.diff-line-removed {
  background-color: rgba(248, 81, 73, 0.1);
  border-left: 3px solid #f85149;
}

.diff-line-modified {
  background-color: rgba(251, 188, 5, 0.1);
  border-left: 3px solid #fbbc05;
}

.diff-line-added .diff-symbol {
  color: #2ea043;
}

.diff-line-removed .diff-symbol {
  color: #f85149;
}

.diff-line-modified .diff-symbol {
  color: #fbbc05;
}
</style>
