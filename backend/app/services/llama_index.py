import json
import logging
from app.services.database import get_session
from app.services.datasource import get_vector_store, get_doc_store
from app.services.db_file import get_file

class LlamaIndexService:
    def __init__(self):

        self.logger = logging.getLogger(__name__)

    def delete_file(self, full_path: str):
        try:
            # Get the file's ref_doc_ids from the database
            with get_session() as session:
                file = get_file(session, full_path)
                if not file or not file.ref_doc_ids:
                    self.logger.warning(f"No ref_doc_ids found for file: {full_path}")
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
                        self.logger.warning(f"Failed to delete {ref_doc_id} from vector store and docstore probably because it was already deleted or does not exist in them : {str(e)}")
                    # In any case delete the ref_doc_id from the file
                    finally:
                        self.logger.info(f"Deleting {ref_doc_id} relation from file {file.path}")
                        # Delete the ref_doc_id from the file
                        file.ref_doc_ids = [ref_doc_id for ref_doc_id in file.ref_doc_ids if ref_doc_id != ref_doc_id]
                        # Delete the processing stack identifier from the processed_stacks list after having it converted to json and reconverting it to a string
                        processed_stacks = json.loads(file.processed_stacks) if file.processed_stacks else []
                        processed_stacks = [stack_id for stack_id in processed_stacks if stack_id != processing_stack_identifier]
                        file.processed_stacks = json.dumps(processed_stacks)
                        # Commit the changes to the file the database
                        session.commit()
                    

        except Exception as e:
            self.logger.error(f"Error deleting file from LlamaIndex: {str(e)}")
            raise

    def rename_file(self, full_old_path: str, full_new_path: str):
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
            generate_service.add_files_to_queue([{
                "path": full_new_path,
                "transformations_stack_name_list": ["default"]
            }])

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

