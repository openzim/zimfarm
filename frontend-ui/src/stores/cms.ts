import type { Config } from '@/config'
import constants from '@/constants'
import { useAuthStore } from '@/stores/auth'
import type { CmsBook, CmsTarget, CmsZimfarmNotification } from '@/types/cms'
import httpRequest from '@/utils/httpRequest'
import { defineStore } from 'pinia'
import { inject } from 'vue'

export const useCmsStore = defineStore('cms', () => {
  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error('Config is not defined')
  }

  const authStore = useAuthStore()

  const cmsApi = async () => {
    const token = await authStore.loadToken()
    const headers: Record<string, string> = {}
    // Zimfarm and the CMS share the same token provider for session and OAuth
    // auth, so the access token is forwarded as a bearer token.
    // This can help access the book/notification if they are
    // behind a permissions. Local accounts are Zimfarm-only
    // and cannot authenticate against the CMS.
    if (token && token.token_type !== 'local') {
      headers.Authorization = `Bearer ${token.access_token}`
    }
    return httpRequest({
      baseURL: config.CMS_API_URL,
      headers,
      withCredentials: false,
    })
  }

  const fetchBook = async (bookId: string): Promise<CmsBook | null> => {
    try {
      const service = await cmsApi()
      return await service.get<null, CmsBook>(`/books/${bookId}`)
    } catch (error) {
      console.error('Failed to fetch book from CMS', error)
      return null
    }
  }

  const fetchZimfarmNotification = async (
    bookId: string,
  ): Promise<CmsZimfarmNotification | null> => {
    try {
      const service = await cmsApi()
      return await service.get<null, CmsZimfarmNotification>(`/zimfarm-notifications/${bookId}`)
    } catch (error) {
      console.error('Failed to fetch zimfarm notification from CMS', error)
      return null
    }
  }

  const resolveCmsTarget = async (bookId: string): Promise<CmsTarget | null> => {
    if (!config.CMS_API_URL || !config.CMS_UI_URL || !bookId) return null

    const book = await fetchBook(bookId)
    if (book) {
      return {
        kind: 'book',
        id: bookId,
        url: `${config.CMS_UI_URL}/book/${bookId}`,
      }
    }

    const notification = await fetchZimfarmNotification(bookId)
    if (notification) {
      return {
        kind: 'notification',
        id: bookId,
        url: `${config.CMS_UI_URL}/zimfarm-notification/${bookId}`,
      }
    }

    return null
  }

  return {
    fetchBook,
    fetchZimfarmNotification,
    resolveCmsTarget,
  }
})
