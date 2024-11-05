export interface FileNode {
  id: number;
  name: string;
  type: 'file' | 'folder';
  size?: string;
  mimeType?: string;
  createdAt: string;
  updatedAt: string;
  originalCreatedAt?: string;
  originalModifiedAt?: string;
  path?: string;
  parentId?: number | null;
} 