import os
from llama_index.core.storage.docstore import SimpleDocumentStore

def get_doc_store():
    # If the storage directory is there, load the document store from it.
    # If not, set up an in-memory document store since we can't load from a directory that doesn't exist.
    if os.path.exists(STORAGE_DIR):
        return SimpleDocumentStore.from_persist_dir(STORAGE_DIR)
    else:
        return SimpleDocumentStore()
