import { type ErrorResponse, type OAuth2ErrorResponse } from '@/types/errors'

export function translateErrors(error: ErrorResponse | OAuth2ErrorResponse) {
  // Handle OAuth2ErrorResponse
  if ('error' in error) {
    const errors = []

    if (typeof error.error === 'object') {
      if (error.error.message) {
        errors.push(error.error.message)
      }
      if (error.error.reason) {
        errors.push(error.error.reason)
      }
      if (errors.length > 0) {
        return errors
      }
    }

    if (typeof error.error === 'string') {
      errors.push(error.error)
    }

    // Add error_description if present
    if (error.error_description) {
      errors.push(error.error_description)
    }

    if (errors.length > 0) {
      return errors
    }
  }

  // Handle ErrorResponse
  if ('errors' in error && error.errors) {
    const errors = []
    if (error.message) {
      errors.push(error.message)
    }
    for (const [key, value] of Object.entries(error.errors)) {
      errors.push(`${key}: ${value}`)
    }
    return errors
  }

  if ('message' in error && error.message) {
    return [error.message]
  }

  return ['An unknown error occurred']
}
