from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.utils import get_user_id, get_file_manager_db_session
from app.datasources.schemas import DatasourceCreate, DatasourceResponse, DatasourceUpdate
from app.datasources.service import (
    get_datasource,
    create_datasource,
    delete_datasource,
    update_datasource,
    get_all_datasources
)
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

        return get_all_datasources(session)
        
    except Exception as e:
        logger.error(f"Error in get_datasources_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.get("/{identifier}", response_model=DatasourceResponse)
async def get_datasource_route(
    identifier: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session),
):
    try:
        logger.info(f"Getting datasource {identifier} for user {user_id}")
        return get_datasource(session, identifier)
    except Exception as e:
        logger.error(f"Error in get_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.post("")
async def create_datasource_route(
    datasource: DatasourceCreate,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session)
):
    try:
        logger.info(f"Creating datasource {datasource.name} for user {user_id}")

        create_datasource(
            session=session,
            user_id=user_id,
            datasource_create=datasource
        )
        return {"message": "Datasource created successfully"}
    except Exception as e:
        logger.error(f"Error in create_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.delete("/{identifier}")
async def delete_datasource_route(
    identifier: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session)
):
    try:
        logger.info(f"Deleting datasource {identifier} for user {user_id}")
        await delete_datasource(session, user_id, identifier)
        return {"message": "Datasource deleted successfully"}
    except Exception as e:
        logger.error(f"Error in delete_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.patch("/{identifier}")
async def update_datasource_route(
    identifier: str,
    update: DatasourceUpdate,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_file_manager_db_session)
):
    try:
        logger.info(f"Updating datasource {identifier} for user {user_id}")
        
        await update_datasource(
            session=session,
            user_id=user_id,
            identifier=identifier,
            datasource_update=update
        )
        return {"message": "Datasource updated successfully"}
    except Exception as e:
        logger.error(f"Error in update_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 