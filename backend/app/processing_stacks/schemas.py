from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum

class ProcessingStackStepCreate(BaseModel):
    step_identifier: str
    order: int
    parameters: dict

class ProcessingStackCreate(BaseModel):
    display_name: str
    description: Optional[str] = None
    supported_extensions: Optional[List[str]] = None
    steps: List[ProcessingStackStepCreate]

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
    description: Optional[str] = None
    is_enabled: bool
    steps: List[ProcessingStackStepResponse]

class ProcessingStackStepUpdate(BaseModel):
    step_identifier: str
    order: int
    parameters: Optional[dict] = None

class ProcessingStackUpdate(BaseModel):
    steps: List[ProcessingStackStepUpdate]
    supported_extensions: Optional[List[str]] = None

    @field_validator('steps')
    def validate_steps_order(cls, steps):
        if not steps:
            return steps
            
        # Check if first step is node parser
        if steps[0].step_identifier != "node_parser" and steps[0].step_identifier != "embedding":
            raise ValueError("First step must be a node parser or embedding")
            
        # Check if last step is embedding
        if steps[-1].step_identifier != "embedding":
            raise ValueError("Last step must be an embedding")
            
        # Count node parsers and embeddings
        parser_count = sum(1 for step in steps if step.step_identifier == "node_parser")
        embedding_count = sum(1 for step in steps if step.step_identifier == "embedding")
        
        if parser_count != 1:
            raise ValueError("Exactly one node parser is required")
        if embedding_count != 1:
            raise ValueError("Exactly one embedding step is required")
            
        return steps

# Processing step parameters
# TODO: Move to a separate file
class SentenceSplitterParameters(BaseModel):
    chunk_size: int = Field(description="The size of the chunks to split the text into", default=512)
    chunk_overlap: int = Field(description="The overlap of the chunks to split the text into", default=128)

class ProcessingStepType(str, Enum):
    NODE_PARSER = "node_parser"
    NODE_POST_PROCESSOR = "node_post_processor"
    EMBEDDING = "embedding"
