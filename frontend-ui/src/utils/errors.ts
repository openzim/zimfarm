import { type ErrorResponse } from '@/types/errors'

export function translateErrors(error: ErrorResponse) {
  // build up a list of the errors
  const errors = []
  if (error.errors) {
    if (error.message) {
      errors.push(error.message)
    }
    for (const [key, value] of Object.entries(error.errors)) {
      errors.push(`${key}: ${value}`)
    }
    return errors
  }

  if (error.message) {
    return [error.message]
  }

  return ['An unknown error occurred']
}
