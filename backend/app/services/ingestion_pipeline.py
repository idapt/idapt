from typing import List
from fastapi import HTTPException

from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.settings import Settings
from llama_index.core.node_parser import SentenceSplitter, HierarchicalNodeParser
from llama_index.core.extractors import (
    SummaryExtractor,
    QuestionsAnsweredExtractor,
    TitleExtractor,
    KeywordExtractor,
)
#from llama_index.extractors.entity import EntityExtractor

from app.services.file_system import FileSystemService
#from app.engine.ingestion.zettlekasten_extractor import ZettlekastenExtractor
from app.engine.storage_context import StorageContextSingleton
        

import nest_asyncio

nest_asyncio.apply()

import logging
logger = logging.getLogger(__name__)

class IngestionPipelineService:
    """
    Service for managing the ingestion pipeline
    This only takes care of the llama index part
    """
    # See https://docs.llamaindex.ai/en/stable/examples/retrievers/auto_merging_retriever/ for more details on the hierarchical node parser
    # List of avaliable transformations stacks with their name and transformations
    TRANSFORMATIONS_STACKS = {
        "default": [
            SentenceSplitter(
                chunk_size=512,
                chunk_overlap=128,
            ),
            Settings.embed_model,
        ],
        "hierarchical": [
            HierarchicalNodeParser.from_defaults(
                include_metadata=True,
                chunk_sizes=[2048, 1024, 512, 128]
            ),
            Settings.embed_model,
        ],
        "titles": [
            TitleExtractor(
                nodes=5,
            ),
        ],
        "questions": [
            QuestionsAnsweredExtractor(
                questions=3,
            ),
        ],
        "summary": [
            SummaryExtractor(
                summaries=["prev", "self"],
            ),
        ],
        "keywords": [
            KeywordExtractor(
                keywords=10,
            ),
        ],
        #"entities": [
        #    EntityExtractor(prediction_threshold=0.5),
        #],
        #"zettlekasten": [
        #    ZettlekastenExtractor(
        #        similar_notes_top_k=5
        #    ),
        #],
    }

    def _create_ingestion_pipeline(self) -> IngestionPipeline:
        try:        
            logger.info(f"Getting vector store and docstore to create ingestion pipeline")

            # TODO : Add custom user pipeline creation with specified transformations and llm settings to personalise the ingestion pipeline and make it match the user files better, also add a way to save and load these pipelines, and a generation management. Also allow proper deletion and regeneration of documents from llama index file_index.

            logger.info(f"Creating ingestion pipeline")
            ingestion_pipeline = IngestionPipeline(
                docstore=StorageContextSingleton().doc_store, # This allow the pipeline to add the documents to the docstore
                vector_store=StorageContextSingleton().vector_store, # This allow the pipeline to add nodes to the vector store
                docstore_strategy=DocstoreStrategy.DUPLICATES_ONLY, # DUPLICATES_ONLY as we insert multiple times nodes with the same red_doc_id when we augment them
            )

            # Load the cache from the pipeline storage
            try:
                ingestion_pipeline.load("./output/pipeline_storage")
            except Exception as e:
                logger.error(f"No existing pipeline cache found: {str(e)}")
                ingestion_pipeline.persist("./output/pipeline_storage")

            return ingestion_pipeline
        except Exception as e:
            logger.error(f"Error creating ingestion pipeline: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error creating ingestion pipeline: {str(e)}")


    def __init__(self):
        self.file_system = FileSystemService()
        # Create a unique ingestion pipeline that will persist between file ingestions
        self.ingestion_pipeline = self._create_ingestion_pipeline()


    async def ingest_file(self, full_file_path: str, logger: logging.Logger, transformations_stack_name_list: List[str]):
        try:
            logger.info(f"Starting ingestion pipeline for file {full_file_path}")
            
            logger.info(f"Using SimpleDirectoryReader to read file {full_file_path}")
            # Use SimpleDirectoryReader to read the only the file
            reader = SimpleDirectoryReader(
                input_files=[full_file_path],
                filename_as_id=True,
                raise_on_error=True,
            )
            documents = reader.load_data()

            # Set the origin metadata of the document
            for doc in documents:
                doc.metadata["origin"] = "upload"
            
            # For each transformations stack we need to apply
            for transformations_stack_name in transformations_stack_name_list:
                
                # Get the transformations stack
                transformations = self.TRANSFORMATIONS_STACKS[transformations_stack_name]

                # Set the transformations stack name for the documents
                for doc in documents:   
                    doc.metadata["transformations_stack_name"] = transformations_stack_name

                # TODO : Make the HierarchicalNodeParser work with the ingestion pipeline
                if transformations_stack_name == "hierarchical":
                    # Dont work with ingestion pipeline so use it directly to extract the nodes and add them manually to the index
                    nodes = transformations[0].get_nodes_from_documents(documents, show_progress=True)
                    # Add the node_id into the metadata for later filtering using it # TODO Implement it for other transformations stacks
                    for node in nodes:
                        node.metadata["node_id"] = node.node_id
                    
                    # Set the transformations for the ingestion pipeline
                    self.ingestion_pipeline.transformations = [] # HierarchicalNodeParser embed the nodes using the Settings.embed_model so no need to re-embed them

                    # Run the ingestion pipeline on the resulting nodes to add the nodes to the docstore and vector store
                    nodes = await self.ingestion_pipeline.arun(
                        nodes=nodes,
                        show_progress=True,
                        docstore_strategy=DocstoreStrategy.UPSERTS,

                    )
                    # Insert nodes into index
                    StorageContextSingleton().index.insert_nodes(nodes)


                else:
                    logger.info(f"Running ingestion pipeline with transformations stack {transformations_stack_name}")
                    # This will add the documents to the vector store and docstore in the expected llama index way

                    # Set the transformations for the ingestion pipeline
                    self.ingestion_pipeline.transformations = transformations
                    nodes = await self.ingestion_pipeline.arun(
                        documents=documents,
                        show_progress=True
                    )
                    # Insert nodes into index
                    StorageContextSingleton().index.insert_nodes(nodes)

            # Save the cache to storage #TODO : Add cache management to delete when too big with cache.clear()
            self.ingestion_pipeline.persist("./output/pipeline_storage")

            logger.info(f"Ingested {len(documents)} documents")

        except Exception as e:
            logger.error(f"Error in ingestion pipeline: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error in ingestion pipeline: {str(e)}"
            ) 