<template>
  <div>
    <template v-if="differences && differences.length > 0">
      <v-card flat variant="outlined">
        <v-card-text class="pa-0">
          <div class="diff-content">
            <div v-for="(diff, index) in flattenedDiffs" :key="index" class="diff-line">
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
          </div>
        </v-card-text>
      </v-card>
    </template>
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
import { computed } from 'vue'

const props = defineProps<{
  differences: DeepDiff.Diff<Record<string, unknown>, Record<string, unknown>>[] | undefined
}>()

interface FlattenedDiff {
  type: 'added' | 'removed' | 'modified'
  path: string
  value: string
  oldValue?: string
}

const flattenedDiffs = computed((): FlattenedDiff[] => {
  if (!props.differences) return []

  // Array to collect all processed diff lines for display
  const flattened: FlattenedDiff[] = []

  /**
   * Converts a path array into a readable dot notation string
   * Examples:
   * - ['config', 'resources', 'cpu'] → 'config.resources.cpu'
   * - ['tags', 0] → 'tags[0]'
   * - [] → 'root'
   */
  const processPath = (path: (string | number)[]): string => {
    if (path.length === 0) return 'root'
    return path.map((p) => (typeof p === 'number' ? `[${p}]` : p)).join('.')
  }

  /**
   * Formats different value types for display in the diff
   * - Strings get quotes: "hello"
   * - Objects/arrays get JSON representation (truncated if too long)
   * - Primitives (numbers, booleans) displayed as-is
   * - null/undefined shown as text
   */
  const formatValue = (value: unknown): string => {
    if (value === null) return 'null'
    if (value === undefined) return 'undefined'
    if (typeof value === 'string') return `"${value}"`
    if (typeof value === 'object') {
      const jsonStr = JSON.stringify(value)
      // Truncate very long JSON to keep diff readable
      if (jsonStr.length > 100) {
        return `${jsonStr.substring(0, 97)}...`
      }
      return jsonStr
    }
    return String(value)
  }

  const processDiff = (
    diff: DeepDiff.Diff<Record<string, unknown>, Record<string, unknown>>,
    basePath: (string | number)[] = [],
  ) => {
    // Build complete path by combining base path with diff's specific path
    const fullPath = diff.path ? [...basePath, ...diff.path] : basePath
    const pathStr = processPath(fullPath)

    // Handle different types of changes from deep-diff
    switch (diff.kind) {
      case 'N': // New property added
        flattened.push({
          type: 'added',
          path: pathStr,
          value: formatValue(diff.rhs), // rhs = right-hand side (new value)
        })
        break

      case 'D': // Property deleted
        flattened.push({
          type: 'removed',
          path: pathStr,
          value: formatValue(diff.lhs), // lhs = left-hand side (old value)
        })
        break

      case 'E': // Property edited/changed
        flattened.push({
          type: 'modified',
          path: pathStr,
          value: formatValue(diff.rhs), // New value
          oldValue: formatValue(diff.lhs), // Old value (for showing old → new)
        })
        break

      case 'A': // Array change (item added/removed/modified within array)
        if (diff.item) {
          // Create path that includes the array index where change occurred
          const arrayPath = [...fullPath, diff.index]
          // Recursively process the change within the array
          processDiff(diff.item, arrayPath)
        }
        break
    }
  }

  // Process each top-level difference and return the flattened list of all changes for rendering
  props.differences.forEach((diff) => processDiff(diff))
  return flattened
})

const getDiffSymbol = (type: string): string => {
  switch (type) {
    case 'added':
      return '+'
    case 'removed':
      return '-'
    case 'modified':
      return '±'
    default:
      return ' '
  }
}

const getDiffLineClass = (type: string): string => {
  switch (type) {
    case 'added':
      return 'diff-line-added'
    case 'removed':
      return 'diff-line-removed'
    case 'modified':
      return 'diff-line-modified'
    default:
      return ''
  }
}
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
