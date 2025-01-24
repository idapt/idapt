import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from base64 import urlsafe_b64decode

from app.api.utils import get_user_id, get_file_manager_db_session
from app.datasources.models import Datasource
from app.datasources.schemas import DatasourceCreate, DatasourceResponse, DatasourceUpdate
from app.datasources.service import get_datasource, create_datasource, delete_datasource, update_datasource
from app.settings.schemas import OllamaEmbedSettings, OpenAIEmbedSettings
import logging


logger = logging.getLogger("uvicorn")

datasources_router = APIRouter()

@datasources_router.get("", response_model=List[DatasourceResponse])
async def get_datasources_route(
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session)
):
    try:
        logger.info(f"Getting all datasources for user {user_id}")
        datasources = session.query(Datasource).all()
        return [DatasourceResponse(
            id=datasource.id,
            identifier=datasource.identifier,
            name=datasource.name,
            type=datasource.type,
            description=datasource.description,
            settings=datasource.settings,
            embedding_provider=datasource.embedding_provider,
            embedding_settings=json.loads(datasource.embedding_settings) if isinstance(datasource.embedding_settings, str) else datasource.embedding_settings,
        ) for datasource in datasources]
    except Exception as e:
        logger.error(f"Error in get_datasources_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.get("/{encoded_identifier}", response_model=DatasourceResponse)
async def get_datasource_route(
    encoded_identifier: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session)
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
            embedding_provider=datasource.embedding_provider,
            embedding_settings=datasource.embedding_settings,
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
    session: Session = Depends(get_file_manager_db_session)
):
    try:
        logger.info(f"Creating datasource {datasource.name} for user {user_id}")
        # Convert settings to a pydantic model
        match datasource.embedding_provider:
            case "ollama_embed":
                embedding_settings = OllamaEmbedSettings(**datasource.embedding_settings)
            case "openai_embed":
                embedding_settings = OpenAIEmbedSettings(**datasource.embedding_settings)
            case _:
                raise ValueError(f"Unsupported embedding provider: {datasource.embedding_provider}")
            
        created = create_datasource(
            session=session,
            user_id=user_id,
            name=datasource.name,
            type=datasource.type,
            description=datasource.description,
            settings_json={},
            embedding_provider=datasource.embedding_provider,
            embedding_settings_json=json.dumps(embedding_settings.model_dump())
        )
        
        # Parse the JSON string back to dict for the response
        embedding_settings_dict = json.loads(created.embedding_settings) if isinstance(created.embedding_settings, str) else created.embedding_settings
        
        return DatasourceResponse(
            id=created.id,
            identifier=created.identifier,
            name=created.name,
            type=created.type,
            description=created.description,
            settings=created.settings,
            embedding_provider=created.embedding_provider,
            embedding_settings=embedding_settings_dict,
        )
    except Exception as e:
        logger.error(f"Error in create_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.delete("/{encoded_identifier}")
async def delete_datasource_route(
    encoded_identifier: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session)
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
    session: Session = Depends(get_file_manager_db_session)
):
    try:
        logger.info(f"Updating datasource {encoded_identifier} for user {user_id}")
        identifier = urlsafe_b64decode(encoded_identifier.encode()).decode()
        
        success = await update_datasource(
            session=session,
            user_id=user_id,
            identifier=identifier,
            description=update.description,
            embedding_provider=update.embedding_provider,
            embedding_settings=update.embedding_settings
            )
        if not success:
            raise HTTPException(status_code=404, detail="Datasource not found")
        return {"message": "Datasource updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in update_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 