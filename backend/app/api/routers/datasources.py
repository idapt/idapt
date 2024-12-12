from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db_session
from app.services.datasource import DatasourceService
from pydantic import BaseModel

datasources_router = APIRouter()
datasource_service = DatasourceService()

class DatasourceCreate(BaseModel):
    name: str
    type: str
    settings: dict = None

@datasources_router.get("")
async def get_datasources(session: Session = Depends(get_db_session)):
    return datasource_service.get_all_datasources(session)

@datasources_router.post("")
async def create_datasource(
    datasource: DatasourceCreate,
    session: Session = Depends(get_db_session)
):
    try:
        return datasource_service.create_datasource(
            session,
            datasource.name,
            datasource.type,
            datasource.settings
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 