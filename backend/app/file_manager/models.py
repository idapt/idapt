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


class FileResponse(BaseModel):
    id: int
    name: str
    path: str
    original_path: str
    mime_type: str | None = None
    size: int | None = None
    uploaded_at: float
    accessed_at: float
    file_created_at: float
    file_modified_at: float
    stacks_to_process: str | None = None
    processed_stacks: str | None = None
    error_message: str | None = None
    status: str

class FolderResponse(BaseModel):
    id: int
    name: str
    path: str
    original_path: str
    uploaded_at: float
    accessed_at: float

class FolderContentsResponse(BaseModel):
    files: list[FileResponse]
    folders: list[FolderResponse]