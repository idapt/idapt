
import logging

from app.engine.storage_context import StorageContextSingleton
from app.services.file_system import get_full_path_from_path

class LlamaIndexService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def delete_file(self, path: str):
        try:
            # Get the full path from the path
            full_path = get_full_path_from_path(path)
            
            # Delete the file from the LlamaIndex
            StorageContextSingleton().index.delete_ref_doc(full_path, delete_from_docstore=True)

            # Delete the file from the docstore
            #StorageContextSingleton().doc_store.delete(full_path)

            # Delete the file from the vector store
            #StorageContextSingleton().vector_store.delete(full_path)

        except Exception as e:
            self.logger.error(f"Error deleting file from LlamaIndex: {str(e)}")
            raise

    def rename_file(self, old_path: str, new_path: str):
        try:
            full_old_path = get_full_path_from_path(old_path)
            full_new_path = get_full_path_from_path(new_path)
            
            StorageContextSingleton().index.update_ref_doc(full_old_path, full_new_path)

            #StorageContextSingleton().doc_store.update_ref_doc(full_old_path, full_new_path)
        except Exception as e:
            self.logger.error(f"Error renaming file in LlamaIndex: {str(e)}")
            raise

