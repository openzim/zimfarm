import type { BaseTask, ConfigWithOnlyResources } from "@/types/base"

export interface TaskLight extends BaseTask {
    config: ConfigWithOnlyResources
}
