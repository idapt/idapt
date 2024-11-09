from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.connection import get_db_session
from app.services.data_generation import DataGenerationService
from app.engine.pipelines.zettlekasten_pipeline import ZettlekastenPipeline

data_generation_router = r = APIRouter()
data_generation_service = DataGenerationService()

@r.post("/generate/{file_id}")
async def generate_data(
    file_id: int,
    session: Session = Depends(get_db_session)
) -> Dict[str, Any]:
    """Generate Zettlekasten notes from a file"""
    try:
        data = await data_generation_service.generate_data_from_file(
            session=session,
            file_id=file_id,
            pipeline=ZettlekastenPipeline
        )
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 