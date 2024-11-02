import asyncio
import base64
import os
from pathlib import Path
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse

from app.api.routers.models import VaultUploadRequest, VaultUploadProgress
from app.config import DATA_DIR
from app.services.file import FileService

vault_router = r = APIRouter()

@r.post("/upload")
async def upload_to_vault(request: VaultUploadRequest) -> EventSourceResponse:
    async def process_uploads() -> AsyncGenerator[VaultUploadProgress, None]:
        total = len(request.items)
        processed = []
        
        try:
            for idx, item in enumerate(request.items, 1):
                try:
                    # Create full path
                    full_path = Path(DATA_DIR) / item.path
                    
                    if item.is_folder:
                        os.makedirs(str(full_path), exist_ok=True)
                        processed.append(f"Created folder: {item.path}")
                    else:
                        # Ensure parent directory exists
                        os.makedirs(str(full_path.parent), exist_ok=True)
                        
                        # Process and save file
                        file_data, _ = FileService._preprocess_base64_file(item.content)
                        with open(str(full_path), "wb") as f:
                            f.write(file_data)
                        
                        processed.append(f"Uploaded file: {item.path}")
                    
                    # Yield progress
                    yield VaultUploadProgress(
                        total=total,
                        current=idx,
                        processed_items=processed,
                        status="processing"
                    )
                    
                    # Small delay to prevent overwhelming the system
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    yield VaultUploadProgress(
                        total=total,
                        current=idx,
                        processed_items=processed,
                        status="error",
                        error=f"Error processing {item.path}: {str(e)}"
                    )
                    return
            
            # Final success message
            yield VaultUploadProgress(
                total=total,
                current=total,
                processed_items=processed,
                status="completed"
            )
            
        except Exception as e:
            yield VaultUploadProgress(
                total=total,
                current=0,
                processed_items=[],
                status="error",
                error=f"Upload failed: {str(e)}"
            )

    return EventSourceResponse(process_uploads())
