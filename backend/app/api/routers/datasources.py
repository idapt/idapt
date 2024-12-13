from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from base64 import urlsafe_b64decode
from app.services import ServiceManager

datasources_router = APIRouter()

def get_datasource_service():
    return ServiceManager.get_instance().datasource_service

def get_db_session():
    return ServiceManager.get_instance().db_service.get_session()

class DatasourceCreate(BaseModel):
    name: str
    type: str
    settings: dict = None

@datasources_router.get("")
async def get_datasources(
    service = Depends(get_datasource_service),
    session: Session = Depends(get_db_session)
):
    return service.get_all_datasources(session)

@datasources_router.post("")
async def create_datasource(
    datasource: DatasourceCreate,
    service = Depends(get_datasource_service),
    session: Session = Depends(get_db_session)
):
    try:
        return service.create_datasource(
            session,
            datasource.name,
            datasource.type,
            datasource.settings
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.delete("/{encoded_name}")
async def delete_datasource(
    encoded_name: str,
    service = Depends(get_datasource_service),
    session: Session = Depends(get_db_session)
):
    try:
        name = urlsafe_b64decode(encoded_name.encode()).decode()
        success = service.delete_datasource(session, name)
        if not success:
            raise HTTPException(status_code=404, detail="Datasource not found")
        return {"message": "Datasource deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 