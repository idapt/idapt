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
    with ServiceManager.get_instance().db_service.get_session() as session:
        yield session

class DatasourceCreate(BaseModel):
    name: str
    type: str
    settings: dict = None

class DatasourceResponse(BaseModel):
    id: int
    identifier: str
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
        id=datasource.id,
        identifier=datasource.identifier,
        name=datasource.name,
        type=datasource.type,
        description=datasource.description,
        settings=datasource.settings,
    ) for datasource in datasources]

@datasources_router.get("/{encoded_identifier}", response_model=DatasourceResponse)
async def get_datasource(
    encoded_identifier: str,
    service = Depends(get_datasource_service),
    session: Session = Depends(get_db_session)
):
    try:
        identifier = urlsafe_b64decode(encoded_identifier.encode()).decode()
        datasource = service.get_datasource(session, identifier)
        if not datasource:
            raise HTTPException(status_code=404, detail="Datasource not found")
        # Convert to DatasourceResponse manually
        return DatasourceResponse(
            id=datasource.id,
            identifier=datasource.identifier,
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
            identifier=created.identifier,
            name=created.name,
            type=created.type,
            description=created.description,
            settings=created.settings,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.delete("/{encoded_identifier}")
async def delete_datasource(
    encoded_identifier: str,
    service = Depends(get_datasource_service),
    session: Session = Depends(get_db_session)
):
    try:
        identifier = urlsafe_b64decode(encoded_identifier.encode()).decode()
        success = service.delete_datasource(session, identifier)
        if not success:
            raise HTTPException(status_code=404, detail="Datasource not found")
        return {"message": "Datasource deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.patch("/{encoded_identifier}")
async def update_datasource(
    encoded_identifier: str,
    update: DatasourceUpdate,
    service = Depends(get_datasource_service),
    session: Session = Depends(get_db_session)
):
    try:
        identifier = urlsafe_b64decode(encoded_identifier.encode()).decode()
        if update.description is not None:
            success = service.update_datasource_description(session, identifier, update.description)
            if not success:
                raise HTTPException(status_code=404, detail="Datasource not found")
        return {"message": "Datasource updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 