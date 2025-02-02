from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.api.utils import get_user_id
from app.datasources.database.utils import get_datasources_db_session
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

# Include the datasource modules
from app.datasources.file_manager.router import file_manager_router
from app.datasources.chats.router import chats_router

datasources_router.include_router(
    file_manager_router,
    prefix="/file-manager"
)
datasources_router.include_router(
    chats_router,
    prefix="/chats"
)


@datasources_router.get("", response_model=List[DatasourceResponse])
async def get_datasources_route(
    user_id: str = Depends(get_user_id),
    datasources_db_session: Session = Depends(get_datasources_db_session)
):
    try:
        logger.info(f"Getting all datasources for user {user_id}")

        return get_all_datasources(datasources_db_session)
        
    except Exception as e:
        logger.error(f"Error in get_datasources_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.get("/{identifier}", response_model=DatasourceResponse)
async def get_datasource_route(
    identifier: str,
    user_id: str = Depends(get_user_id),
    datasources_db_session: Session = Depends(get_datasources_db_session),
):
    try:
        logger.info(f"Getting datasource {identifier} for user {user_id}")
        return get_datasource(datasources_db_session, identifier)
    except Exception as e:
        logger.error(f"Error in get_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.post("")
async def create_datasource_route(
    datasource: DatasourceCreate,
    user_id: str = Depends(get_user_id),
    datasources_db_session: Session = Depends(get_datasources_db_session)
) -> None:
    try:
        logger.info(f"Creating datasource {datasource.name} for user {user_id}")

        create_datasource(
            datasources_db_session=datasources_db_session,
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
    datasources_db_session: Session = Depends(get_datasources_db_session)
) -> None:
    try:
        logger.info(f"Deleting datasource {identifier} for user {user_id}")
        await delete_datasource(datasources_db_session, user_id, identifier)
        return {"message": "Datasource deleted successfully"}
    except Exception as e:
        logger.error(f"Error in delete_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@datasources_router.patch("/{identifier}")
async def update_datasource_route(
    identifier: str,
    update: DatasourceUpdate,
    user_id: str = Depends(get_user_id),
    datasources_db_session: Session = Depends(get_datasources_db_session)
) -> None:
    try:
        logger.info(f"Updating datasource {identifier} for user {user_id}")
        
        await update_datasource(
            datasources_db_session=datasources_db_session,
            user_id=user_id,
            identifier=identifier,
            datasource_update=update
        )
        return {"message": "Datasource updated successfully"}
    except Exception as e:
        logger.error(f"Error in update_datasource_route: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e)) 