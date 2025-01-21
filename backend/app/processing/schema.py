from pydantic import BaseModel, Field
from typing import List, Optional

class ProcessingItem(BaseModel):
    path: str = Field(..., example="path/to/item")
    transformations_stack_name_list: List[str] = Field(..., example=["default", "titles"])

class ProcessingRequest(BaseModel):
    items: List[ProcessingItem] = Field(..., example=[{
        "path": "path/to/item",
        "transformations_stack_name_list": ["default", "titles"]
    }])