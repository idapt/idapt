from fastapi import HTTPException

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
from app.engine.ingestion.zettlekasten_extractor import ZettlekastenExtractor
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

    def _create_ingestion_pipeline(self) -> IngestionPipeline:
        try:        
            logger.info(f"Getting vector store and docstore to create ingestion pipeline")

            # TODO : Add custom user pipeline creation with specified transformations and llm settings to personalise the ingestion pipeline and make it match the user files better, also add a way to save and load these pipelines, and a generation management. Also allow proper deletion and regeneration of documents from llama index file_index.

            #ingestion_llm =  # TODO : Add custom ingestion llm, for now use the default Settings.llm

            transformations = [
                # Node parser
                SentenceSplitter(
                    chunk_size=256, # Use small chunks so that the llm dont have too much input and always extract most of the important information
                    chunk_overlap=32,
                ), # TODO : Use a better node parser https://docs.llamaindex.ai/en/stable/api_reference/node_parsers/
                ## Metadata extractors
                #TitleExtractor(
                #    nodes=5,
                #    #llm=ingestion_llm
                #    node_template=  """\
                #        Context: {context_str}. Give a title that summarizes all of \
                #        the unique entities, titles or themes found in the context. Title: """
                #    ,
                #    combine_template="""\
                #        {context_str}. Based on the above candidate titles and content, \
                #        what is the comprehensive title for this document? Title: """
                #    ,
                #),
                #QuestionsAnsweredExtractor(
                #    questions=3,
                #    
                #    #llm=ingestion_llm
                #),
                #SummaryExtractor(
                #    summaries=["prev", "self"],
                #    #llm=ingestion_llm
                #),
                #KeywordExtractor( # Using this extractors lead to an empty node list and so no embeddings, so it is disabled for now
                #    keywords=10,
                #    #llm=ingestion_llm
                #    prompt_template=  = """\
                #        {context_str}. Give {keywords} unique keywords for this \
                #        document. Format as comma separated. Keywords: """
                #),
                #EntityExtractor(prediction_threshold=0.5),
                #ZettlekastenExtractor(
                #    similar_notes_top_k=5
                #),
                # Embed the nodes so they can be used by the query engine
                Settings.embed_model,
            ]

            logger.info(f"Creating ingestion pipeline")
            ingestion_pipeline = IngestionPipeline(
                transformations=transformations,
                docstore=StorageContextSingleton().doc_store, # This allow the pipeline to add the documents to the docstore
                vector_store=StorageContextSingleton().vector_store, # This allow the pipeline to add nodes to the vector store
                docstore_strategy=DocstoreStrategy.UPSERTS, # UPSERTS_AND_DELETE causes a deletion of all previous documents in the docstore and vector store when the pipeline is ran
            )

            # Load the cache from the pipeline storage # TODO : Dont use local file storage ?
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


    async def ingest_file(self, full_file_path: str, logger: logging.Logger):
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

            # Set private=false to mark the document as public (required for filtering)
            for doc in documents:
                doc.metadata["private"] = "false"

            logger.error(f"Running ingestion pipeline")
            # Now run the user specified ingestion pipeline on this document
            # This will add the documents to the vector store and docstore in the expected llama index way
            nodes = await self.ingestion_pipeline.arun(
                documents=documents,
                show_progress=True
                #num_workers=1
            )

            # Get the index from the storage context
            index = StorageContextSingleton().index
            # Add the nodes to the index
            index.insert_nodes(nodes)

            # Save the cache to storage #TODO Add cache management to delete when too big with  cache.clear()
            #self.ingestion_pipeline.persist("./output/pipeline_storage")

            logger.error(f"Ingested {len(documents)} documents")

        except Exception as e:
            logger.error(f"Error in ingestion pipeline: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Error in ingestion pipeline: {str(e)}"
            ) 
