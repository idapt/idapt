from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.utils import get_user_id
from app.datasources.database.session import get_datasources_db_session
from app.settings.database.session import get_settings_db_session
from app.datasources.schemas import DatasourceCreate, DatasourceResponse, DatasourceUpdate
from app.datasources.service import (
    get_datasource,
    create_datasource,
    delete_datasource,
    update_datasource,
    get_all_datasources
)
from app.datasources.dependencies import validate_datasource_and_get_identifier
import logging


logger = logging.getLogger("uvicorn")

datasources_router = APIRouter()

# Include the datasource modules
from app.datasources.file_manager.router import file_manager_router
from app.datasources.chats.router import chats_router

datasources_router.include_router(
    file_manager_router,
    prefix="/{datasource_name}/file-manager"
)
datasources_router.include_router(
    chats_router,
    prefix="/{datasource_name}/chats"
)


@datasources_router.get("", response_model=List[DatasourceResponse])
async def get_all_datasources_route(
    datasources_db_session: Session = Depends(get_datasources_db_session),
):
    try:
        logger.info(f"Getting all datasources")

        return get_all_datasources(datasources_db_session)
        
    except Exception as e:
        logger.error(f"Error in get_datasources_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.get("/{datasource_name}", response_model=DatasourceResponse)
async def get_datasource_route(
    datasource_name: str,
    datasource_identifier = Depends(validate_datasource_and_get_identifier),
    datasources_db_session: Session = Depends(get_datasources_db_session),
):
    try:
        logger.info(f"Getting datasource {datasource_name}")
        return get_datasource(datasources_db_session, datasource_name)
    except Exception as e:
        logger.error(f"Error in get_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.post("/{datasource_name}")
async def create_datasource_route(
    datasource: DatasourceCreate,
    datasource_name: str,
    user_id: str = Depends(get_user_id),
    settings_db_session: Session = Depends(get_settings_db_session),
    datasource_identifier = Depends(validate_datasource_and_get_identifier),
    datasources_db_session: Session = Depends(get_datasources_db_session),
) -> None:
    try:
        logger.info(f"Creating datasource {datasource_name}")

        create_datasource(
            datasources_db_session=datasources_db_session,
            settings_db_session=settings_db_session,
            user_id=user_id,
            datasource_create=datasource,
            datasource_name=datasource_name
        )
        return {"message": "Datasource created successfully"}
    except Exception as e:
        logger.error(f"Error in create_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.delete("/{datasource_name}")
async def delete_datasource_route(
    datasource_name: str,
    user_id: str = Depends(get_user_id),
    datasource_identifier = Depends(validate_datasource_and_get_identifier),
    datasources_db_session: Session = Depends(get_datasources_db_session),
) -> None:
    try:
        logger.info(f"Deleting datasource {datasource_name} for user {user_id}")
        await delete_datasource(datasources_db_session, user_id, datasource_name)
        return {"message": "Datasource deleted successfully"}
    except Exception as e:
        logger.error(f"Error in delete_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.patch("/{datasource_name}")
async def update_datasource_route(
    datasource_name: str,
    update: DatasourceUpdate,
    user_id: str = Depends(get_user_id),
    settings_db_session: Session = Depends(get_settings_db_session),
    datasources_db_session: Session = Depends(get_datasources_db_session),
    datasource_identifier = Depends(validate_datasource_and_get_identifier),
) -> None:
    try:
        logger.info(f"Updating datasource {datasource_name} for user {user_id}")
        
        await update_datasource(
            datasources_db_session=datasources_db_session,
            settings_db_session=settings_db_session,
            user_id=user_id,
            identifier=datasource_name,
            datasource_update=update
        )
        return {"message": "Datasource updated successfully"}
    except Exception as e:
        logger.error(f"Error in update_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 