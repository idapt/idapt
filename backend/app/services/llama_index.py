import logging

from llama_index.core import Document

class LlamaIndexService:
    def __init__(self):

        self.logger = logging.getLogger(__name__)

    def delete_file(self, full_path: str):
        try:

            # Get the service manager instance to avoid circular dependencies
            from app.services import ServiceManager
            service_manager = ServiceManager.get_instance()
            datasource_service = service_manager.datasource_service

            from app.services.datasource import get_datasource_name_from_path
            # Get the datasource name from the path
            datasource_name = get_datasource_name_from_path(full_path)

            # Get the datasource vector store and docstore
            vector_store = datasource_service.get_vector_store(datasource_name)
            doc_store = datasource_service.get_doc_store(datasource_name)

            # Delete the file from the vector store
            vector_store.delete(full_path)

            # Delete the file from the docstore
            doc_store.delete_ref_doc(full_path)

        except Exception as e:
            self.logger.error(f"Error deleting file from LlamaIndex: {str(e)}")
            raise

    def rename_file(self, full_old_path: str, full_new_path: str):
        try:

            # Get the service manager instance to avoid circular dependencies
            from app.services import ServiceManager
            service_manager = ServiceManager.get_instance()
            datasource_service = service_manager.datasource_service

            from app.services.datasource import get_datasource_name_from_path
            # Get the datasource name from the path 
            datasource_name = get_datasource_name_from_path(full_old_path)

            # Get the datasource vector store and docstore
            vector_store = datasource_service.get_vector_store(datasource_name)
            doc_store = datasource_service.get_doc_store(datasource_name)

            # For now simply delete the old file from the vector store and docstore
            vector_store.delete(full_old_path)
            doc_store.delete_ref_doc(full_old_path)

            # And sent it to generate again to pass it through the ingestion pipeline with the default transformations # TODO VERY BAD IMPLEMENTATION
            
            # self.generate_service.add_to_queue(full_new_path) # Use the default transformations for now

            # Add the file to the generation queue with default transformations
            service_manager.generate_service.add_to_queue({
                "path": full_new_path,
                "transformations_stack_name_list": ["default"]
            })

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
            self.logger.error(f"Error renaming file in LlamaIndex: {str(e)}")
            raise

