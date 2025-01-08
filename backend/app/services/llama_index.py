from sqlalchemy.orm import Session
from app.database.models import Datasource
from app.services.db_file import get_db_file
from app.settings.models import AppSettings

from llama_index.core.storage import StorageContext
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.tools import BaseTool, QueryEngineTool
from llama_index.core.tools import ToolMetadata
from llama_index.core.retrievers import VectorIndexRetriever#, AutoMergingRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.settings import Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.storage.docstore import SimpleDocumentStore
from llama_index.core.llms import LLM
import chromadb

import logging
from typing import Tuple
from sqlalchemy import text
from pathlib import Path
import json

logger = logging.getLogger("uvicorn")


def get_storage_components(datasource_identifier: str) -> Tuple[ChromaVectorStore, SimpleDocumentStore]:
    """Get or create all storage components for a datasource"""
    try:
        vector_store = get_vector_store(datasource_identifier)
        doc_store = get_doc_store(datasource_identifier)
        return vector_store, doc_store
    except Exception as e:
        logger.error(f"Error getting storage components: {str(e)}")
        raise

def get_vector_store(datasource_identifier: str) -> ChromaVectorStore:
    # TODO Add caching
    return _create_vector_store(datasource_identifier)

def get_doc_store(datasource_identifier: str) -> SimpleDocumentStore:
    # TODO Add caching
    return _create_doc_store(datasource_identifier)

def get_index(datasource_identifier: str) -> VectorStoreIndex:
    # TODO Add caching
    return _create_index(datasource_identifier)

def get_query_tool(session: Session, datasource_identifier: str, llm: LLM, app_settings: AppSettings) -> BaseTool:
    # TODO Add caching
    return _create_query_tool(session, datasource_identifier, llm, app_settings)




def _delete_llama_index_components(session: Session, datasource_identifier: str):
    """Delete all llama-index components for a datasource"""
    try:

        # Drop vector store table
        query = text('DROP TABLE IF EXISTS public.data_{}_{}'.format(
            datasource_identifier, "embeddings"))
        session.execute(query)

        # Drop doc store table
        query = text('DROP TABLE IF EXISTS public.data_{}_{}'.format(
            datasource_identifier, "docstore"))
        session.execute(query)

        # Drop index store table
        query = text('DROP TABLE IF EXISTS public.data_{}_{}'.format(
            datasource_identifier, "index"))
        session.execute(query)
                        
        session.commit()
    
        # Clean up the in-memory references
        # TODO Add caching

    except Exception as e:
        logger.error(f"Error deleting llama-index components: {str(e)}")
        raise

# Private methods for creating components
def _create_vector_store(datasource_identifier: str) -> ChromaVectorStore:
    try:
        # Create the embeddings directory if it doesn't exist
        embeddings_dir = Path("/data/.idapt/embeddings")
        embeddings_dir.mkdir(parents=True, exist_ok=True)
        embeddings_file = embeddings_dir / f"{datasource_identifier}"
        
        # Create a Chroma persistent client
        client = chromadb.PersistentClient(path=str(embeddings_file))
        # Create a Chroma collection
        chroma_collection = client.get_or_create_collection(name=datasource_identifier)
        # Create a Chroma vector store
        vector_store = ChromaVectorStore.from_collection(
            chroma_collection
        )
        return vector_store
    except Exception as e:
        logger.error(f"Error creating vector store: {str(e)}")
        raise

def _create_doc_store(datasource_identifier: str) -> SimpleDocumentStore:
    try:
        # Create the docstore directory if it doesn't exist
        docstores_dir = Path("/data/.idapt/docstores")
        docstores_dir.mkdir(parents=True, exist_ok=True)
        docstore_file = docstores_dir / f"{datasource_identifier}.json"

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

def _create_index(datasource_identifier: str) -> VectorStoreIndex:
    try:
        vector_store, doc_store = get_storage_components(datasource_identifier)

        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
            docstore=doc_store
        )

        # Recreate the index from the vector store and doc store at each app restart if needed
        index = VectorStoreIndex.from_documents(
            [],  # Empty nodes as they will be loaded from storage context
            storage_context=storage_context
        )

        return index
    except Exception as e:
        logger.error(f"Error creating index: {str(e)}")
        raise

def _create_query_tool(session: Session, datasource_identifier: str, llm: LLM, app_settings: AppSettings) -> BaseTool:
    try:
        index = get_index(datasource_identifier)

        retriever = VectorIndexRetriever(
            index=index,
            similarity_top_k=int(app_settings.top_k),
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
        datasource = session.query(Datasource).filter(Datasource.identifier == datasource_identifier).first()
        if not datasource or not datasource.description or datasource.description == "":
            description = f"Query engine for the {datasource_identifier} datasource"
        else:
            description = datasource.description

        # Add this instruction to the tool description for the agent to know how to use the tool # ? Great ?
        tool_description = f"{description}\nUse a detailed plain text question as input to the tool."
        
        return QueryEngineTool(
            query_engine=query_engine,
            metadata=ToolMetadata(
                name=f"{datasource_identifier}_query_engine",
                description=tool_description
            ),
            resolve_input_errors=True
        )
    except Exception as e:
        logger.error(f"Error creating query tool: {str(e)}")
        raise



def delete_file_llama_index(session: Session, full_path: str):
    try:
        # Get the file's ref_doc_ids from the database
        file = get_db_file(session, full_path)
        if not file or not file.ref_doc_ids:
            logger.warning(f"No ref_doc_ids found for file: {full_path}")
            return

        from app.services.datasource import get_datasource_identifier_from_path
        # Get the datasource name from the path
        datasource_identifier = get_datasource_identifier_from_path(full_path)

        # Get the datasource vector store and docstore
        vector_store = get_vector_store(datasource_identifier)
        doc_store = get_doc_store(datasource_identifier)

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
                session.commit()

        # Needed for now as SimpleDocumentStore is not persistent
        doc_store.persist(persist_path=get_docstore_path(datasource_identifier))


    except Exception as e:
        logger.error(f"Error deleting file from LlamaIndex: {str(e)}")
        raise

def get_docstore_path(datasource_identifier: str) -> str:
    return f"/data/.idapt/docstores/{datasource_identifier}.json"

def get_indexstore_path(datasource_identifier: str) -> str:
    return f"/data/.idapt/indexstores/{datasource_identifier}.json"

def rename_file_llama_index(session: Session, full_old_path: str, full_new_path: str):
    try:

        from app.services.datasource import get_datasource_identifier_from_path
        # Get the datasource name from the path 
        datasource_identifier = get_datasource_identifier_from_path(full_old_path)

        # Get the datasource vector store and docstore
        vector_store = get_vector_store(datasource_identifier)
        doc_store = get_doc_store(datasource_identifier)

        # For now simply delete the old file from the vector store and docstore
        vector_store.delete(full_old_path)
        doc_store.delete_ref_doc(full_old_path)

        # And sent it to generate again to pass it through the ingestion pipeline with the default transformations # TODO VERY BAD IMPLEMENTATION

        # Add the file to the generation queue with default transformations
        #from app.services.generate import GenerateService
        #generate_service = GenerateService()
        #generate_service.add_files_to_queue([{
        #    "path": full_new_path,
        #    "transformations_stack_name_list": ["default"]
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

    except Exception as e:
        logger.error(f"Error renaming file in LlamaIndex: {str(e)}")
        raise

