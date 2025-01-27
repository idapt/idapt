export interface DatasourceResponse {
  identifier: string;
  name: string;
  type: string;
  description: string;
  settings_json: string;
  embedding_setting_identifier: string;
  created_at: number;
  updated_at: number;
}

export interface DatasourceCreate {
  name: string;
  type: string;
  description?: string;
  settings_json?: string;
  embedding_setting_identifier?: string;
}

export interface DatasourceUpdate {
  description?: string;
  embedding_setting_identifier?: string;
}