from pydantic import BaseModel
from typing import List, Optional

class FileUploadItem(BaseModel):
    path: str  # Relative path in the file system
    content: str  # Base64 content
    name: str  # Original file name
    file_created_at: float # Unix timestamp in milliseconds
    file_modified_at: float # Unix timestamp in milliseconds
    transformations_stack_name: Optional[str] = "default"


class FileUploadRequest(BaseModel):
    items: List[FileUploadItem]


class FileUploadProgress(BaseModel):
    total: int
    current: int
    processed_items: List[str]
    status: str
    error: Optional[str] = None