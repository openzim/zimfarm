export interface ErrorResponse {
  success: boolean
  message: string
  errors?: Record<string, string>
}
