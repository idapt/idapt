import asyncio
import base64
import os
from pathlib import Path
from typing import AsyncGenerator
from fastapi import APIRouter, BackgroundTasks, Depends
from sse_starlette.sse import EventSourceResponse
import json
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from app.api.routers.models import VaultUploadRequest, VaultUploadProgress
from app.config import DATA_DIR
from app.services.file import FileService
from app.services.db_file import DBFileService
from app.database.connection import get_db_session
vault_router = r = APIRouter()

async def trigger_generate():
    """Trigger the generate endpoint after upload"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post("http://localhost:8000/api/generate")
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to trigger generate endpoint: {e}")

@r.post("/upload")
async def upload_to_vault(
    request: VaultUploadRequest,
    background_tasks: BackgroundTasks,
    conflict_resolution: str | None = None,
    session: Session = Depends(get_db_session)
) -> EventSourceResponse:
    async def process_uploads() -> AsyncGenerator[dict, None]:
        total = len(request.items)
        processed = []
        skipped = []
        
        print(f"Processing {total} upload items")
        
        try:
            for idx, item in enumerate(request.items, 1):
                try:
                    print(f"Processing item {idx}/{total}: {item.path}")
                    
                    # Store full path for filesystem operations
                    full_path = Path(DATA_DIR) / item.path
                    
                    # Get relative path for database operations by removing idapt_data prefix
                    db_path = str(full_path).replace(str(DATA_DIR), '').lstrip('/')
                    
                    if item.is_folder:
                        os.makedirs(str(full_path), exist_ok=True)
                        # Create folder in database with cleaned path
                        DBFileService.create_folder_path(session, db_path)
                        processed.append(f"Created folder: {item.path}")
                    else:
                        # Check for file conflict
                        if full_path.exists() and conflict_resolution not in ['overwrite', 'overwrite_all']:
                            if conflict_resolution in ['skip', 'skip_all']:
                                skipped.append(f"Skipped existing file: {item.path}")
                                continue
                            else:
                                yield {
                                    "event": "conflict",
                                    "data": json.dumps({
                                        "path": item.path,
                                        "name": item.name
                                    })
                                }
                                continue

                        # Process and save file to disk
                        os.makedirs(str(full_path.parent), exist_ok=True)
                        file_data, _ = FileService._preprocess_base64_file(item.content)
                        with open(str(full_path), "wb") as f:
                            f.write(file_data)
                        
                        # Create folder structure and file in database with cleaned path
                        parent_path = str(Path(db_path).parent)
                        folder = None if parent_path in ['', '.'] else DBFileService.create_folder_path(session, parent_path)
                        
                        DBFileService.create_file(
                            session=session,
                            name=item.name,
                            folder_id=folder.id if folder else None,
                            original_created_at=item.original_created_at,
                            original_modified_at=item.original_modified_at,
                        )
                        
                        processed.append(f"Uploaded file: {item.path}")

                    yield {
                        "event": "message",
                        "data": VaultUploadProgress(
                            total=total,
                            current=idx,
                            processed_items=processed + skipped,
                            status="processing"
                        ).model_dump_json()
                    }
                    
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    print(f"Error processing item: {str(e)}")
                    error_message = str(e)
                    yield {
                        "event": "message",
                        "data": VaultUploadProgress(
                            total=total,
                            current=idx,
                            processed_items=processed + skipped,
                            status="error",
                            error=f"Error processing {item.path}: {error_message}"
                        ).model_dump_json()
                    }
                    return

            # Trigger generate endpoint after successful upload
            background_tasks.add_task(trigger_generate)
            
            # Final success message
            yield {
                "event": "message",
                "data": VaultUploadProgress(
                    total=total,
                    current=total,
                    processed_items=processed + skipped,
                    status="completed"
                ).model_dump_json()
            }

        except Exception as e:
            yield {
                "event": "message",
                "data": VaultUploadProgress(
                    total=total,
                    current=0,
                    processed_items=[],
                    status="error",
                    error=f"Upload failed: {str(e)}"
                ).model_dump_json()
            }
            
    return EventSourceResponse(process_uploads())
