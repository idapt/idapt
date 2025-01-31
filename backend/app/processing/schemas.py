from pydantic import BaseModel
from typing import List, Literal

class ProcessingItem(BaseModel):
    original_path: str
    stacks_identifiers_to_queue: List[str]

class ProcessingRequest(BaseModel):
    items: List[ProcessingItem]


class ItemProcessingStatusResponse(BaseModel):
    original_path: str
    name: str
    queued_stacks: List[str]
    status: Literal['pending', 'processing', 'queued', 'completed', 'error']

class ProcessingStatusResponse(BaseModel):
    queued_count: int
    queued_items: List[ItemProcessingStatusResponse]
    processing_count: int
    processing_items: List[ItemProcessingStatusResponse]
