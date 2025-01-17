from pydantic import BaseModel
from typing import List, Optional

class FileUploadItem(BaseModel):
    relative_path_from_home: str  # Relative path from the user home directory
    base64_content: str  # Base64 content
    name: str  # Original file name
    file_created_at: float # Unix timestamp in milliseconds
    file_modified_at: float # Unix timestamp in milliseconds


class FileUploadRequest(BaseModel):
    items: List[FileUploadItem]


class FileUploadProgress(BaseModel):
    total: int
    current: int
    processed_items: List[str]
    status: str
    error: Optional[str] = None