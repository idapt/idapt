from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class ProcessingStackStepCreate(BaseModel):
    step_identifier: str
    order: int
    parameters: dict

class ProcessingStackCreate(BaseModel):
    display_name: str
    description: Optional[str] = ""
    supported_extensions: Optional[List[str]] = []
    steps: Optional[List[ProcessingStackStepCreate]] = []

class ProcessingStepResponse(BaseModel):
    identifier: str
    display_name: str
    description: Optional[str] = None
    type: str
    parameters_schema: dict

class ProcessingStackStepResponse(BaseModel):
    id: int
    order: int
    parameters: Optional[dict] = None
    step_identifier: str
    step: ProcessingStepResponse

class ProcessingStackResponse(BaseModel):
    identifier: str
    display_name: str
    description: Optional[str] = ""
    supported_extensions: List[str]
    is_enabled: bool
    steps: List[ProcessingStackStepResponse]

class ProcessingStackStepUpdate(BaseModel):
    step_identifier: str
    order: int
    parameters: Optional[dict] = None

class ProcessingStackUpdate(BaseModel):
    steps: List[ProcessingStackStepUpdate]
    supported_extensions: List[str]

# Processing step parameters
# TODO: Move to a separate file
class SentenceSplitterParameters(BaseModel):
    chunk_size: int = Field(description="The size of the chunks to split the text into", default=512)
    chunk_overlap: int = Field(description="The overlap of the chunks to split the text into", default=128)

class ProcessingStepType(str, Enum):
    NODE_PARSER = "node_parser"
    NODE_POST_PROCESSOR = "node_post_processor"
    EMBEDDING = "embedding"
