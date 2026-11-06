import type { Choice, OfflinerDefinition } from '@/types/offliner'
import type { BlobKind } from '@/utils/blob'
import { byGrapheme } from 'split-by-grapheme'

export interface FlagField {
  label: string
  dataKey: string
  key: string
  type: string
  required: boolean
  description: string | null
  placeholder: string
  component: string
  options?: Array<Choice>
  step?: number | null
  min: number | null
  max: number | null
  min_graphemes: number | null
  max_graphemes: number | null
  pattern: string | null
  kind?: BlobKind
  allowRemoteUrl: boolean
}

export interface FlagVisibilityContext {
  dependentDataKeys: Map<string, string>
  enumFields: OfflinerDefinition[]
}

export function buildFlagFields(flagsDefinition: OfflinerDefinition[]): FlagField[] {
  return flagsDefinition.map((field) => {
    let component = 'text'
    let options: Array<Choice> | undefined
    let step: number | null = null

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
          dependents: choice.dependents,
        })) || undefined
    } else if (field.type === 'boolean') {
      component = 'switch'
    } else if (field.type === 'string-enum') {
      component = 'select'
      options =
        field.choices?.map((choice) => ({
          title: choice.title,
          value: choice.value,
          dependents: choice.dependents,
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
      type: field.type,
      required: field.required,
      description: field.description,
      min: field.min,
      max: field.max,
      min_graphemes: field.min_graphemes,
      max_graphemes: field.max_graphemes,
      pattern: field.pattern,
      placeholder: 'Not set',
      component,
      options,
      step,
      kind: field.kind,
      allowRemoteUrl: field.allow_remote_url,
    }
  })
}

export function getFieldRules(field: FlagField): Array<(value: unknown) => boolean | string> {
  const rules: Array<(value: unknown) => boolean | string> = []

  if (field.required) {
    rules.push((value: unknown) => {
      if (!value || value === '' || value === undefined || value === null) {
        return 'This field is required'
      }
      return true
    })
  }

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

  const shouldValidate = (value: unknown) => {
    return value !== null && value !== undefined && value !== ''
  }

  if (field.min_graphemes !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value) && typeof value === 'string') {
        if (value.split(byGrapheme).length < field.min_graphemes!) {
          return `Minimum length is ${field.min_graphemes} characters`
        }
      }
      return true
    })
  }

  if (field.max_graphemes !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value) && typeof value === 'string') {
        if (value.split(byGrapheme).length > field.max_graphemes!) {
          return `Maximum length is ${field.max_graphemes} characters`
        }
      }
      return true
    })
  }

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

  if (field.pattern !== null) {
    rules.push((value: unknown) => {
      if (shouldValidate(value) && typeof value === 'string') {
        try {
          const regex = new RegExp(field.pattern!)
          if (!regex.test(value)) {
            return `Value must match pattern: ${field.pattern}`
          }
        } catch {
          console.warn(`Invalid regex pattern for field ${field.dataKey}:`, field.pattern)
        }
      }
      return true
    })
  }

  return rules
}

export function getGraphemeCount(value: unknown): number {
  if (typeof value === 'string') {
    return value.split(byGrapheme).length
  }
  return 0
}

export function truncateToMaxGraphemes(value: string, maxLength: number): string {
  const graphemes = value.split(byGrapheme)
  if (graphemes.length <= maxLength) {
    return value
  }
  return graphemes.slice(0, maxLength).join('')
}

export function applyGraphemeLimit(field: FlagField, value: string): string {
  const trimmedValue = value?.trim() || value
  if (field.max_graphemes && typeof trimmedValue === 'string') {
    return truncateToMaxGraphemes(trimmedValue, field.max_graphemes)
  }
  return trimmedValue
}

export function buildFlagVisibilityContext(
  flagsDefinition: OfflinerDefinition[],
): FlagVisibilityContext {
  const dependentDataKeys = new Map<string, string>()
  for (const field of flagsDefinition) {
    dependentDataKeys.set(field.key, field.data_key)
    dependentDataKeys.set(field.data_key, field.data_key)
  }

  return {
    dependentDataKeys,
    enumFields: flagsDefinition.filter((field) => field.type === 'string-enum' && !!field.choices),
  }
}

export function isFlagFieldVisible(
  field: FlagField,
  context: FlagVisibilityContext,
  flags: Record<string, unknown>,
): boolean {
  let isDependent = false

  for (const enumField of context.enumFields) {
    if (!enumField.choices) continue
    const selectedValue = flags[enumField.data_key]

    for (const choice of enumField.choices) {
      const dependsOnField = choice.dependents.some(
        (dependent) => context.dependentDataKeys.get(dependent) === field.dataKey,
      )
      if (!dependsOnField) continue

      isDependent = true
      if (choice.value === selectedValue) {
        return true
      }
    }
  }

  return !isDependent
}

export function isFlagValueSet(value: unknown): boolean {
  if (value === null || value === undefined || value === '') return false
  if (Array.isArray(value)) return value.length > 0
  return true
}

export function normalizeFlagValue(value: unknown): unknown {
  if (value === undefined || value === '') return null
  return value
}
