export interface OfflinerDefinition {
  data_key: string
  secret?: boolean
  description: string | null
  choices:
    | {
        title: string
        value: string
      }[]
    | null
  label: string
  key: string
  required: boolean
  type: string
  min: number | null
  max: number | null
  min_graphemes: number | null
  max_graphemes: number | null
  pattern: string | null
  kind?: 'image' | 'illustration' | 'css' | 'html' | 'txt'
  allow_remote_url: boolean
}

export interface OfflinerDefinitionResponse {
  flags: OfflinerDefinition[]
  help: string
}
