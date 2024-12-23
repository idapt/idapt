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

#from app.engine.ingestion.zettlekasten_extractor import ZettlekastenExtractor

from app.services.database import DatabaseService
from app.services.db_file import DBFileService
from app.services.datasource import DatasourceService


import nest_asyncio

nest_asyncio.apply()

import logging

class IngestionPipelineService:
    """
    Service for managing the ingestion pipeline
    This only takes care of the llama index part
    """

    def __init__(self, db_file_service: DBFileService, db_service: DatabaseService, datasource_service: DatasourceService):

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)  # Set log level as we are in a child thread

        self.db_service = db_service
        
        self.db_file_service = db_file_service
        self.datasource_service = datasource_service
        self.pipelines = {}

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
                chunk_sizes=[512, 256, 64], # Stella embedding is trained on 512 tokens chunks so for best performance this is the maximum size, we also chunk it into The smallest sentences possible to capture as much atomic meaning of the sentence as possible.
                chunk_overlap=0
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

    # At this point the files are grouped by ingestion stack
    async def process_files(self, full_file_paths: List[str], datasource_identifier: str, transformations_stack_name_list: List[str] = ["default"]):
        """Process a list of files through the ingestion pipeline"""
        try:

            self.logger.info(f"Starting batch ingestion pipeline for {len(full_file_paths)} files")
            
            # Read all files in batch
            reader = SimpleDirectoryReader(
                input_files=full_file_paths,
                filename_as_id=True,
                raise_on_error=True,
            )
            documents = reader.load_data()

            # Remove the unwanted metadata from the documents
            for doc in documents:
                doc.metadata.pop("creation_date", None)
                doc.metadata.pop("last_modified_date", None)
                
            # Remove the metadata created by the file reader that we dont want to embed and llm
            for doc in documents:
                doc.excluded_embed_metadata_keys = ["file_path","file_name", "file_type", "file_size", "document_id", "doc_id", "ref_doc_id"]
                doc.excluded_llm_metadata_keys = ["file_path","file_name", "file_type", "file_size", "document_id", "doc_id", "ref_doc_id"]

            # Set the origin metadata of the document
            for doc in documents:
                doc.metadata["origin"] = "upload"
                doc.excluded_embed_metadata_keys.append("origin")
                doc.excluded_llm_metadata_keys.append("origin")
            
            
            with self.db_service.get_session() as session:
                # Override the file creation time to the current time with the times from the database
                for doc in documents:
                    # Get the file from the database
                    file = self.db_file_service.get_file(session, doc.metadata["file_path"])
                    # Set the creation and modification times
                    doc.metadata["created_at"] = file.file_created_at.isoformat()
                    doc.metadata["modified_at"] = file.file_modified_at.isoformat()
                    # Remove from embed and llm
                    doc.excluded_embed_metadata_keys.append("created_at")
                    doc.excluded_embed_metadata_keys.append("modified_at")
                    doc.excluded_llm_metadata_keys.append("created_at")
                    doc.excluded_llm_metadata_keys.append("modified_at")


            # Create the ingestion pipeline for the datasource
            vector_store, doc_store, _ = self.datasource_service.get_storage_components(datasource_identifier)

            ingestion_pipeline = IngestionPipeline(
                docstore=doc_store,
                vector_store=vector_store,
                docstore_strategy=DocstoreStrategy.DUPLICATES_ONLY,
            )

            # Load/create pipeline cache
            try:
                ingestion_pipeline.load(f"/backend_data/output/pipeline_storage_{datasource_identifier}")
            except Exception as e:
                self.logger.error(f"No existing pipeline cache found: {str(e)}")
                ingestion_pipeline.persist(f"/backend_data/output/pipeline_storage_{datasource_identifier}")


            # For each transformations stack we need to apply
            for transformations_stack_name in transformations_stack_name_list:
                
                # Get the transformations stack
                transformations = self.TRANSFORMATIONS_STACKS[transformations_stack_name]

                # Set the transformations stack name for the datasource_documents
                for doc in documents:   
                    doc.metadata["transformations_stack_name"] = transformations_stack_name
                    doc.excluded_embed_metadata_keys.append("transformations_stack_name")
                    doc.excluded_llm_metadata_keys.append("transformations_stack_name")

                # TODO : Make the HierarchicalNodeParser work with the ingestion pipeline
                if transformations_stack_name == "hierarchical":
                    # Dont work with ingestion pipeline so use it directly to extract the nodes and add them manually to the index
                    nodes = transformations[0].get_nodes_from_documents(
                        documents, 
                        show_progress=True
                    )
                    
                    # Set the transformations for the ingestion pipeline
                    ingestion_pipeline.transformations = [] # HierarchicalNodeParser embed the nodes using the Settings.embed_model so no need to re-embed them

                    # Run the ingestion pipeline on the resulting nodes to add the nodes to the docstore and vector store
                    nodes = await ingestion_pipeline.arun(
                        nodes=nodes,
                        show_progress=True,
                        docstore_strategy=DocstoreStrategy.UPSERTS, # This allows that if there is a crash during ingestion it can resume from where it left off
                        num_workers=None # We process in this thread as it is a child thread managed by the generate service and spawning other threads here causes issue with the uvicorn dev reload mechanism
                    )
                    # No need to insert nodes into index as we use a vector store


                else:
                    self.logger.info(f"Running ingestion pipeline with transformations stack {transformations_stack_name}")
                    # This will add the documents to the vector store and docstore in the expected llama index way

                    # Set the transformations for the ingestion pipeline
                    ingestion_pipeline.transformations = transformations
                    nodes = await ingestion_pipeline.arun(
                        documents=documents,
                        show_progress=True,
                        docstore_strategy=DocstoreStrategy.UPSERTS, # This allows that if there is a crash during ingestion it can resume from where it left off # ? Mess up the stack if there is more than one ingestion transformation stack ?
                        num_workers=None # We process in this thread as it is a child thread managed by the generate service and spawning other threads here causes issue with the uvicorn dev reload mechanism
                    )
                    # No need to insert nodes into index as we use a vector store

            # Save the cache to storage #TODO : Add cache management to delete when too big with cache.clear()
            ingestion_pipeline.persist(f"/backend_data/output/pipeline_storage_{datasource_identifier}")

            self.logger.info(f"Ingested {len(documents)} documents")


        except Exception as e:
            self.logger.error(f"Error in ingestion pipeline: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error in ingestion pipeline: {str(e)}"
            ) 
        