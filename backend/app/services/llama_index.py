import logging

from app.engine.storage_context import StorageContextSingleton

class LlamaIndexService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def delete_file(self, full_path: str):
        try:
            # Delete the file from the LlamaIndex
            StorageContextSingleton().index.delete_ref_doc(full_path, delete_from_docstore=True)

            # Delete the file from the vector store
            StorageContextSingleton().vector_store.delete(full_path)

            # Delete the file from the docstore
            StorageContextSingleton().doc_store.delete_ref_doc(full_path)

        except Exception as e:
            self.logger.error(f"Error deleting file from LlamaIndex: {str(e)}")
            raise

    def rename_file(self, full_old_path: str, full_new_path: str):
        try:

            StorageContextSingleton().index.update_ref_doc(full_old_path, full_new_path)

            #StorageContextSingleton().doc_store.(full_old_path, full_new_path)

        except Exception as e:
            self.logger.error(f"Error renaming file in LlamaIndex: {str(e)}")
            raise

