from typing import List
from app.engine.pipelines.base import GenerateDataPipeline, BaseData

class TextAnalysisPipeline(GenerateDataPipeline):
    """Example pipeline that performs basic text analysis"""
    
    async def generate(self, source_file_ids: List[int], content: str) -> List[BaseData]:
        # This is just an example implementation
        word_count = len(content.split())
        char_count = len(content)
        
        return [BaseData(
            source_file_ids=source_file_ids,
            content={
            "analysis": {
                "word_count": word_count,
                "character_count": char_count,
                "first_100_chars": content[:100]
            },
            "metadata": {
                "pipeline": "text_analysis",
                    "version": "1.0"
                }
            } 
        )]