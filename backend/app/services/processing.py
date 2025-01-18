from app.services.db_file import get_db_file, get_db_files_by_status
from app.services.datasource import get_datasource_identifier_from_path
from app.services.llama_index import delete_file_llama_index, delete_file_processing_stack_from_llama_index
from app.services.ollama_status import is_ollama_server_reachable, wait_for_ollama_models_to_be_downloaded
from app.database.models import File, FileStatus
from app.services.llama_index import get_docstore_file_path, create_vector_store, create_doc_store
from app.database.models import Datasource
from app.services.processing_stacks import get_transformations_for_stack
from app.services.settings import get_setting
from app.settings.models import AppSettings, OllamaSettings

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


from datetime import datetime
import mimetypes
import os
from typing import List
from sqlalchemy.orm import Session
import json
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
    "image": [
        #ImageDescriptionExtractor(
        #    
        #),
        #ImageEXIFExtractor(
        #    
        #),
    ],
    "video": [
        #VideoDescriptionExtractor(
        #    
        #),
        #VideoTranscriptionExtractor(
        #    
        #),
        #VideoEXIFExtractor(
        #    
        #),
    ],
    "audio": [
        #AudioTranscriptionExtractor(
        #    
        #),
        #AudioEXIFExtractor(
        #    
        #),
    ],
    "code": [
        #CodeExtractor(
        #    
        #),
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

logger = logging.getLogger("uvicorn")


def _get_file_type(file_path: str) -> str:
    """Get the file type from the file path"""
    try:
        file_extension = os.path.splitext(file_path)[1]
        file_type = ""
        match file_extension:
            # Text files
            case ".pdf" | ".doc" | ".odt" | ".docx" | ".txt" | ".md" | ".markdown":
                file_type = "text"
            # Images
            case ".jpg" | ".jpeg" | ".png" | ".gif" | ".bmp" | ".tiff" | ".ico" | ".webp":
                file_type = "image"
            # Videos
            case ".mp4" | ".avi" | ".mov" | ".wmv" | ".flv" | ".mkv" | ".webm" | ".mpg" | ".mpeg" | ".m4v":
                file_type = "video"
            # Audio
            case ".mp3" | ".wav" | ".aac" | ".flac" | ".m4a" | ".ogg" | ".opus":
                file_type = "audio"
            # Code
            case ".py" | ".js" | ".html" | ".css" | ".java" | ".c" | ".cpp" | ".cs" | ".go" | ".rb" | ".swift" | ".kt" | ".rs" | ".php" | ".sql" | ".xml" | ".json" | ".yaml" | ".yml" | ".toml" | ".md" | ".rst" | ".sh" | ".bash" | ".zsh" | ".fish" | ".powershell" | ".ps1" | ".bat" | ".cmd" | ".psm1" | ".ps1xml" | ".psscrip" :
                file_type = "code"
            case _:
                # File extension not recognized, try to use the mime type
                mime_type = mimetypes.guess_type(file_path)
                match mime_type:
                    case "text/plain":
                        file_type = "text"
                    case "image/jpeg" | "image/png" | "image/gif" | "image/bmp" | "image/tiff" | "image/ico" | "image/webp":
                        file_type = "image"
                    case "video/mp4" | "video/avi" | "video/mov" | "video/wmv" | "video/flv" | "video/mkv":
                        file_type = "video"
                    case "audio/mp3" | "audio/wav" | "audio/aac" | "audio/flac" | "audio/m4a" | "audio/ogg" | "audio/opus":
                        file_type = "audio"
                    case "application/pdf":
                        file_type = "pdf"
                    case _:
                        file_type = "unknown"
            
        return file_type
    except Exception as e:
        logger.error(f"Failed to get file type for {file_path}: {str(e)}")
        return "unknown"
    
def _validate_stacks_to_process_for_file_type(stacks_to_process: List[str], file_type: str) -> List[str]:
    """Validate the stacks to process for a given file type"""
    try:
        validated_stacks_to_process = []
        for stack_name in stacks_to_process:
            # Check if this transformation stack is applicable to the file type
            # TODO Implement better generation, for now we just add all stacks
            validated_stacks_to_process.append(stack_name)
        return validated_stacks_to_process
    except Exception as e:
        logger.error(f"Failed to validate stacks to process for file type {file_type}: {str(e)}")
        return stacks_to_process

def mark_file_as_queued(session: Session, file_path: str, stacks_to_process: List[str]):
    """Mark a file as queued"""
    try:
        # Get the file type
        file_type = _get_file_type(file_path)
        # For each transformation stack name
        validated_stacks_to_process = _validate_stacks_to_process_for_file_type(stacks_to_process, file_type)

        # Get the file
        file = get_db_file(session, file_path)
        if not file:
            raise ValueError(f"File not found: {file_path}")

        # Try to load the stacks_to_process as a json list, set it as an empty list if it is null
        existing_stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else []
        # Try to load the processed_stacks as a json list, set it as an empty list if it is null
        processed_stacks = json.loads(file.processed_stacks) if file.processed_stacks else []

        stacks_to_process_not_already_processed = []
        # Check in the processing_stacks json list and add the stacks that are not already processed
        for stack in validated_stacks_to_process:
            if stack not in processed_stacks:
                stacks_to_process_not_already_processed.append(stack)

        if not stacks_to_process_not_already_processed:
            logger.info(f"All stacks for file {file_path} are already processed, skipping")
            return
        
        stacks_to_process_not_already_in_stacks_to_process = []
        for stack in stacks_to_process_not_already_processed:
            if stack not in existing_stacks_to_process:
                stacks_to_process_not_already_in_stacks_to_process.append(stack)

        # Make sure the file is queued as there is stacks to process
        file.status = FileStatus.QUEUED
        # Add the stacks to process to the existing stacks to process
        existing_stacks_to_process.extend(stacks_to_process_not_already_in_stacks_to_process)
        # Convert back to json string and store it in the database
        file.stacks_to_process = json.dumps(existing_stacks_to_process)
        
        session.commit()

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to mark file as queued: {str(e)}")
        raise

async def process_queued_files(
        session: Session,
        user_id: str
    ):
    """Processing loop"""
    try:
        app_settings : AppSettings = get_setting(session, "app")
        if app_settings.llm_model_provider == "ollama" or app_settings.embedding_model_provider == "ollama":
            ollama_settings : OllamaSettings = get_setting(session, "ollama")
            # Check if the ollama server is reachable
            if not await is_ollama_server_reachable(ollama_settings.llm_host):
                # We can't process files if the ollama server is not reachable, skip this processing request
                logger.error("Ollama server is not reachable, skipping processing request")
                return

        # Wait for Ollama models to be downloaded
        await wait_for_ollama_models_to_be_downloaded(session)
   
        logger.info("Beginning processing files")
        # Process all files marked as processing that have been interrupted with unfinished processing
        _process_files_marked_as_processing(session=session, user_id=user_id)

        # Process all queued files
        _process_all_queued_files(session=session, user_id=user_id)
   

    except Exception as e:
        logger.error(f"Processing loop error: {str(e)}")
        raise

def _process_files_marked_as_processing(session: Session, user_id: str):
    """Process all files marked as processing"""
    try:
        while True:
            try:
                logger.info("Processing files marked as processing")
                # Get the files one by one so that in case of queued file changes we get the freshest database data
                oldest_processing_file = session.query(File).filter(
                    File.status == FileStatus.PROCESSING
                ).order_by(
                    File.uploaded_at.asc()
                ).first()

                # If there are no more files marked as processing, return
                if not oldest_processing_file:
                    return

                # Move the processed stacks to the stacks_to_process column as we will delete all already processed stacks from llama index and reprocess them
                processed_stacks = json.loads(oldest_processing_file.processed_stacks)
                stacks_to_process = json.loads(oldest_processing_file.stacks_to_process)
                stacks_to_process.extend(processed_stacks)
                oldest_processing_file.stacks_to_process = json.dumps(stacks_to_process)
                oldest_processing_file.processed_stacks = json.dumps([])
                session.commit()

                logger.info(f"Reprocessing interrupted file: {oldest_processing_file.path}")
                try:
                    delete_file_llama_index(session=session, user_id=user_id, full_path=oldest_processing_file.path)
                except Exception as e:
                    logger.error(f"Failed to delete {oldest_processing_file.path} from stores: {str(e)}")
                
                _process_single_file(session, oldest_processing_file, user_id)
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to process interrupted file {oldest_processing_file.path}: {str(e)}, marking as error")
                try:
                    oldest_processing_file.status = FileStatus.ERROR
                    session.commit()
                except Exception as e:
                    session.rollback()
                    logger.error(f"Failed to update file status for {oldest_processing_file.path}: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to process all queued files: {str(e)}")
        raise
        
def _process_all_queued_files(session: Session, user_id: str):
    """Process all queued files"""
    try:
        while True:
            try:
                # Get the files one by one so that in case of queued file changes we get the freshest database data
                # Get oldest queued file
                queued_file = session.query(File).filter(
                    File.status == FileStatus.QUEUED
                ).order_by(
                    File.uploaded_at.asc()
                ).first()
                
                if queued_file:
                    _process_single_file(session=session, file=queued_file, user_id=user_id)
                else:
                    return
        
            except Exception as e:
                logger.error(f"Failed to process queued file {queued_file.path}: {str(e)}, marking as error")
                try:
                    queued_file.status = FileStatus.ERROR
                    session.commit()
                except Exception as e:
                    session.rollback()
                    logger.error(f"Failed to update file status for {queued_file.path}: {str(e)}")
    except Exception as e:
        logger.error(f"Failed to process all queued files: {str(e)}")
        raise

def _process_single_file(session: Session, file: File, user_id: str):
    """Process a single file through the ingestion pipeline"""
    try:
        # Update status to processing
        file.status = FileStatus.PROCESSING
        file.processing_started_at = datetime.now()
        session.commit()

        logger.info(f"Processing file: {file.path}")
        
        # Properly decode JSON stacks with defaults
        stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else []
        processed_stacks = json.loads(file.processed_stacks) if file.processed_stacks else []
        datasource_identifier = get_datasource_identifier_from_path(file.path)
        datasource = session.query(Datasource).filter(Datasource.identifier == datasource_identifier).first()
        
        # Process each stack
        for stack_identifier in stacks_to_process:
            try:
                # If the stack is not already processed, process it
                if processed_stacks and stack_identifier in processed_stacks:
                    logger.info(f"Stack {stack_identifier} already processed, skipping")
                    # Remove the stack from the stacks_to_process list
                    stacks_to_process = [stack for stack in stacks_to_process if stack != stack_identifier]
                    file.stacks_to_process = json.dumps(stacks_to_process)
                    session.commit()
                    continue

                logger.info(f"Processing stack {stack_identifier} for file {file.path}")
                
                # Create the ingestion pipeline for the datasource
                vector_store = create_vector_store(datasource.id, user_id)
                doc_store = create_doc_store(datasource_identifier, user_id)

                # Create the ingestion pipeline for the datasource
                ingestion_pipeline = IngestionPipeline(
                    name=f"ingestion_pipeline_{datasource_identifier}",
                    docstore=doc_store,
                    vector_store=vector_store,
                    docstore_strategy=DocstoreStrategy.UPSERTS,
                    #docstore_strategy=DocstoreStrategy.DUPLICATES_ONLY, # Otherwise it dont work with the hierarchical node parser because it always upserts all previous nodes for this document
                    # TODO Make a hierarchical node parser that works with the ingestion pipeline
                )

                # Load/create pipeline cache
                #try:
                    #ingestion_pipeline.load(f"/data/.idapt/output/pipeline_storage_{datasource_identifier}")
                #except Exception as e:
                #    logger.error(f"No existing pipeline cache found: {str(e)}")
                    #ingestion_pipeline.persist(f"/data/.idapt/output/pipeline_storage_{datasource_identifier}")


                # Use SimpleDirectoryReader from llama index
                # It try to use existing apropriate readers based on the file type to get the most metadata from it
                reader = SimpleDirectoryReader(
                    input_files=[file.path],
                    filename_as_id=True,
                    raise_on_error=True,
                )
                documents = reader.load_data()

                # Remove the unwanted metadata from the documents
                # In case multiple documents are created from the same file ?
                for document in documents:
                    document.metadata.pop("creation_date", None)
                    document.metadata.pop("last_modified_date", None)
                    
                    # Remove the metadata created by the file reader that we dont want to embed and llm
                    document.excluded_embed_metadata_keys = ["file_path","file_name", "file_type", "file_size", "document_id", "doc_id", "ref_doc_id"]
                    document.excluded_llm_metadata_keys = ["file_path","file_name", "file_type", "file_size", "document_id", "doc_id", "ref_doc_id"]

                    # Set the origin metadata of the document
                    document.metadata["origin"] = "upload"
                    document.excluded_embed_metadata_keys.append("origin")
                    document.excluded_llm_metadata_keys.append("origin")

                    # Override the file creation time to the current time with the times from the database
                    # Set the creation and modification times
                    document.metadata["created_at"] = file.file_created_at.isoformat()
                    document.metadata["modified_at"] = file.file_modified_at.isoformat()
                    # Remove from embed and llm
                    document.excluded_embed_metadata_keys.append("created_at")
                    document.excluded_embed_metadata_keys.append("modified_at")
                    document.excluded_llm_metadata_keys.append("created_at")
                    document.excluded_llm_metadata_keys.append("modified_at")

                    # Set the transformations stack name for the datasource_documents
                    document.metadata["transformations_stack_identifier"] = stack_identifier
                    document.excluded_embed_metadata_keys.append("transformations_stack_identifier")
                    document.excluded_llm_metadata_keys.append("transformations_stack_identifier")

                    original_doc_id = document.doc_id

                    # Modify the doc id to append the transformation stack at the end so that they are treated as different documents by the docstore upserts and are managable independently of each other
                    document.doc_id = f"{original_doc_id}_{stack_identifier}"

                    # Get the transformations stack
                    transformations = get_transformations_for_stack(session, stack_identifier)

                    # Update the file in the database with the ref_doc_ids
                    # Do this before the ingestion so that if it crashes we can try to delete the file from the vector store and docstore with its ref_doc_ids and reprocess
                    
                    # Parse the json ref_doc_ids as a list
                    file_ref_doc_ids = json.loads(file.ref_doc_ids) if file.ref_doc_ids else []
                    # Add the new doc id to the list
                    file_ref_doc_ids.append(document.doc_id)
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
                    # This will add the documents to the vector store and docstore in the expected llama index way
                    # Add the embed model to the transformations stack as we always want to embed the results of the processing stacks for search
                    #transformations.append(embed_model)
                    # Set the transformations for the ingestion pipeline
                    ingestion_pipeline.transformations = transformations
                    ingestion_pipeline.run(
                        documents=documents,
                        show_progress=True,
                        #num_workers=None # We process in this thread as it is a child thread managed by the generate service and spawning other threads here causes issue with the uvicorn dev reload mechanism
                    )
                    
                # Save the cache to storage #TODO : Add cache management to delete when too big with cache.clear()
                #ingestion_pipeline.persist(f"/data/.idapt/output/pipeline_storage_{datasource_identifier}")

                # Needed for now as SimpleDocumentStore is not persistent
                doc_store.persist(persist_path=get_docstore_file_path(datasource_identifier, user_id))

                # Get the processed stacks from json
                processed_stacks = json.loads(file.processed_stacks) if file.processed_stacks else []
                # Add the stack to the processed stacks
                processed_stacks.append(stack_identifier)
                file.processed_stacks = json.dumps(processed_stacks)
                # Remove the stack from the stacks to process
                stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else []
                if stack_identifier in stacks_to_process:
                    stacks_to_process = [stack for stack in stacks_to_process if stack != stack_identifier]
                    file.stacks_to_process = json.dumps(stacks_to_process)

                session.commit()

            except Exception as e:
                session.rollback()
                # try to delete the processing stack from llama index as it failed to try to avoid partially processed states
                try:
                    delete_file_processing_stack_from_llama_index(session=session, user_id=user_id, full_path=file.path, processing_stack_identifier=stack_identifier)
                except Exception as e:
                    logger.error(f"Failed to delete erroring file stack {file.path} from stores: {str(e)}")
                # Add the stack to the stacks_to_process list as it failed to process and if we retry to process the file we want it there
                stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else []
                if stack_identifier not in stacks_to_process:
                    stacks_to_process.append(stack_identifier)
                    file.stacks_to_process = json.dumps(stacks_to_process)
                session.commit()
                logger.error(f"Failed to process stack {stack_identifier} for file {file.path}, marking file status as error and letting the stack in stacks_to_process: {str(e)}")
                raise
        
        # All stacks are processed, update status to completed
        file.status = FileStatus.COMPLETED
        file.processing_started_at = datetime.now()
        session.commit()

        logger.info(f"Processed file '{file.path}' for user '{user_id}'")

    except Exception as e:
        logger.error(f"Failed to process file {file.path}: {str(e)}")
        try:
            file.status = FileStatus.ERROR
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update file status for {file.path}: {str(e)}")
        raise









def get_queue_status(session: Session) -> dict:
    """Get the current status of the generation queue"""
    try:
        queued_files = get_db_files_by_status(
            session, 
            FileStatus.QUEUED
        )
        processing_files = get_db_files_by_status(
            session,
            FileStatus.PROCESSING
        )
        
        return {
            "queued_count": len(queued_files),
            "processing_count": len(processing_files),
            "queued_files": [{"name": f.name, "path": f.path} for f in queued_files],
            "processing_files": [{"name": f.name, "path": f.path} for f in processing_files],
        }
    except Exception as e:
        logger.error(f"Failed to get queue status: {str(e)}")
        raise

def should_start_processing(session: Session) -> bool:
    """Check if the processing should start"""
    
    try:
        # Try to get the oldest file that has been processing for the longest time
        oldest_processing_file = session.query(File).filter(
            File.status == FileStatus.PROCESSING
        ).order_by(
            File.processing_started_at.asc()
        ).first()

        if not oldest_processing_file:
            return True

        # If the file has been processing for more than 10 minutes, start start the processing because it is probably stuck/ the app has restarted and processing background task has not been restarted
        if oldest_processing_file.processing_started_at < datetime.now() - datetime.timedelta(seconds=600):
            logger.info(f"Processing file {oldest_processing_file.path} is stuck, starting processing")
            return True

        # A processing is probably still running
        # TODO Make this better
        return False
    
    except Exception as e:
        logger.error(f"Failed to check if processing should start: {str(e)}")
        return False

