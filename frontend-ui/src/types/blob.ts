export interface Blob {
  id: string
  flag_name: string
  kind: string
  url: string
  checksum: string
  comments: string
  created_at: string
}

export interface CreateBlob {
  flag_name: string
  kind: string
  data: string
  comments: string
}
