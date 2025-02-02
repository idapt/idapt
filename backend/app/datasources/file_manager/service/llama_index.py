import os
import chromadb
import logging
from pathlib import Path
import json
from fastapi import HTTPException
import shutil

from sqlalchemy.orm import Session
from app.datasources.file_manager.database.models import File, FileStatus, Folder
from app.datasources.database.models import Datasource
from app.datasources.file_manager.service.db_operations import get_db_folder_files_recursive
from app.settings.schemas import AppSettings, SettingResponse
from app.settings.service import get_setting
from app.api.user_path import get_user_app_data_dir
from app.datasources.file_manager.utils import validate_path

from llama_index.core.storage import StorageContext
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.tools import BaseTool, QueryEngineTool
from llama_index.core.tools import ToolMetadata
from llama_index.core.retrievers import VectorIndexRetriever#, AutoMergingRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.llms import LLM
from llama_index.core.base.embeddings.base import BaseEmbedding


logger = logging.getLogger("uvicorn")

# Private methods for creating components
def create_vector_store(datasource_identifier: str, user_id: str) -> ChromaVectorStore:
    try:
        # Create the embeddings directory if it doesn't exist
        datasource_embeddings_dir = Path(get_llama_index_datasource_folder_path(datasource_identifier, user_id)) / "embeddings"

        # Create the parent directory if it doesn't exist
        datasource_embeddings_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a Chroma persistent client with telemetry disabled
        client = chromadb.PersistentClient(
            path=str(datasource_embeddings_dir),
            settings=chromadb.Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        # Create a Chroma collection using a generic name because there is limitation on collection names
        collection_name = f"chroma_collection"
        chroma_collection = client.get_or_create_collection(name=collection_name)
        # Create a Chroma vector store
        vector_store = ChromaVectorStore.from_collection(
            chroma_collection
        )
        return vector_store
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}")
        raise

def get_llama_index_datasource_folder_path(datasource_identifier: str, user_id: str) -> str:
    return f"{get_user_app_data_dir(user_id)}/processed/{datasource_identifier}"

def create_doc_store(datasource_identifier: str, user_id: str) -> SimpleDocumentStore:
    try:
        # Create the docstore directory if it doesn't exist
        docstore_file = Path(get_llama_index_datasource_folder_path(datasource_identifier, user_id)) / "docstores" / f"docstore.json"
        docstore_file.parent.mkdir(parents=True, exist_ok=True)

        docstore = None
        # If the file doesn't exist, create a new docstore and persist it
        if not docstore_file.exists():
            docstore = SimpleDocumentStore()
            docstore.persist(persist_path=str(docstore_file))
        else:
            docstore = SimpleDocumentStore.from_persist_path(
                str(docstore_file)
            )

        return docstore
    except Exception as e:
        logger.error(f"Error creating doc store: {str(e)}")
        raise

def create_query_tool(
    settings_db_session: Session, 
    datasources_db_session: Session,
    datasource_identifier: str,
    vector_store: ChromaVectorStore,
    doc_store: SimpleDocumentStore, 
    embed_model: BaseEmbedding, 
    llm: LLM
) -> BaseTool:
    try:
    
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
            docstore=doc_store
        )

        # Recreate the index from the vector store and doc store at each app restart if needed
        index = VectorStoreIndex.from_documents(
            [],  # Empty nodes as they will be loaded from storage context
            storage_context=storage_context,
            embed_model=embed_model
        )

        # Get the app settings
        app_settings_response : SettingResponse = get_setting(settings_db_session=settings_db_session, identifier="app")
        app_settings : AppSettings = AppSettings.model_validate_json(app_settings_response.value_json)
    
        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=int(app_settings.top_k)
        )
        # Don't use this for now as we are not using hierarchical node parser
        #retriever = AutoMergingRetriever(
        #    retriever,
        #    storage_context=index.storage_context,
        #    verbose=True
        #)
        response_synthesizer = get_response_synthesizer(
            response_mode="compact",
            llm=llm
        )

        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            response_synthesizer=response_synthesizer,
        )
        
        # Get datasource info within session and extract needed data
        description = ""
        datasource = datasources_db_session.query(Datasource).filter(Datasource.identifier == datasource_identifier).first()
        if not datasource or not datasource.description or datasource.description == "":
            description = f"Query engine for the {datasource_identifier} datasource"
        else:
            description = datasource.description

        # Add this instruction to the tool description for the agent to know how to use the tool # ? Great ?
        tool_description = f"{description}\nUse a detailed plain text question as input to the tool."
        
        return QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name=f"{datasource.identifier}_query_engine",
                description=tool_description
            ),
            resolve_input_errors=True
        )
    except Exception as e:
        logger.error(f"Error creating query tool: {str(e)}")
        raise

# ? Move to file manager ?
async def delete_item_from_llama_index(file_manager_session: Session, user_id: str, original_path: str):
    """
    Delete an item from the llama index
    If it is a file, delete the file from the llama index
    If it is a folder, delete all the files in the folder from the llama index
    """
    try:
        # Validate path
        validate_path(original_path)

        # Check if it's a file
        file = file_manager_session.query(File).filter(File.original_path == original_path).first()
        if file:
            # Delete llama index data
            delete_file_llama_index(file_manager_session=file_manager_session, user_id=user_id, file=file)
            return {"success": True}
            
        # If not a file, check if it's a folder
        folder = file_manager_session.query(Folder).filter(Folder.original_path == original_path).first()
        if folder:
            delete_files_in_folder_recursive_from_llama_index(file_manager_session=file_manager_session, user_id=user_id, full_folder_path=folder.path)
            return {"success": True}
            
        raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        logger.error(f"Error deleting item from LlamaIndex: {str(e)}")
        raise

def delete_files_in_folder_recursive_from_llama_index(file_manager_session: Session, user_id: str, full_folder_path: str):
    try:
        # Get the files in the folder recursively from the database
        files, _ = get_db_folder_files_recursive(file_manager_session, full_folder_path)
        
        # Delete each file from the llama index
        for file in files:
            try:
                delete_file_llama_index(file_manager_session, user_id, file)
            except Exception as e:
                logger.warning(f"Failed to delete {file.path} from LlamaIndex: {str(e)}")

    except Exception as e:
        file_manager_session.rollback()
        logger.error(f"Error deleting files in folder from LlamaIndex: {str(e)}")
        raise

def delete_datasource_llama_index_components(datasource_identifier: str, user_id: str):
    try:        
        # Get the paths
        datasource_embeddings_dir = Path(get_llama_index_datasource_folder_path(datasource_identifier, user_id)) / "embeddings"
        
        # First close any open ChromaDB connections
        try:
            client = chromadb.PersistentClient(
                path=str(datasource_embeddings_dir),
                settings=chromadb.Settings( # Need to be the same settings as the one used to create the vector store
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            # Needed otherwise the client can persist in memory even if the files are deleted
            client.reset()
        except Exception as e:
            logger.warning(f"Error closing ChromaDB connection: {str(e)}")

        # Delete the datasource llama index directory
        #llama_index_datasource_folder_path = Path(get_llama_index_datasource_folder_path(datasource_identifier, user_id))
        #if os.path.exists(llama_index_datasource_folder_path):
        #    try:
        #        shutil.rmtree(llama_index_datasource_folder_path, ignore_errors=True)
        #        logger.info(f"Deleted datasource llama index directory: {llama_index_datasource_folder_path}")
        #    except Exception as e:
        #        logger.error(f"Error deleting datasource llama index directory: {str(e)}")
        #        raise

        # Delete the entire vector store directory
        # Known bug where recreating it lead to read permission errors https://github.com/langchain-ai/langchain/issues/14872
        #if os.path.exists(vector_store_path):
        #    try:
        #        shutil.rmtree(vector_store_path, ignore_errors=True)
        #        logger.info(f"Deleted vector store directory: {vector_store_path}")
        #    except Exception as e:
        #        logger.error(f"Error deleting vector store directory: {str(e)}")
        #        raise


        docstore_file = Path(get_llama_index_datasource_folder_path(datasource_identifier, user_id)) / "docstores" / f"docstore.json"
        # Delete the docstore file
        if os.path.exists(docstore_file):
            try:
                os.remove(docstore_file)
                logger.info(f"Deleted docstore file: {docstore_file}")
            except Exception as e:
                logger.error(f"Error deleting docstore file: {str(e)}")
                raise
            
    except Exception as e:
        logger.error(f"Error deleting datasource llama index components: {str(e)}")
        raise

def delete_file_llama_index(file_manager_session: Session, user_id: str, file: File):
    try:
        if file.status == FileStatus.PROCESSING:
            raise Exception(f"File {file.path} is currently being processed, please wait for it to finish or cancel the processing before deleting it")

        from app.datasources.utils import get_datasource_identifier_from_path
        # Get the datasource vector store and docstore
        datasource_identifier = get_datasource_identifier_from_path(file.path)
        vector_store = create_vector_store(datasource_identifier, user_id)
        doc_store = create_doc_store(datasource_identifier, user_id)

        # Delete each ref_doc_id from the vector store and docstore
        # Parse the json ref_doc_ids as a list
        ref_doc_ids = json.loads(file.ref_doc_ids) if file.ref_doc_ids else []
        for ref_doc_id in ref_doc_ids:
            # Get the processing stack identifier from last part after the _ in the ref_doc_id
            processing_stack_identifier = ref_doc_id.split("_")[-1]
            try:
                # Delete the ref_doc_id from the vector store
                vector_store.delete(ref_doc_id)
                # Delete the ref_doc_id from the docstore
                doc_store.delete_document(ref_doc_id)
            except Exception as e:
                logger.warning(f"Failed to delete {ref_doc_id} from vector store and docstore probably because it was already deleted or does not exist in them : {str(e)}")
            # In any case delete the ref_doc_id from the file
            finally:
                logger.info(f"Deleting {ref_doc_id} relation from file {file.path}")
                # Delete the ref_doc_id from the file
                file.ref_doc_ids = [ref_doc_id for ref_doc_id in file.ref_doc_ids if ref_doc_id != ref_doc_id]
                # Delete the processing stack identifier from the processed_stacks list after having it converted to json and reconverting it to a string
                processed_stacks = json.loads(file.processed_stacks) if file.processed_stacks else []
                processed_stacks = [stack_id for stack_id in processed_stacks if stack_id != processing_stack_identifier]
                file.processed_stacks = json.dumps(processed_stacks)
                # Commit the changes to the file the database
                file_manager_session.flush() # Commit ?

        # Mark the file statuis as pending
        file.status = FileStatus.PENDING
        # Remove already processed stacks from the file
        file.processed_stacks = json.dumps([])
        # Remove all pending stacks from the file # ?
        file.stacks_to_process = json.dumps([])
        # Commit the changes to the file the database
        file_manager_session.commit()

        # Needed for now as SimpleDocumentStore is not persistent
        docstore_file = Path(get_llama_index_datasource_folder_path(datasource_identifier, user_id)) / "docstores" / f"docstore.json"
        doc_store.persist(persist_path= str(docstore_file))

    except Exception as e:
        file_manager_session.rollback()
        logger.error(f"Error deleting file from LlamaIndex: {str(e)}")
        raise e

def delete_file_processing_stack_from_llama_index(file_manager_session: Session, user_id: str, fs_path: str, processing_stack_identifier: str):
    try:
        # Get the file's ref_doc_ids from the database
        file = file_manager_session.query(File).filter(File.path == fs_path).first()
        if not file or not file.ref_doc_ids:
            logger.warning(f"No ref_doc_ids found for file: {fs_path}")
            return

        from app.datasources.utils import get_datasource_identifier_from_path
        # Get the datasource name from the path
        datasource_identifier = get_datasource_identifier_from_path(fs_path)


        # Get the datasource vector store and docstore
        vector_store = create_vector_store(datasource_identifier, user_id)
        doc_store = create_doc_store(datasource_identifier, user_id)

        # Delete each ref_doc_id from the vector store and docstore
        # Parse the json ref_doc_ids as a list
        ref_doc_ids = json.loads(file.ref_doc_ids) if file.ref_doc_ids else []

        # Keep only the ref_doc_ids that are with the processing stack identifier
        ref_doc_ids = [ref_doc_id for ref_doc_id in ref_doc_ids if processing_stack_identifier in ref_doc_id]

        for ref_doc_id in ref_doc_ids:
            try:
                # Delete the ref_doc_id from the vector store
                vector_store.delete(ref_doc_id)
                # Delete the ref_doc_id from the docstore
                doc_store.delete_document(ref_doc_id)
            except Exception as e:
                logger.warning(f"Failed to delete {ref_doc_id} from vector store and docstore probably because it was already deleted or does not exist in them : {str(e)}")
            # In any case delete the ref_doc_id from the file
            finally:
                logger.info(f"Deleting {ref_doc_id} relation from file {file.path}")
                # Delete the ref_doc_id from the file
                file.ref_doc_ids = [ref_doc_id for ref_doc_id in file.ref_doc_ids if ref_doc_id != ref_doc_id]
                # Delete the processing stack identifier from the processed_stacks list after having it converted to json and reconverting it to a string
                processed_stacks = json.loads(file.processed_stacks) if file.processed_stacks else []
                processed_stacks = [stack_id for stack_id in processed_stacks if stack_id != processing_stack_identifier]
                file.processed_stacks = json.dumps(processed_stacks)
                # Commit the changes to the file the database
                file_manager_session.commit()

        # Needed for now as SimpleDocumentStore is not persistent
        docstore_file = Path(get_llama_index_datasource_folder_path(datasource_identifier, user_id)) / "docstores" / f"docstore.json"
        doc_store.persist(persist_path=str(docstore_file))
        
    except Exception as e:
        logger.error(f"Error deleting file processing stack from LlamaIndex: {str(e)}")
        raise

#def rename_file_llama_index(session: Session, full_old_path: str, full_new_path: str):
#    try:

#        from app.services.datasource import get_datasource_identifier_from_path
#        # Get the datasource name from the path 
#        datasource_identifier = get_datasource_identifier_from_path(full_old_path)

        # Get the datasource vector store and docstore
        #vector_store = create_vector_store(datasource_identifier, user_id)
        #doc_store = create_doc_store(datasource_identifier, user_id)

        # For now simply delete the old file from the vector store and docstore
        #vector_store.delete(full_old_path)
        #doc_store.delete_ref_doc(full_old_path)

        # And sent it to generate again to pass it through the ingestion pipeline with the default transformations # TODO VERY BAD IMPLEMENTATION

        # Add the file to the generation queue with default transformations
        #from app.services.generate import GenerateService
        #generate_service = GenerateService()
        #generate_service.add_files_to_queue([{
        #    "path": full_new_path,
        #    "stacks_identifiers_to_queue": ["default"]
        #}])

        # Get the the old ref doc info document
        #ref_doc_info = doc_store.get_ref_doc_info(full_old_path)
        # Get all the nodes of this document from
        #nodes = vector_store.get_nodes(ref_doc_info.node_ids)

        # Delete the old document
        #doc_store.delete_ref_doc(full_old_path)
        #vector_store.delete(full_old_path)

        # Update ref doc info with the new path
        # ref_doc_info. = full_new_path # TODO Check if this is the correct implementation
        
        # Update the nodes with the new path
        #for node in nodes:
        #    node.ref_doc_id = full_new_path

        # Build the new document
        #document = Document(
        #    metadata=ref_doc_info.metadata,
        #    doc_id=ref_doc_info.doc_id,
        #    ref_doc_id=full_new_path
        #    nodes=nodes,
        #    text=ref_doc_info,
        #)

        #doc_store.update_ref_doc(full_old_path, document)

        # Update the file in the vector store
        #vector_store.update_ref_doc(full_old_path, full_new_path)

        # Update the file in the docstore
        #doc_store.update_ref_doc(full_old_path, full_new_path)

#    except Exception as e:
#        logger.error(f"Error renaming file in LlamaIndex: {str(e)}")
#        raise

