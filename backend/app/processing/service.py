from app.datasources.utils import get_datasource_identifier_from_path
from app.datasources.file_manager.service.service import get_file_info
from app.datasources.file_manager.service.llama_index import delete_file_llama_index, delete_file_processing_stack_from_llama_index
from app.datasources.file_manager.database.models import File, FileStatus, Folder
from app.datasources.database.models import Datasource
from app.processing_stacks.database.models import ProcessingStack
from app.datasources.file_manager.service.llama_index import get_llama_index_datasource_folder_path, create_vector_store, create_doc_store
from app.processing_stacks.service import get_transformations_for_stack
from app.ollama_status.service import can_process
from app.datasources.file_manager.utils import validate_path
from app.settings.service import get_setting
from app.processing.schemas import ProcessingItem, ProcessingRequest, ProcessingStatusResponse, ItemProcessingStatusResponse

# Set the llama index default llm and embed model to none otherwise it will raise an error.
# We use on demand initialization of the llm and embed model when needed as it can change depending on the request.
from llama_index.core.settings import Settings
Settings.llm = None
Settings.embed_model = None
from llama_index.core.ingestion import IngestionPipeline, DocstoreStrategy
from llama_index.core.readers import SimpleDirectoryReader

from datetime import datetime, timedelta
import os
from typing import List, Dict
from pathlib import Path
from sqlalchemy.orm import Session
import json
import threading
import asyncio

import logging

logger = logging.getLogger("uvicorn")

# Global processing thread reference
users_processing_threads: Dict[str, threading.Thread] = {}
users_processing_threads_lock = threading.Lock()

users_file_manager_db_sessions: Dict[str, Dict[str, Session]] = {}
users_settings_db_session: Dict[str, Session] = {}
users_processing_stacks_db_session: Dict[str, Session] = {}
users_datasources_db_session: Dict[str, Session] = {}

def start_processing_thread(user_uuid: str, file_manager_db_sessions: Dict[str, Session], datasources_db_session: Session, settings_db_session: Session, processing_stacks_db_session: Session):
    """Start a new processing thread if none is running"""
    global users_processing_threads
    global users_file_manager_db_sessions
    global users_settings_db_session
    global users_processing_stacks_db_session
    global users_datasources_db_session

    with users_processing_threads_lock:
        # Initialize the user's thread entry if it doesn't exist
        if user_uuid not in users_processing_threads:
            users_processing_threads[user_uuid] = None
            
        # Now check if there's an active thread
        if users_processing_threads[user_uuid] and users_processing_threads[user_uuid].is_alive():
            logger.info(f"Processing thread already running")
            return
        
        # Init the global variables for the user if they don't exist
        if user_uuid not in users_file_manager_db_sessions:
            users_file_manager_db_sessions[user_uuid] = {}
        if user_uuid not in users_settings_db_session:
            users_settings_db_session[user_uuid] = {}
        if user_uuid not in users_processing_stacks_db_session:
            users_processing_stacks_db_session[user_uuid] = {}
        if user_uuid not in users_datasources_db_session:
            users_datasources_db_session[user_uuid] = {}
        
        # Store the sessions in the global variables
        # Append the sessions to the global variables
        for datasource_name in file_manager_db_sessions.keys():
            if datasource_name not in users_file_manager_db_sessions[user_uuid]:
                users_file_manager_db_sessions[user_uuid][datasource_name] = file_manager_db_sessions[datasource_name]
        users_settings_db_session[user_uuid] = settings_db_session
        users_processing_stacks_db_session[user_uuid] = processing_stacks_db_session
        users_datasources_db_session[user_uuid] = datasources_db_session
        
        # Create thread sessions
        file_manager_thread_sessions: Dict[str, Session] = {}
        for datasource_name in file_manager_db_sessions.keys():
            file_manager_thread_sessions[datasource_name] = Session(bind=file_manager_db_sessions[datasource_name].get_bind())
        settings_thread_session = Session(bind=settings_db_session.get_bind())
        processing_stacks_thread_session = Session(bind=processing_stacks_db_session.get_bind())
        datasources_thread_session = Session(bind=datasources_db_session.get_bind())

        def process_wrapper():
            try:
                asyncio.run(process_queued_files(file_manager_thread_sessions, datasources_thread_session, settings_thread_session, processing_stacks_thread_session, user_uuid))
            except Exception as e:
                logger.error(f"Processing thread error: {str(e)}")
            finally:
                for file_manager_thread_session in file_manager_thread_sessions.values():
                    file_manager_thread_session.close()
                settings_thread_session.close()
                processing_stacks_thread_session.close()
                datasources_thread_session.close()

        users_processing_threads[user_uuid] = threading.Thread(target=process_wrapper, daemon=True)
        users_processing_threads[user_uuid].start()


def mark_items_as_queued(
        processing_stacks_db_session: Session, 
        file_manager_db_session: Session,
        user_uuid: str, 
        items: List[ProcessingItem]
    ):
    """Mark items as queued"""
    try:
        total_files = 0
        
        for item in items:
            # Validate path
            validate_path(item.original_path)

            # TODO Check if the first part of the path is the right datasource name
            
            # Check if it's a folder
            folder = file_manager_db_session.query(Folder).filter(Folder.original_path == item.original_path).first()
            if folder:
                # Get all files in the folder from the database
                files = file_manager_db_session.query(File).filter(File.path.like(f"{folder.path}%")).all()
                for file in files:
                    mark_file_as_queued(
                        processing_stacks_db_session,
                        file_manager_db_session,
                        file.path,
                        item.stacks_identifiers_to_queue
                    )
                total_files += len(files)
                continue
                
            # If not a folder, try as a file
            file = file_manager_db_session.query(File).filter(File.original_path == item.original_path).first()
            if file:
                mark_file_as_queued(
                    processing_stacks_db_session,
                    file_manager_db_session,
                    file.path,
                    item.stacks_identifiers_to_queue
                )
                total_files += 1
                continue

            logger.warning(f"File or folder {item.original_path} not found, skipping")

    except Exception as e:
        logger.error(f"Failed to mark items as queued: {str(e)}")
        raise

# Not used for now do not use it
def _validate_stacks_to_process_for_file_extension(processing_stacks_db_session: Session, stacks_to_process: List[str], file_extension: str) -> List[str]:
    """Validate the stacks to process for a given file extension"""
    try:
        validated_stacks_to_process = []
        for stack_name in stacks_to_process:
            # Get the stack from the database
            stack = processing_stacks_db_session.query(ProcessingStack).filter(ProcessingStack.identifier == stack_name).first()
            if not stack:
                logger.error(f"Stack {stack_name} not found, skipping")
                continue
            # Check if this transformation stack is applicable to the file type
            if stack.supported_extensions and file_extension in stack.supported_extensions:
                validated_stacks_to_process.append(stack_name)
            else:
                logger.warning(f"Stack {stack_name} does not support file extension {file_extension}, skipping")
                
        return validated_stacks_to_process
    except Exception as e:
        logger.error(f"Failed to validate stacks to process for file extension {file_extension}: {str(e)}")
        return stacks_to_process

def mark_file_as_queued(
        processing_stacks_db_session: Session, 
        file_manager_db_session: Session,
        file_path: str, 
        stacks_to_process: List[str]
    ):
    """Mark a file as queued"""
    try:
        # Get the file extension
        file_extension = os.path.splitext(file_path)[1]
        # For each transformation stack name
        validated_stacks_to_process = _validate_stacks_to_process_for_file_extension(processing_stacks_db_session, stacks_to_process, file_extension)
        
        # Get the file
        file = file_manager_db_session.query(File).filter(File.path == file_path).first()
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
        
        file_manager_db_session.commit()

    except Exception as e:
        file_manager_db_session.rollback()
        logger.error(f"Failed to mark file as queued: {str(e)}")
        raise

async def process_queued_files(
        file_manager_db_sessions: Dict[str, Session],
        datasources_db_session: Session,
        settings_db_session: Session,
        processing_stacks_db_session: Session,
        user_uuid: str
    ):
    """Processing loop"""
    try:
        # TODO Check only for the datasources that are in the files to process
        # TODO Make it work with other providers

        # Wait for Ollama models to be downloaded
        #for file_manager_db_session in file_manager_db_sessions.values():
        await can_process(settings_db_session, True)
   
        logger.info("Beginning processing files")
        # Process all files marked as processing that have been interrupted with unfinished processing
        #await _process_files_marked_as_processing(file_manager_db_session=file_manager_db_session, settings_db_session=settings_db_session, processing_stacks_db_session=processing_stacks_db_session, user_uuid=user_uuid)

        # Process all queued files
        await _process_all_queued_files(file_manager_db_sessions=file_manager_db_sessions, datasources_db_session=datasources_db_session, settings_db_session=settings_db_session, processing_stacks_db_session=processing_stacks_db_session, user_uuid=user_uuid)
   

    except Exception as e:
        logger.error(f"Processing loop error: {str(e)}")
        raise

#async def _process_files_marked_as_processing(file_manager_db_sessions: Dict[str, Session], settings_db_session: Session, processing_stacks_db_session: Session, user_uuid: str):
#    """Process all files marked as processing"""
#    try:
#        logger.info("Processing files marked as processing")
#        files_to_process = []
#        # For each datasource file manager db session we have
#        for file_manager_db_session in file_manager_db_sessions.values():
#            # Get the files one by one so that in case of queued file changes we get the freshest database data
#            oldest_processing_file = file_manager_db_session.query(File).filter(
#                File.status == FileStatus.PROCESSING
#            ).order_by(
#                File.uploaded_at.asc()
#            ).first()
#
#            # If there are no more files marked as processing, return
#            if not oldest_processing_file:
#                continue
#
#            files_to_process.append(oldest_processing_file)
#
#            # Move the processed stacks to the stacks_to_process column as we will delete all already processed stacks from llama index and reprocess them
#            processed_stacks = json.loads(file.processed_stacks)
#            stacks_to_process = json.loads(file.stacks_to_process)
#            stacks_to_process.extend(processed_stacks)
#            file.stacks_to_process = json.dumps(stacks_to_process)
#            file.processed_stacks = json.dumps([])
#            file_manager_db_session.commit()
#
#            logger.info(f"Reprocessing interrupted file: {file.path}")
#            try:
#                delete_file_llama_index(file_manager_session=file_manager_db_session, user_uuid=user_uuid, file=file)
#            except Exception as e:
#                logger.error(f"Failed to delete {file.path} from stores: {str(e)}")
#            
#            try:
#                await _process_single_file(file_manager_db_session=file_manager_db_session, settings_db_session=settings_db_session, processing_stacks_db_session=processing_stacks_db_session, file=file, #user_uuid=user_uuid)
#            except Exception as e:
#                file_manager_db_session.rollback()
#                if file:  # Only try to handle the file if it exists
#                    logger.error(f"Failed to process interrupted file {file.path}: {str(e)}, marking as error")
#                    try:
#                        file.status = FileStatus.ERROR
#                        file_manager_db_session.commit()
#                    except Exception as e:
#                        file_manager_db_session.rollback()
#                        logger.error(f"Failed to update file status for {file.path}: {str(e)}")
#                else:
#                    logger.error(f"Failed to process interrupted file: {str(e)}")
#                    
#
#
#    except Exception as e:
#        logger.error(f"Failed to process all queued files: {str(e)}")
#        raise
        
async def _process_all_queued_files(file_manager_db_sessions: Dict[str, Session], datasources_db_session: Session, settings_db_session: Session, processing_stacks_db_session: Session, user_uuid: str):
    """Process all queued files"""
    try:
        queued_files = []  # Initialize the variable
        # For each datasource file manager db session we have
        for file_manager_db_session in file_manager_db_sessions.values():
            # Get the files one by one so that in case of queued file changes we get the freshest database data
            # Get oldest queued file
            queued_files.extend(file_manager_db_session.query(File).filter(
                File.status == FileStatus.QUEUED
            ).order_by(
                File.uploaded_at.asc()
            ).all())

            if not queued_files:
                continue

            for file in queued_files:
                try:
                    await _process_single_file(file_manager_db_session=file_manager_db_session, datasources_db_session=datasources_db_session, settings_db_session=settings_db_session, processing_stacks_db_session=processing_stacks_db_session, file=file, user_uuid=user_uuid)
                except Exception as e:
                    logger.error(f"Failed to process queued file {file.path}: {str(e)}, marking as error")
                    file.status = FileStatus.ERROR
                    file.error_message = str(e)
                    file_manager_db_session.commit()
                queued_files.remove(file)

        if not queued_files:
            logger.info("No more files to process, stopping")
            # Reset the global variables for the user
            # TODO Make it remove the unuesed datasource once there is no more files in this datasource to process
            users_file_manager_db_sessions[user_uuid] = {}
            users_settings_db_session[user_uuid] = {}
            users_processing_stacks_db_session[user_uuid] = {}
            return

    except Exception as e:
        logger.error(f"Failed to process all queued files: {str(e)}")
        raise

async def _process_single_file(file_manager_db_session: Session, datasources_db_session: Session, settings_db_session: Session, processing_stacks_db_session: Session, file: File, user_uuid: str):
    """Process a single file through the ingestion pipeline"""
    try:
        # Get file response
        file_response = await get_file_info(file_manager_db_session, user_uuid, file.original_path, include_content=False)

        # Update status to processing
        file.error_message = None
        file.status = FileStatus.PROCESSING
        file.processing_started_at = datetime.now()
        file_manager_db_session.commit()

        logger.info(f"Processing file: {file.path}")
        
        # Properly decode JSON stacks with defaults
        stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else []
        processed_stacks = json.loads(file.processed_stacks) if file.processed_stacks else []
        datasource_identifier = get_datasource_identifier_from_path(file.path)
        datasource = datasources_db_session.query(Datasource).filter(Datasource.identifier == datasource_identifier).first()
        
        # Process each stack
        for stack_identifier in stacks_to_process:
            try:
                # If the stack is not already processed, process it
                if processed_stacks and stack_identifier in processed_stacks:
                    logger.info(f"Stack {stack_identifier} already processed, skipping")
                    # Remove the stack from the stacks_to_process list
                    stacks_to_process = [stack for stack in stacks_to_process if stack != stack_identifier]
                    file.stacks_to_process = json.dumps(stacks_to_process)
                    file_manager_db_session.commit()
                    continue

                logger.info(f"Processing stack {stack_identifier} for file {file.path}")
                
                # Create the ingestion pipeline for the datasource
                vector_store = create_vector_store(datasource.identifier, user_uuid)
                doc_store = create_doc_store(datasource.identifier, user_uuid)

                # Create the ingestion pipeline for the datasource
                ingestion_pipeline = IngestionPipeline(
                    name=f"ingestion_pipeline_{datasource.identifier}",
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

                    # Get the embedding settings for this datasource
                    embedding_settings_response = get_setting(settings_db_session, datasource.embedding_setting_identifier)

                    # Get the transformations stack
                    transformations = get_transformations_for_stack(processing_stacks_db_session, stack_identifier, datasource, file_response, embedding_settings_response)

                    # Update the file in the database with the ref_doc_ids
                    # Do this before the ingestion so that if it crashes we can try to delete the file from the vector store and docstore with its ref_doc_ids and reprocess
                    
                    # Parse the json ref_doc_ids as a list
                    file_ref_doc_ids = json.loads(file.ref_doc_ids) if file.ref_doc_ids else []
                    # Add the new doc id to the list
                    file_ref_doc_ids.append(document.doc_id)
                    # Update the file in the database
                    file.ref_doc_ids = json.dumps(file_ref_doc_ids)
                    file_manager_db_session.commit()

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
                docstore_file = Path(get_llama_index_datasource_folder_path(datasource.identifier, user_uuid)) / "docstores" / f"docstore.json"
                doc_store.persist(persist_path=str(docstore_file))

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

                file_manager_db_session.commit()

            except Exception as e:
                file_manager_db_session.rollback()
                # try to delete the processing stack from llama index as it failed to try to avoid partially processed states
                try:
                    delete_file_processing_stack_from_llama_index(file_manager_session=file_manager_db_session, user_uuid=user_uuid, fs_path=file.path, processing_stack_identifier=stack_identifier)
                except Exception as e:
                    logger.error(f"Failed to delete erroring file stack {file.path} from stores: {str(e)}")
                # Add the stack to the stacks_to_process list as it failed to process and if we retry to process the file we want it there
                stacks_to_process = json.loads(file.stacks_to_process) if file.stacks_to_process else []
                if stack_identifier not in stacks_to_process:
                    stacks_to_process.append(stack_identifier)
                    file.stacks_to_process = json.dumps(stacks_to_process)
                file.error_message = str(e)
                file_manager_db_session.commit()
                logger.error(f"Failed to process stack {stack_identifier} for file {file.path}, marking file status as error and letting the stack in stacks_to_process: {str(e)}")
                raise
        
        # All stacks are processed, update status to completed
        file.status = FileStatus.COMPLETED
        file.processing_started_at = datetime.now()
        file_manager_db_session.commit()

        logger.info(f"Processed file '{file.path}' for user '{user_uuid}'")

    except Exception as e:
        logger.error(f"Failed to process file {file.path}: {str(e)}")
        try:
            file.status = FileStatus.ERROR
            file.error_message = str(e)
            file_manager_db_session.commit()
        except Exception as e:
            file_manager_db_session.rollback()
            logger.error(f"Failed to update file status for {file.path}: {str(e)}")
        raise

def get_queue_status(user_uuid: str) -> ProcessingStatusResponse:
    """Get the current status of the generation queue"""
    try:
        processing_status_response = ProcessingStatusResponse(
            queued_count=0,
            queued_items=[],
            processing_count=0,
            processing_items=[]
        )

        file_manager_db_sessions = users_file_manager_db_sessions.get(user_uuid, {})
        if not file_manager_db_sessions:
            # Convert to dict before returning
            return processing_status_response.model_dump()

        for file_manager_db_session in file_manager_db_sessions.values():
            queued_files = file_manager_db_session.query(File).filter(File.status == FileStatus.QUEUED).all()
            processing_files = file_manager_db_session.query(File).filter(File.status == FileStatus.PROCESSING).all()

            for file in queued_files:
                file_queued_stacks : List[str] = []
                for stack in json.loads(file.stacks_to_process):
                    if stack not in file_queued_stacks:
                        file_queued_stacks.append(stack)
                processing_status_response.queued_items.append(
                    ItemProcessingStatusResponse(
                        original_path=file.original_path,
                        name=file.name,
                        queued_stacks=file_queued_stacks,
                        status=file.status.value
                    )
                )
            
            for file in processing_files:
                file_queued_stacks : List[str] = []
                for stack in json.loads(file.stacks_to_process):
                    if stack not in file_queued_stacks:
                        file_queued_stacks.append(stack)
                processing_status_response.processing_items.append(
                    ItemProcessingStatusResponse(
                        original_path=file.original_path,
                        name=file.name,
                        queued_stacks=file_queued_stacks,
                        status=file.status.value
                    )
                )

        processing_status_response.queued_count = len(processing_status_response.queued_items)
        processing_status_response.processing_count = len(processing_status_response.processing_items)

        # Convert to dict before returning
        return processing_status_response.model_dump()

    except Exception as e:
        logger.error(f"Failed to get queue status: {str(e)}")
        raise

def should_start_processing(user_uuid: str) -> bool:
    """Check if the processing should start"""
    
    try:
        for file_manager_db_session in users_file_manager_db_sessions.get(user_uuid, {}).values():
            # Try to get the oldest file that has been processing for the longest time
            oldest_processing_file = file_manager_db_session.query(File).filter(
                File.status == FileStatus.PROCESSING
            ).order_by(
                File.processing_started_at.asc()
            ).first()

            # If the file has been processing for more than 10 minutes, start start the processing because it is probably stuck/ the app has restarted and processing background task has not been restarted
            if oldest_processing_file and oldest_processing_file.processing_started_at < datetime.now() - timedelta(seconds=60 * 15):
                # A processing is probably still running
                # TODO Make this better
                # See if there are any files that are queued
                queued_files = file_manager_db_session.query(File).filter(
                    File.status == FileStatus.QUEUED
                ).first()
                if queued_files:
                    return True
            else:
                # No file currently processing, see if there are any files that are queued
                queued_files = file_manager_db_session.query(File).filter(
                    File.status == FileStatus.QUEUED
                ).first()
                if queued_files:
                    return True
        
        return False
    
    except Exception as e:
        logger.error(f"Failed to check if processing should start: {str(e)}")
        return False

