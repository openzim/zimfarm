export interface ErrorResponse {
  success: boolean
  message: string
  errors?: Record<string, string>
}

export interface OAuth2ErrorResponse {
  code?: number
  error: string
  error_description?: string
}
