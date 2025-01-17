from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from base64 import urlsafe_b64decode

from app.api.dependencies import get_user_id
from app.services.database import get_db_session
from app.services.datasource import get_all_datasources, get_datasource, create_datasource, delete_datasource, update_datasource_description
import logging

logger = logging.getLogger("uvicorn")

datasources_router = APIRouter()

class DatasourceCreate(BaseModel):
    name: str
    type: str
    settings: dict = {}

class DatasourceResponse(BaseModel):
    id: int
    identifier: str
    name: str
    type: str
    description: Optional[str] = None
    settings: dict = {}

    class Config:
        from_attributes = True

class DatasourceUpdate(BaseModel):
    description: Optional[str] = None

@datasources_router.get("", response_model=List[DatasourceResponse])
async def get_datasources_route(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        logger.info(f"Getting all datasources for user {user_id}")
        datasources = get_all_datasources(session)
        # Convert to DatasourceResponse manually
        return [DatasourceResponse(
            id=datasource.id,
            identifier=datasource.identifier,
            name=datasource.name,
            type=datasource.type,
            description=datasource.description,
            settings=datasource.settings,
        ) for datasource in datasources]
    except Exception as e:
        logger.error(f"Error in get_datasources_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.get("/{encoded_identifier}", response_model=DatasourceResponse)
async def get_datasource_route(
    encoded_identifier: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        logger.info(f"Getting datasource {encoded_identifier} for user {user_id}")
        identifier = urlsafe_b64decode(encoded_identifier.encode()).decode()
        datasource = get_datasource(session, identifier)
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
        logger.error(f"Error in get_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.post("", response_model=DatasourceResponse)
async def create_datasource_route(
    datasource: DatasourceCreate,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        logger.info(f"Creating datasource {datasource.name} for user {user_id}")
        created = create_datasource(
            session,
            user_id,
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
        logger.error(f"Error in create_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.delete("/{encoded_identifier}")
async def delete_datasource_route(
    encoded_identifier: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        logger.info(f"Deleting datasource {encoded_identifier} for user {user_id}")
        identifier = urlsafe_b64decode(encoded_identifier.encode()).decode()
        success = await delete_datasource(session, user_id, identifier)
        if not success:
            raise HTTPException(status_code=404, detail="Datasource not found")
        return {"message": "Datasource deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in delete_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.patch("/{encoded_identifier}")
async def update_datasource_route(
    encoded_identifier: str,
    update: DatasourceUpdate,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session)
):
    try:
        logger.info(f"Updating datasource {encoded_identifier} for user {user_id}")
        identifier = urlsafe_b64decode(encoded_identifier.encode()).decode()
        if update.description is not None:
            success = update_datasource_description(session, identifier, update.description)
            if not success:
                raise HTTPException(status_code=404, detail="Datasource not found")
        return {"message": "Datasource updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 