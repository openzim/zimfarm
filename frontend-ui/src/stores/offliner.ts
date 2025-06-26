import { defineStore } from "pinia";
import { ref, inject } from "vue";
import httpRequest from "@/utils/httpRequest";
import type { ListResponse } from "@/types/base";
import type { Config } from "@/config";
import constants from "@/constants";

export const useOfflinerStore = defineStore("offliner", () => {
  const offliners = ref<string[]>([]);
  const error = ref<Error | null>(null);

  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error("Config is not defined");
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/offliners`,
  });

  const fetchOffliners = async (limit: number = 100) => {
    try {
      const response = await service.get<null, ListResponse<string>>("", { params: { limit } })
      offliners.value = response.items;
    } catch (_error) {
      console.error("Failed to fetch offliners", _error);
      error.value = _error as Error;
    }
  };

  return {
    offliners,
    error,
    fetchOffliners,
  };
});
