from pydantic import BaseModel
from typing import List

class ProcessingItem(BaseModel):
    original_path: str
    stacks_identifiers_to_queue: List[str]

class ProcessingRequest(BaseModel):
    items: List[ProcessingItem]