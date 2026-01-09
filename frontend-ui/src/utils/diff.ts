import type * as DeepDiff from 'deep-diff'
import type { BlobKind } from '@/utils/blob'

/**
 * Enhanced diff type with blob metadata
 * Extends the base DeepDiff type to include information about blob fields
 */
export type EnhancedDiff<LHS = unknown, RHS = unknown> = DeepDiff.Diff<LHS, RHS> & {
  isBlob?: boolean
  blobKind?: BlobKind
}

/**
 * Converts a path array into a readable dot notation string
 * Examples:
 * - ['config', 'resources', 'cpu'] → 'config.resources.cpu'
 * - ['tags', 0] → 'tags[0]'
 * - [] → 'root'
 */
export const processPath = (path: (string | number)[]): string => {
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
export const formatValue = (value: unknown): string => {
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

/**
 * Returns the symbol to display for a diff type
 */
export const getDiffSymbol = (type: string): string => {
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

/**
 * Returns the CSS class for styling a diff line
 */
export const getDiffLineClass = (type: string): string => {
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

export interface FlattenedDiff {
  type: 'added' | 'removed' | 'modified'
  path: string
  value: string
  oldValue?: string
}

/**
 * Flattens deep-diff differences into a simple array for display
 */
export const flattenDifferences = (
  differences: DeepDiff.Diff<Record<string, unknown>, Record<string, unknown>>[] | undefined,
): FlattenedDiff[] => {
  if (!differences) return []

  const flattened: FlattenedDiff[] = []

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
  differences.forEach((diff) => processDiff(diff))
  return flattened
}
