export interface Paginator {
    count: number
    skip: number
    limit: number
    pageSize: number
}

export interface ListResponse<T> {
    meta: Paginator
    items: T[]
}
