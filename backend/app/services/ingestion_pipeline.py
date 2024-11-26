from typing import Type, Dict, Any, List
from fastapi import HTTPException
from sqlalchemy.orm import Session

from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.settings import Settings
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.extractors import (
    SummaryExtractor,
    QuestionsAnsweredExtractor,
    TitleExtractor,
    #KeywordExtractor,
)
#from llama_index.extractors.entity import EntityExtractor

from app.services.file_system import FileSystemService
#from app.engine.pipelines.zettlekasten_pipeline import ZettlekastenExtractor
#from app.engine.index import get_global_index
from app.engine.vectordb import get_vector_store
from app.engine.docdb import get_postgres_document_store


import nest_asyncio
nest_asyncio.apply()

import logging
logger = logging.getLogger(__name__)

class IngestionPipelineService:

    def _create_ingestion_pipeline(self) -> IngestionPipeline:
        
        logger.info(f"Getting vector store and docstore to create ingestion pipeline")
        # Get the vector store and docstore
        vector_store = get_vector_store()
        docstore = get_postgres_document_store()

        # TODO : Add custom user pipeline creation with specified transformations and llm settings to personalise the ingestion pipeline and make it match the user files better, also add a way to save and load these pipelines, and a generation management. Also allow proper deletion and regeneration of documents from llama index file_index.

        #ingestion_llm =  # TODO : Add custom ingestion llm, for now use the default Settings.llm

        transformations = [
            SentenceSplitter(), # TODO : Use a better node parser https://docs.llamaindex.ai/en/stable/api_reference/node_parsers/
            TitleExtractor(
                nodes=5,
                #llm=ingestion_llm
            ),
            QuestionsAnsweredExtractor(
                questions=3,
                #llm=ingestion_llm
            ),
            SummaryExtractor(
                summaries=["prev", "self"],
                #llm=ingestion_llm
            ),
            #KeywordExtractor( # Using this extractors lead to an empty node list and so no embeddings, so it is disabled for now
            #    keywords=10,
            #    #llm=ingestion_llm
            #),
            #EntityExtractor(prediction_threshold=0.5),
            #ZettlekastenExtractor(),
            # Embed the nodes so they can be used by the query engine
            Settings.embed_model,
        ]

        logger.info(f"Creating zettlekasten ingestion pipeline")
            ingestion_pipeline = IngestionPipeline(
                transformations=transformations,
                docstore=docstore, # This allow the pipeline to add the documents to the docstore
                vector_store=vector_store, # This allow the pipeline to add nodes to the vector store
                docstore_strategy=DocstoreStrategy.UPSERTS, # UPSERTS_AND_DELETE causes a deletion of all previous documents in the docstore and vector store when the pipeline is ran
            )

            # Load the cache from the pipeline storage # TODO dont use local file storage ?
        try:
            ingestion_pipeline.load("./output/pipeline_storage")
        except Exception as e:
            logger.error(f"No existing pipeline cache found: {str(e)}")
            ingestion_pipeline.persist("./output/pipeline_storage")


        return ingestion_pipeline


    def __init__(self):
        self.file_system = FileSystemService()
        # Create the zettlekasten ingestion pipeline
        self.ingestion_pipeline = self._create_ingestion_pipeline()


#    async def ingest_file_from_id(self, session: AsyncSession, file_id: int):
#        try:
#            print(f"Retrieving file info for {file_id} from database")
#
#            # Get file from database using async session
#            result = await session.execute(
#                select(File).where(File.id == file_id)
#            )
#            file = result.scalar_one_or_none()
#            
#            if not file:
#                raise HTTPException(status_code=404, detail="File not found")
#
#            # Convert db path to local path
#            file_path = self.file_system.get_full_path(file.path)
#
#            return await self.ingest_file(file_path)
#        except Exception as e:
#            logger.error(f"Error ingesting file: {str(e)}")
#            raise HTTPException(status_code=500, detail=f"Error ingesting file: {str(e)}")


    async def ingest_file(self, full_file_path: str, logger: logging.Logger):
        try:
            logger.info(f"Starting ingestion pipeline for file {full_file_path}")
            
            logger.info(f"Using SimpleDirectoryReader to read file {full_file_path}")
            # Use SimpleDirectoryReader to read the file
            reader = SimpleDirectoryReader(
                input_files=[full_file_path],
                filename_as_id=True,
                raise_on_error=True,
            )
            documents = reader.load_data()

            # Set private=false to mark the document as public (required for filtering)
            for doc in documents:
                doc.metadata["private"] = "false"

            # ? Add file metadata to the document here ?
            # For now add the document to the index here #TODO Move this base document addition to its own service right after file upload, they need to be separated to allow for user triggered data generation through another specific pipeline / file data augmentation
            #logger.info(f"Adding documents to index")
            #index = get_global_index()
            #logger.info(f"Loaded {len(documents)} documents from file")
            #for document in documents:
            #    logger.info(f"Document: {document}")
            #    logger.info(f"Document content length: {len(document.text)}")
            #    index.insert(document)
            # Note : these changes will only appear in new indexes created after this point, so if there is a chat running it will use an index built from the old vector store and document store

            #TODO Add cache management to delete when too big with  cache.clear()

            # Now run the user specified ingestion pipeline on this document
            logger.info(f"Running ingestion pipeline")
            nodes = await self.ingestion_pipeline.arun(
                documents=documents,
                show_progress=True
                #num_workers=1
            )

            # Save the cache to storage
            self.ingestion_pipeline.persist("./output/pipeline_storage")

            logger.info(f"Ingested {len(nodes)} nodes")

            # No need to add these nodes to the index, they are added to the vector store and document store and will be used by all new indexes created after this point from the docstore and vector store
            logger.info("Ingestion completed successfully")

        except Exception as e:
            logger.error(f"Error in ingestion pipeline: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error in ingestion pipeline: {str(e)}"
            ) 
