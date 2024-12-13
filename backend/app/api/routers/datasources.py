from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from base64 import urlsafe_b64decode
from app.services import ServiceManager
from app.database.models import Datasource

datasources_router = APIRouter()

def get_datasource_service():
    return ServiceManager.get_instance().datasource_service

def get_db_session():
    return ServiceManager.get_instance().db_service.get_session()

class DatasourceCreate(BaseModel):
    name: str
    type: str
    settings: dict = None

class DatasourceResponse(BaseModel):
    id: int
    name: str
    type: str
    description: Optional[str] = None
    settings: dict = None

class DatasourceUpdate(BaseModel):
    description: Optional[str] = None

@datasources_router.get("", response_model=List[DatasourceResponse])
async def get_datasources(
    service = Depends(get_datasource_service),
    session: Session = Depends(get_db_session)
):
    datasources = service.get_all_datasources(session)
    # Convert to DatasourceResponse manually
    return [DatasourceResponse(
        id=ds.id,
        name=ds.name,
        type=ds.type,
        description=ds.description,
        settings=ds.settings,
    ) for ds in datasources]

@datasources_router.get("/{encoded_name}", response_model=DatasourceResponse)
async def get_datasource(
    encoded_name: str,
    service = Depends(get_datasource_service),
    session: Session = Depends(get_db_session)
):
    try:
        name = urlsafe_b64decode(encoded_name.encode()).decode()
        datasource = service.get_datasource(session, name)
        if not datasource:
            raise HTTPException(status_code=404, detail="Datasource not found")
        # Convert to DatasourceResponse manually
        return DatasourceResponse(
            id=datasource.id,
            name=datasource.name,
            type=datasource.type,
            description=datasource.description,
            settings=datasource.settings,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.post("", response_model=DatasourceResponse)
async def create_datasource(
    datasource: DatasourceCreate,
    service = Depends(get_datasource_service),
    session: Session = Depends(get_db_session)
):
    try:
        created = service.create_datasource(
            session,
            datasource.name,
            datasource.type,
            datasource.settings
        )
        # Convert to DatasourceResponse manually
        return DatasourceResponse(
            id=created.id,
            name=created.name,
            type=created.type,
            description=created.description,
            settings=created.settings,
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

@datasources_router.patch("/{encoded_name}")
async def update_datasource(
    encoded_name: str,
    update: DatasourceUpdate,
    service = Depends(get_datasource_service),
    session: Session = Depends(get_db_session)
):
    try:
        name = urlsafe_b64decode(encoded_name.encode()).decode()
        if update.description is not None:
            success = service.update_datasource_description(session, name, update.description)
            if not success:
                raise HTTPException(status_code=404, detail="Datasource not found")
        return {"message": "Datasource updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 