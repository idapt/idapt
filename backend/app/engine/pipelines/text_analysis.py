from typing import Dict, Any
from app.engine.pipelines.base import GenerateDataPipeline

class TextAnalysisPipeline(GenerateDataPipeline):
    """Example pipeline that performs basic text analysis"""
    
    async def generate(self, content: str) -> Dict[str, Any]:
        # This is just an example implementation
        word_count = len(content.split())
        char_count = len(content)
        
        return {
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