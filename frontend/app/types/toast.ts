export type ToastItemStatus = 'pending' | 'processing' | 'completed' | 'error';

export interface BaseToastItem {
  id: string;
  name: string;
  path: string;
  status: ToastItemStatus;
  progress: number;
}

export interface UploadToastItem extends BaseToastItem {
  type: 'upload';
}

export interface DeletionToastItem extends BaseToastItem {
  type: 'deletion';
}

export interface ProcessingToastItem extends BaseToastItem {
  type: 'processing';
  total: number;
  processed: number;
}

export type ToastItem = UploadToastItem | DeletionToastItem | ProcessingToastItem; 