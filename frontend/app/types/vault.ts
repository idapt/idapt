export type ConflictResolution = 'overwrite' | 'skip' | 'overwrite_all' | 'skip_all';

export interface FileConflict {
  path: string;
  name: string;
} 