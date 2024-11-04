export interface FileNode {
  id: number;
  name: string;
  type: 'file' | 'folder';
  mime_type?: string;
  children?: FileNode[];
} 