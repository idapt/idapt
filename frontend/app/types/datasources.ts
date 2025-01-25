export interface Datasource {
  id: number;
  identifier: string;
  name: string;
  type: string;
  description: string;
  settings_json: string;
  embedding_provider: string;
  embedding_settings_json: string;
  created_at: number;
  updated_at: number;
}

export interface CreateDatasourceRequest {
  name: string;
  type: string;
  settings_json?: string;
  embedding_provider: string;
  embedding_settings_json?: string;
}
