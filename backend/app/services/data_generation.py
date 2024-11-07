from typing import Type, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.engine.pipelines.base import GenerateDataPipeline
from app.services.db_data_manager import DBDataManagerService
from app.services.db_file import DBFileService
from app.services.file_system import FileSystemService

class DataGenerationService:
    def __init__(self):
        self.file_system = FileSystemService()

    async def generate_data_from_file(
        self,
        session: Session,
        file_id: int,
        pipeline: Type[GenerateDataPipeline]
    ) -> Dict[str, Any]:
        """
        Generate structured data from a file using the specified pipeline
        
        Args:
            session: Database session
            file_id: ID of the file to process
            pipeline: Pipeline class to use for generation
            
        Returns:
            Generated data record
        """
        try:
            # Get file from database
            file = DBFileService.get_file(session, file_id)
            if not file:
                raise HTTPException(status_code=404, detail="File not found")

            # Read file content
            file_path = self.file_system.get_full_path(file.path)
            with open(file_path, 'r') as f:
                content = f.read()

            # Initialize and run pipeline
            pipeline_instance = pipeline()
            generated_data = await pipeline_instance.generate(content)

            # Store generated data
            data = DBDataManagerService.create_data(
                session=session,
                file_ids=[file_id],
                data_content=generated_data
            )

            return data

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error generating data: {str(e)}"
            ) 