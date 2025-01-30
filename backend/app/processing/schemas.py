from pydantic import BaseModel
from typing import List
from app.datasources.file_manager.models import FileStatus

class ProcessingItem(BaseModel):
    original_path: str
    stacks_identifiers_to_queue: List[str]

class ProcessingRequest(BaseModel):
    items: List[ProcessingItem]


class ItemProcessingStatusResponse(BaseModel):
    original_path: str
    name: str
    queued_stacks: List[str]
    status: FileStatus

class ProcessingStatusResponse(BaseModel):
    queued_count: int
    processing_count: int
    processing_items: List[ItemProcessingStatusResponse]
