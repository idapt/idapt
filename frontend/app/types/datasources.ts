export interface Datasource {
  id: number;
  identifier: string;
  name: string;
  type: string;
  description?: string;
  settings?: any;
  embedding_provider?: string;
  embedding_settings?: any;
  created_at: number;
  updated_at: number;
}

export interface CreateDatasourceRequest {
  name: string;
  type: string;
  settings: Record<string, any>;
  embedding_provider: string;
  embedding_settings: Record<string, any>;
}
