export interface FileNode {
  id: number;
  name: string;
  type: 'file' | 'folder';
  size?: string;
  modified?: string;
  path?: string;
  parentId?: number | null;
} 