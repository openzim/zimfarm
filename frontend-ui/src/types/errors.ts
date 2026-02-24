export interface ErrorResponse {
  success: boolean
  message: string
  errors?: Record<string, string>
}

export interface OAuth2ErrorRecord {
  id: string
  code: number
  status: string
  reason: string
  details: Record<string, string>
  message: string
}

export interface OAuth2ErrorResponse {
  code?: number
  error: string | OAuth2ErrorRecord
  error_description?: string
}
