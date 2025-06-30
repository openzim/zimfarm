import { defineStore } from "pinia";
import { ref, computed } from "vue";
import type { Token } from "@/types/user";

export const useUserStore = defineStore("user", () => {
  const token = ref<Token | null>(null);
  const loading = ref(false);
  const loadingText = ref("");

  // Computed properties
  const isLoggedIn = computed(() => {
    if (!token.value) return false;
    const now = Math.floor(Date.now() / 1000);
    return token.value.payload.exp > now;
  });

  const username = computed(() => {
    return token.value?.payload.user.username || null;
  });

  const accessToken = computed(() => {
    return token.value?.accessToken || null;
  });

  const refreshToken = computed(() => {
    return token.value?.refreshToken || null;
  });

  const permissions = computed(() => {
    return token.value?.payload.user.scope || {};
  });

  const loadingStatus = computed(() => {
    return {
      shouldDisplay: loading.value,
      text: loadingText.value
    };
  });

  // Methods
  const setLoading = (status: boolean, text?: string) => {
    loading.value = status;
    loadingText.value = text || "";
  };

  const saveToken = (tokenData: Token) => {
    token.value = tokenData;
  };

  const clearToken = () => {
    token.value = null;
  };

  const hasPermission = (resource: string, action: string) => {
    if (!token.value) return false;
    return token.value.payload.user.scope[resource]?.[action] || false;
  };

  return {
    // State
    token,
    loading,
    loadingText,

    // Computed
    isLoggedIn,
    username,
    accessToken,
    refreshToken,
    permissions,
    loadingStatus,

    // Methods
    setLoading,
    saveToken,
    clearToken,
    hasPermission,
  };
});
