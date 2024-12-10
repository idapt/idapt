export interface FolderContentsResponse {
  files: File[];
  folders: Folder[];
}

export interface File {
  id: number;
  name: string;
  path: string;
  mime_type?: string;
  size?: string;
  created_at: string;
  updated_at: string;
  original_created_at?: string;
  original_modified_at?: string;
}

export interface Folder {
  id: number;
  name: string;
  path: string;
  created_at: string;
  updated_at: string;
  original_created_at?: string;
  original_modified_at?: string;
}