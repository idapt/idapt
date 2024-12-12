export interface Datasource {
  id: number;
  name: string;
  type: string;
  settings?: any;
  created_at: number;
  updated_at: number;
}

export interface FolderContentsResponse {
  files: File[];
  folders: Folder[];
  datasource?: Datasource;  // Include datasource info when at root level
}

export interface File {
  id: number;
  name: string;
  path: string;
  mime_type?: string;
  size?: string;
  uploaded_at: number;
  accessed_at: number;
  file_created_at: number;
  file_modified_at: number;
}

export interface Folder {
  id: number;
  name: string;
  path: string;
  uploaded_at: number;
  accessed_at: number;
}