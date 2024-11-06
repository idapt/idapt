from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.responses import Response
from sse_starlette.sse import EventSourceResponse
import asyncio
import json
from typing import List, AsyncGenerator

from app.database.connection import get_db_session
from app.services.file_manager import FileManagerService, convert_db_path_to_filesystem_path, convert_filesystem_path_to_db_path
from app.api.routers.models import FileNode, FileUploadRequest, FileUploadProgress
from app.services.db_file import DBFileService
from app.services.file import FileService

import base64
import os
from pathlib import Path
from typing import AsyncGenerator
import httpx
from datetime import datetime
from app.config import DATA_DIR

import logging
logger = logging.getLogger(__name__)

file_manager_router = r = APIRouter()
file_manager = FileManagerService()


async def trigger_generate(file_paths: List[str]):
    """Trigger the generate endpoint after upload with specific files"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/api/generate",
                json={"file_paths": file_paths}
            )
            response.raise_for_status()
        except Exception as e:
            logger.error(f"Failed to trigger generate endpoint: {e}")


@r.post("/upload")
async def upload_files(
    request: FileUploadRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session)
) -> EventSourceResponse:
    async def process_uploads() -> AsyncGenerator[dict, None]:
        total = len(request.items)
        processed = []
        skipped = []
        file_paths = []
        
        print(f"Processing {total} upload items")
        
        try:
            for idx, item in enumerate(request.items, 1):
                try:
                    print(f"Processing item {idx}/{total}: {item.path}")
                    
                    # Store full path for filesystem operations
                    full_path = Path(convert_db_path_to_filesystem_path(item.path))
                    
                    # Get relative path for database operations
                    db_path = convert_filesystem_path_to_db_path(str(full_path))
                    
                    # Check if path already exists
                    if DBFileService.path_exists(session, db_path):
                        # Delete existing file/folder if it exists
                        if item.is_folder:
                            folder = session.query(Folder).filter(Folder.path == db_path).first()
                            if folder:
                                DBFileService.delete_folder(session, folder.id)
                                await file_system.delete_folder(db_path)
                        else:
                            file = session.query(File).filter(File.path == db_path).first()
                            if file:
                                DBFileService.delete_file(session, file.id)
                                await file_system.delete_file(db_path)
                    
                    # Now proceed with the upload
                    if item.is_folder:
                        os.makedirs(str(full_path), exist_ok=True)
                        DBFileService.create_folder_path(session, db_path)
                    else:
                        # Process and save file to disk
                        os.makedirs(str(full_path.parent), exist_ok=True)
                        file_data, _ = FileService._preprocess_base64_file(item.content)
                        with open(str(full_path), "wb") as f:
                            f.write(file_data)
                        
                        # Store file path for generation
                        file_paths.append(db_path)
                        
                        # Create folder structure and file in database
                        parent_path = str(Path(db_path).parent)
                        folder = None if parent_path in ['', '.'] else DBFileService.create_folder_path(session, parent_path)
                        
                        DBFileService.create_file(
                            session=session,
                            name=item.name,
                            path=db_path,
                            folder_id=folder.id if folder else None,
                            original_created_at=item.original_created_at,
                            original_modified_at=item.original_modified_at
                        )
                        
                        processed.append(f"Uploaded file: {item.path}")

                    yield {
                        "event": "message",
                        "data": FileUploadProgress(
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
                        "data": FileUploadProgress(
                            total=total,
                            current=idx,
                            processed_items=processed + skipped,
                            status="error",
                            error=f"Error processing {item.path}: {error_message}"
                        ).model_dump_json()
                    }
                    return

            # Trigger generate endpoint after successful upload only for files (not folders)
            if file_paths:
                background_tasks.add_task(trigger_generate, file_paths)
            
            # Final success message
            yield {
                "event": "message",
                "data": FileUploadProgress(
                    total=total,
                    current=total,
                    processed_items=processed + skipped,
                    status="completed"
                ).model_dump_json()
            }

        except Exception as e:
            yield {
                "event": "message",
                "data": FileUploadProgress(
                    total=total,
                    current=0,
                    processed_items=[],
                    status="error",
                    error=f"Upload failed: {str(e)}"
                ).model_dump_json()
            }
            
    return EventSourceResponse(process_uploads())


@r.get("/download/{file_id}")
async def download_file(file_id: int, session: Session = Depends(get_db_session)):
    result = await file_manager.download_file(session, file_id)
    return Response(
        content=result["content"],
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={result['filename']}",
            "X-Creation-Time": str(result["created_at"]),
            "X-Modified-Time": str(result["modified_at"])
        }
    )

@r.delete("/file/{file_id}")
async def delete_file(file_id: int, session: Session = Depends(get_db_session)):
    await file_manager.delete_file(session, file_id)
    return {"success": True}

@r.delete("/folder/{folder_id}")
async def delete_folder(folder_id: int, session: Session = Depends(get_db_session)):
    await file_manager.delete_folder(session, folder_id)
    return {"success": True}

@r.put("/file/{file_id}/rename")
async def rename_file(
    file_id: int, 
    new_name: str, 
    session: Session = Depends(get_db_session)
):
    await file_manager.rename_file(session, file_id, new_name)
    return {"success": True}

@r.get("/folder")
async def get_root_folder_contents(
    session: Session = Depends(get_db_session)
) -> List[FileNode]:
    """Get contents of root folder"""
    return DBFileService.get_folder_contents(session, None)

@r.get("/folder/{folder_id}")
async def get_folder_contents(
    folder_id: int,
    session: Session = Depends(get_db_session)
) -> List[FileNode]:
    """Get contents of a specific folder"""
    return DBFileService.get_folder_contents(session, folder_id)

@r.get("/download-folder/{folder_id}")
async def download_folder(folder_id: int, session: Session = Depends(get_db_session)):
    result = await file_manager.download_folder(session, folder_id)
    return Response(
        content=result["content"],
        media_type=result["mime_type"],
        headers={
            "Content-Disposition": f"attachment; filename={result['filename']}"
        }
    )
