from pydantic import BaseModel
from typing import List, Literal, Optional

class ProcessingItem(BaseModel):
    original_path: str
    stacks_identifiers_to_queue: List[str]

class ProcessingRequest(BaseModel):
    items: List[ProcessingItem]

class ProcessingStatusResponse(BaseModel):
    status: Literal["pending", "queued", "processing", "completed", "error"]
    message: Optional[str]
