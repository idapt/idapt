import asyncio
import base64
import os
from pathlib import Path
from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from sse_starlette.sse import EventSourceResponse
import json

from app.api.routers.models import VaultUploadRequest, VaultUploadProgress
from app.config import DATA_DIR
from app.services.file import FileService

vault_router = r = APIRouter()

@r.post("/check-conflicts")
async def check_upload_conflicts(request: VaultUploadRequest) -> list[str]:
    conflicts = []
    for item in request.items:
        if not item.is_folder:
            full_path = Path(DATA_DIR) / item.path
            if full_path.exists():
                conflicts.append(item.path)
    return conflicts

@r.post("/upload")
async def upload_to_vault(
    request: VaultUploadRequest, 
    conflict_resolution: str | None = None
) -> EventSourceResponse:
    async def process_uploads() -> AsyncGenerator[dict, None]:
        total = len(request.items)
        processed = []
        skipped = []
        
        try:
            for idx, item in enumerate(request.items, 1):
                try:
                    full_path = Path(DATA_DIR) / item.path
                    
                    if item.is_folder:
                        os.makedirs(str(full_path), exist_ok=True)
                        processed.append(f"Created folder: {item.path}")
                    else:
                        # Check for file conflict
                        if full_path.exists() and conflict_resolution not in ['overwrite', 'overwrite_all']:
                            if conflict_resolution in ['skip', 'skip_all']:
                                skipped.append(f"Skipped existing file: {item.path}")
                                continue
                            else:
                                # Yield conflict notification
                                yield {
                                    "event": "conflict",
                                    "data": json.dumps({
                                        "path": item.path,
                                        "name": item.name
                                    })
                                }
                                continue

                        # Process and save file
                        os.makedirs(str(full_path.parent), exist_ok=True)
                        file_data, _ = FileService._preprocess_base64_file(item.content)
                        with open(str(full_path), "wb") as f:
                            f.write(file_data)
                        
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
                    yield {
                        "event": "message",
                        "data": VaultUploadProgress(
                            total=total,
                            current=idx,
                            processed_items=processed + skipped,
                            status="error",
                            error=f"Error processing {item.path}: {str(e)}"
                        ).model_dump_json()
                    }
                    return
            
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
