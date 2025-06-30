import { defineStore } from "pinia";
import { inject, ref } from "vue";
import httpRequest from "@/utils/httpRequest";
import type { Config } from "@/config";
import constants from "@/constants";
import type { ListResponse } from "@/types/base";

export const useTagStore = defineStore("tag", () => {
  const tags = ref<string[]>([]);
  const error = ref<Error | null>(null);

  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error("Config is not defined");
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/tags`,
  });

  const fetchTags = async (limit: number = 100) => {
    try {
      const response = await service.get<null, ListResponse<string>>("", { params: { limit } })
      tags.value = response.items;
    } catch (_error) {
      console.error("Failed to fetch tags", _error);
      error.value = _error as Error;
    }
  };

  return {
    tags,
    error,
    fetchTags,
  };
});
