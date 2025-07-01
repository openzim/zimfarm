import type { BaseTask, ConfigWithOnlyOfflinerAndResources } from "@/types/base"


export interface RequestedTaskLight extends BaseTask{
    config: ConfigWithOnlyOfflinerAndResources
}
