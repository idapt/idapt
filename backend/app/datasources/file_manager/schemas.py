from pydantic import BaseModel
from typing import List, Optional

class FileUploadItem(BaseModel):
    original_path: str  # Relative path from the user home directory
    base64_content: str  # Base64 content
    name: str  # Original file name
    # TODO Do pydantic validation for the file creation and modification time
    file_created_at: float # Unix timestamp in milliseconds
    file_modified_at: float # Unix timestamp in milliseconds

class FileDownloadResponse(BaseModel):
    content: bytes
    media_type: str
    filename: str
    created_at: float
    modified_at: float

class FolderDownloadResponse(BaseModel):
    content: bytes
    filename: str
    mime_type: str

class FileInfoResponse(BaseModel):
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

class FolderInfoResponse(BaseModel):
    id: int
    name: str
    path: str
    original_path: str
    uploaded_at: float
    accessed_at: float
    child_folders: list['FolderInfoResponse'] | None = None
    child_files: list['FileInfoResponse'] | None = None

class UpdateFileProcessingStatusRequest(BaseModel):
    fs_path: str
    status: str
    stacks_to_process: List[str] | None = None
    stack_being_processed: str | None = None
    processed_stack: str | None = None
    error_message: str | None = None
    erroring_stack: str | None = None