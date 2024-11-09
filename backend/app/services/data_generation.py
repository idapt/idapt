from typing import Type, Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.engine.pipelines.base import GenerateDataPipeline, BaseData
from app.services.db_data_manager import DBDataManagerService
from app.services.db_file import DBFileService
from app.services.file_system import FileSystemService
from app.engine.index import get_index, refresh_index

import logging
logger = logging.getLogger(__name__)

class DataGenerationService:
    def __init__(self):
        self.file_system = FileSystemService()

    async def generate_data_from_file(
        self,
        session: Session,
        file_id: int,
        pipeline: Type[GenerateDataPipeline]
    ):
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
            logger.info(f"Starting data generation for file {file_id}")
            
            # Get file from database
            file = DBFileService.get_file(session, file_id)
            if not file:
                raise HTTPException(status_code=404, detail="File not found")
            
            logger.info(f"Processing file: {file.name}")
            
            # Read file content
            file_path = self.file_system.get_full_path(file.path)
            with open(file_path, 'r') as f:
                content = f.read()

            # Initialize and run pipeline
            logger.info("Running data generation pipeline")
            # Create the pipeline instance from the pipeline class passed in
            pipeline_instance = pipeline()
            # Run the pipeline on the file content
            generated_data = await pipeline_instance.generate([file.id], content)

            # Store generated data
            for base_data in generated_data:
                logger.info("Storing generated data in database")
                DBDataManagerService.create_data(
                    session=session,
                    file_ids=base_data.source_file_ids,
                    data_content=base_data.content
                )

            # Temporary
            logger.info(f"Adding {len(generated_data)} data nodes to index")
            # Convert the generated data to llama index documents
            generated_data_documents = BaseData.to_documents(generated_data)
            index = get_index()
            # Add the generated data to the llama index directly
            # For now directly index the note each time new data is generated #TODO make index document management better
            for document in generated_data_documents:
                index.insert(document)    
            refresh_index()  # Ensure all services see the new data

            logger.info("Data generation completed successfully")

        except Exception as e:
            logger.error(f"Error in data generation: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error generating data: {str(e)}"
            ) 