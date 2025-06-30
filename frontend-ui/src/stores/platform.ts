import { defineStore } from "pinia";
import { inject, ref } from "vue";
import httpRequest from "@/utils/httpRequest";
import type { Config } from "@/config";
import constants from "@/constants";
import type { ListResponse } from "@/types/base";

export const usePlatformStore = defineStore("platform", () => {
  const platforms = ref<string[]>([]);
  const error = ref<Error | null>(null);

  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error("Config is not defined");
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/platforms`,
  });

  const fetchPlatforms = async (limit: number = 100) => {
    try {
      const response = await service.get<null, ListResponse<string>>("", { params: { limit } })
      platforms.value = response.items;
    } catch (_error) {
      console.error("Failed to fetch platforms", _error);
      error.value = _error as Error;
    }
  };

  return {
    platforms,
    error,
    fetchPlatforms,
  };
});
