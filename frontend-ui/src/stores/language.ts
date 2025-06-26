import { defineStore } from "pinia";
import { inject, ref } from "vue";
import { type LanguageSchema } from "@/types/language";
import constants from "@/constants";
import type { Config } from "@/config";
import type { ListResponse } from "@/types/base";
import httpRequest from "@/utils/httpRequest";

export const useLanguageStore = defineStore("language", () => {
  const languages = ref<LanguageSchema[]>([]);
  const error = ref<Error | null>(null);

  const config = inject<Config>(constants.config)

  if (!config) {
    throw new Error("Config is not defined");
  }

  const service = httpRequest({
    baseURL: `${config.ZIMFARM_WEBAPI}/languages`,
  });

  const fetchLanguages = async (limit: number = 100) => {
    try {
      const response = await service.get<null, ListResponse<LanguageSchema>>("", { params: { limit } })
      languages.value = response.items;
    } catch (_error) {
      console.error("Failed to fetch languages", _error);
      error.value = _error as Error;
    }
  };

  return {
    languages,
    error,
    fetchLanguages,
  };
});
