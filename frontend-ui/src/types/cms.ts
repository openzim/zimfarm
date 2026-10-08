export interface CmsBook {
  id: string
  title_id?: string
  title_name?: string
  created_at: string
  location_kind: 'quarantine' | 'staging' | 'prod'
  name?: string
  date?: string
  flavour: string
}

export interface CmsZimfarmNotification {
  id: string
  task_id: string
  book_id?: string
  status?: string
  received_at: string
}

export type CmsTargetKind = 'book' | 'notification'

export interface CmsTarget {
  kind: CmsTargetKind
  id: string
  /** URL of the resource in the CMS UI */
  url: string
}
