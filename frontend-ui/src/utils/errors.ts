import { type ErrorResponse } from '@/types/errors'

export function translateErrors(error: ErrorResponse) {
  // build up a list of the errors
  const errors = []
  if (error.errors) {
    for (const _error of Object.values(error.errors)) {
      for (const error of _error) {
        errors.push(error)
      }
    }
    return errors
  }

  if (error.message) {
    return [error.message]
  }

  return ['An unknown error occurred']
}
