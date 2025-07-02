export interface ErrorResponse {
  success: boolean
  message: string
  errors?: {
    [key: string]: string[]
  }
}
