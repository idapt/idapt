import json
from typing import List
from fastapi import HTTPException

# Set the llama index default llm and embed model to none otherwise it will raise an error.
# We use on demand initialization of the llm and embed model when needed as it can change depending on the request.
from llama_index.core.settings import Settings
Settings.llm = None
Settings.embed_model = None

from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy
from llama_index.core.readers import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter, HierarchicalNodeParser
from llama_index.core.extractors import (
    SummaryExtractor,
    QuestionsAnsweredExtractor,
    TitleExtractor,
    KeywordExtractor,
)
#from llama_index.extractors.entity import EntityExtractor

#from app.engine.ingestion.zettlekasten_extractor import ZettlekastenExtractor

from app.services.database import get_session
from app.services.db_file import get_db_file
from app.settings.model_initialization import init_embedding_model
from app.settings.models import AppSettings
from app.services.llama_index import get_docstore_path, create_vector_store, create_doc_store
import logging

logger = logging.getLogger("uvicorn")


TRANSFORMATIONS_STACKS = {
# See https://docs.llamaindex.ai/en/stable/examples/retrievers/auto_merging_retriever/ for more details on the hierarchical node parser
# List of avaliable transformations stacks with their name and transformations
    "default": [
        SentenceSplitter(
            chunk_size=512,
            chunk_overlap=64,
        ),
    ],
    #"hierarchical": [ # TODO Fix the bug where a relation with a non existing doc id is created and creates issues when querying the index
    #    HierarchicalNodeParser.from_defaults(
    #        include_metadata=True,
    #        chunk_sizes=[1024, 512, 256, 128], # Stella embedding is trained on 512 tokens chunks so for best performance this is the maximum #size, we also chunk it into The smallest sentences possible to capture as much atomic meaning of the sentence as possible.
    #        # When text chunks are too small like under 128 tokens, the embedding model may return null embeddings and we want to avoid that because it break the search as they can come out on top of the search results
    #        chunk_overlap=0
    #    ),
    #    # Embedding is present at ingestion pipeline level
    #],
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
    # NOTE: Current sentence splitter stacks are not linking each node like the hierarchical node parser does, so if multiple are used they are likely to generate duplicates nodes at retreival time. Only use one at a time to avoid this. # TODO Fix hierarchical node parser
    "sentence-splitter-2048": [
        SentenceSplitter(
            chunk_size=2048,
            chunk_overlap=256,
        ),
    ],
    "sentence-splitter-1024": [
        SentenceSplitter(
            chunk_size=1024,
            chunk_overlap=128,
        ),
    ],
    "sentence-splitter-512": [
        SentenceSplitter(
            chunk_size=512,
            chunk_overlap=64,
        ),
    ],
    "sentence-splitter-256": [
        SentenceSplitter(
            chunk_size=256,
            chunk_overlap=0,
        ),
    ],
    "sentence-splitter-128": [
        SentenceSplitter(
            chunk_size=128,
            chunk_overlap=0,
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
def process_files(full_file_paths: List[str], datasource_identifier: str, app_settings: AppSettings, transformations_stack_name_list: List[str] = ["default"]):
    """Process a list of files through the ingestion pipeline"""
    try:            
        # Use SimpleDirectoryReader from llama index as it try to use existing apropriate readers based on the file type to get the most metadata from it
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
        
        
        with get_session() as session:
            # Override the file creation time to the current time with the times from the database
            for doc in documents:
                # Get the file from the database
                file = get_db_file(session, doc.metadata["file_path"])
                # Set the creation and modification times
                doc.metadata["created_at"] = file.file_created_at.isoformat()
                doc.metadata["modified_at"] = file.file_modified_at.isoformat()
                # Remove from embed and llm
                doc.excluded_embed_metadata_keys.append("created_at")
                doc.excluded_embed_metadata_keys.append("modified_at")
                doc.excluded_llm_metadata_keys.append("created_at")
                doc.excluded_llm_metadata_keys.append("modified_at")

        # Init the embed model from the app settings
        embed_model = init_embedding_model(app_settings)

        # Create the ingestion pipeline for the datasource
        vector_store = create_vector_store(datasource_identifier, embed_model)
        doc_store = create_doc_store(datasource_identifier)

        # Create the ingestion pipeline for the datasource
        ingestion_pipeline = IngestionPipeline(
            name=f"ingestion_pipeline_{datasource_identifier}",
            docstore=doc_store,
            vector_store=vector_store,
            docstore_strategy=DocstoreStrategy.UPSERTS,
            #docstore_strategy=DocstoreStrategy.DUPLICATES_ONLY, # Otherwise it dont work with the hierarchical node parser because it always upserts all previous nodes for this document
            # TODO Make a hierarchical node parser that works with the ingestion pipeline
            # Could be set to UPSERTS to allow the ingestion pipeline to resume from where it left off if it crashes
            # But this mess up the stack if there is more than one ingestion transformation stack
            # TODO Add multiple ingestion pipeline stacks support to the ingestion pipeline
            # TODO It still does not work as when we add a document with a new doc id, it upserts the old red doc id but it works well with single ingestion stack
        )

        # Load/create pipeline cache
        #try:
            #ingestion_pipeline.load(f"/data/.idapt/output/pipeline_storage_{datasource_identifier}")
        #except Exception as e:
        #    logger.error(f"No existing pipeline cache found: {str(e)}")
            #ingestion_pipeline.persist(f"/data/.idapt/output/pipeline_storage_{datasource_identifier}")


        # For each transformations stack we need to apply
        for transformations_stack_name in transformations_stack_name_list:
            
            # Get the transformations stack
            transformations = TRANSFORMATIONS_STACKS[transformations_stack_name]

            # If the current embed model match the cached embed model, use the cached embed model
            # TODO Add model name check also but also TODO support embedding change for datasources
            #if self.cached_embed_model_provider != app_settings.embedding_model_provider:
            # Update the llama index settings to use the new embed model so that the Settings.embed_model is updated
            # TODO Add a way to only update on each when app settings are changed, complicated as this is run in a child thread and appsettings updates are not done here.

            # Set the transformations stack name for the datasource_documents
            for doc in documents:
                doc.metadata["transformations_stack_name"] = transformations_stack_name
                doc.excluded_embed_metadata_keys.append("transformations_stack_name")
                doc.excluded_llm_metadata_keys.append("transformations_stack_name")

                # Modify the doc id to append the transformation stack at the end so that they are treated as different documents by the docstore upserts
                # If its the first iteration of the loop append the transformation stack name at the end of the doc id
                if transformations_stack_name == transformations_stack_name_list[0]:
                    doc.doc_id = f"{doc.doc_id}_{transformations_stack_name}"
                else:
                    # If its not the first iteration of the loop replace the end part of the doc id with the transformation stack name
                    # Split the doc id by the underscore and replace the last part with the transformation stack name
                    doc_id_parts = doc.doc_id.split("_")
                    doc_id_parts[-1] = transformations_stack_name
                    doc.doc_id = "_".join(doc_id_parts)

                # Update the file in the database with the ref_doc_ids
                # Do this before the ingestion so that if it crashes we can try to delete the file from the vector store and docstore with its ref_doc_ids and reprocess
                with get_session() as session:
                    file = get_db_file(session, doc.metadata["file_path"])
                    if file:
                        # Parse the json ref_doc_ids as a list
                        file_ref_doc_ids = json.loads(file.ref_doc_ids) if file.ref_doc_ids else []
                        # Add the new doc id to the list
                        file_ref_doc_ids.append(doc.doc_id)
                        # Update the file in the database
                        file.ref_doc_ids = json.dumps(file_ref_doc_ids)
                        session.commit()

            # TODO : Make the HierarchicalNodeParser work with the ingestion pipeline
            #if transformations_stack_name == "hierarchical":
            #    # Dont work with ingestion pipeline so use it directly to extract the nodes and add them manually to the index
            #    hierarchical_nodes = transformations[0].get_nodes_from_documents(
            #        documents, 
            #        show_progress=True
            #    )
            #    
            #    # Set the transformations for the ingestion pipeline
            #    ingestion_pipeline.transformations = [self.cached_embed_model] # Only keep the embedding as the nodes are parsed with the HierarchicalNodeParser
            #    
            #    # Run the ingestion pipeline on the resulting nodes to add the nodes to the docstore and vector store
            #    nodes = await ingestion_pipeline.arun(
            #        nodes=hierarchical_nodes,
            #        show_progress=True,
            #        #num_workers=None # We process in this thread as it is a child thread managed by the generate service and spawning other threads here causes issue with the uvicorn dev reload mechanism
            #    )
            #    # No need to insert nodes into index as we use a vector store


            #else:
            logger.info(f"Running processing stack {transformations_stack_name} on {full_file_paths}")
            # This will add the documents to the vector store and docstore in the expected llama index way
            # Add the embed model to the transformations stack as we always want to embed the results of the processing stacks for search
            transformations.append(embed_model)
            # Set the transformations for the ingestion pipeline
            ingestion_pipeline.transformations = transformations
            nodes = ingestion_pipeline.run(
                documents=documents,
                show_progress=True,
                #num_workers=None # We process in this thread as it is a child thread managed by the generate service and spawning other threads here causes issue with the uvicorn dev reload mechanism
            )
            # No need to insert nodes into index as we use a vector store

        # Save the cache to storage #TODO : Add cache management to delete when too big with cache.clear()
        #ingestion_pipeline.persist(f"/data/.idapt/output/pipeline_storage_{datasource_identifier}")

        # Needed for now as SimpleDocumentStore is not persistent
        doc_store.persist(persist_path=get_docstore_path(datasource_identifier))


        logger.info(f"Processed {full_file_paths}")

    except Exception as e:
        logger.error(f"Error in ingestion pipeline: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in ingestion pipeline: {str(e)}"
        ) 
    