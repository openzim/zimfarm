export interface TeamLight {
  name: string
  is_private: boolean
}

export interface Team extends TeamLight {
  id: string
}

export interface TeamCreateSchema {
  name: string
  is_private: boolean
}

export interface TeamUpdateSchema {
  name?: string
  is_private?: boolean
  comment?: string
}

export interface TeamHistory {
  id: string
  comment: string | null
  author: string
  name: string | null
  created_at: string
  is_private: boolean
}
