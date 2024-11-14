from typing import Dict
#from app.engine.index import get_global_index
import logging

logger = logging.getLogger(__name__)

class LlamaIndexService:
    async def remove_document(self, document_id: str):
        pass
        #try:    
        #    # Get the vector store and document store
        #    index = get_global_index()
        #    
        #    # Delete from vector store and document store
        #    index.delete_ref_doc(document_id, delete_from_docstore=True)
        #    
        #    # Force cleanup of both stores
        #    if hasattr(index, '_vector_store'):
        #        await index._vector_store.delete(document_id)
        #    if hasattr(index, '_docstore'):
        #        index._docstore.delete_document(document_id)
        #        
        #    logger.info(f"Deleted document {document_id} from LlamaIndex")
        #except Exception as e:
        #    logger.error(f"Error deleting document {document_id}: {e}")
        #    raise e

    async def update_document(self, document_id: str, metadata: Dict):
        
        # TODO: Implement update for when a file path changes when the file is moved, renamed, parent folder changed etc.
        pass
