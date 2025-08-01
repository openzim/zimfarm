export interface OfflinerDefinition {
  data_key: string;
  secret?: boolean;
  description: string | null;
  choices: {
    title: string;
    value: string;
  }[] | null;
  label: string;
  key: string;
  required: boolean;
  type: string;
}

export interface OfflinerDefinitionResponse {
  flags: OfflinerDefinition[];
  help: string;
}
