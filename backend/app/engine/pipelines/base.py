from abc import ABC, abstractmethod
from typing import Dict, Any

class GenerateDataPipeline(ABC):
    """Base class for data generation pipelines"""
    
    @abstractmethod
    async def generate(self, content: str) -> Dict[str, Any]:
        """
        Generate structured data from text content
        
        Args:
            content: Raw text content to process
            
        Returns:
            Dict containing the generated structured data
        """
        pass 