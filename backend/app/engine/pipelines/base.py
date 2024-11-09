from abc import ABC, abstractmethod
from typing import List, Any
from pydantic import BaseModel, Json
from llama_index.core.schema import Document
import json

class BaseData(BaseModel):
    
    content: Json[Any]
    source_file_ids: List[int]

    """Base class for all data models"""
    @classmethod
    def to_document(cls, base_data: 'BaseData') -> 'Document':
        """Convert a single data object to a LlamaIndex document"""
        # Convert the JSON content to a string if it isn't already
        content = base_data.content if isinstance(base_data.content, str) else json.dumps(base_data.content)
        return Document(text=content, metadata={"source_file_ids": base_data.source_file_ids})

    @classmethod
    def to_documents(cls, base_data_list: List['BaseData']) -> List['Document']:
        """Convert multiple data objects to LlamaIndex documents"""
        return [cls.to_document(base_data) for base_data in base_data_list]

class GenerateDataPipeline(ABC):
    """Base class for data generation pipelines"""
    
    @abstractmethod
    async def generate(self, source_file_ids: List[int], content: str) -> List[BaseData]:
        """
        Generate structured data from text content
        
        Args:
            content: Raw text content to process
            
        Returns:
            List of BaseData objects
        """
        pass 