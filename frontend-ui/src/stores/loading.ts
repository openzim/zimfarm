import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useLoadingStore = defineStore('loading', () => {
  const isLoading = ref(false)
  const loadingText = ref('')

  const setLoading = (payload: { status: boolean; text?: string }) => {
    isLoading.value = payload.status
    loadingText.value = payload.text || ''
  }

  const startLoading = (text?: string) => {
    setLoading({ status: true, text })
  }

  const stopLoading = () => {
    setLoading({ status: false })
  }

  return {
    isLoading,
    loadingText,
    setLoading,
    startLoading,
    stopLoading,
  }
})
