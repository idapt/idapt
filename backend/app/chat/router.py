import logging
from typing import Annotated
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.chat.schemas import (
    ChatData
)
from app.auth.dependencies import get_user_uuid_from_token
from app.chat.service import chat_streaming_response, chat_request_response
from app.settings.database.session import get_settings_db_session
from app.datasources.database.session import get_datasources_db_session
from app.datasources.chats.database.session import get_datasources_chats_db_session

chat_router = r = APIRouter()

logger = logging.getLogger("uvicorn")

@r.post("")
async def chat_streaming_route(
    request: Request,
    data: ChatData,
    background_tasks: BackgroundTasks,
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
    settings_db_session: Annotated[Session, Depends(get_settings_db_session)],
    datasources_db_session: Annotated[Session, Depends(get_datasources_db_session)],
    chat_db_session: Annotated[Session, Depends(get_datasources_chats_db_session)],
):
    """
    Streaming endpoint for chat requests.
    Returns a stream of messages from the agent.
    """
    try:
        logger.info(f"Chat streaming route called")
        return chat_streaming_response(
            data=data,
            settings_db_session=settings_db_session,
            datasources_db_session=datasources_db_session,
            request=request,
            background_tasks=background_tasks,
            user_uuid=user_uuid,
            chat_db_session=chat_db_session
        )
    except Exception as e:
        logger.error(f"Error in chat route: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in chat route: {str(e)}"
        ) from e

@r.post("/request", response_model=ChatData)
async def chat_request_route(
    data: ChatData,
    user_uuid: Annotated[str, Depends(get_user_uuid_from_token)],
    settings_db_session: Annotated[Session, Depends(get_settings_db_session)],
    datasources_db_session: Annotated[Session, Depends(get_datasources_db_session)],
    chat_db_session: Annotated[Session, Depends(get_datasources_chats_db_session)],
) -> ChatData:
    """
    Non-streaming endpoint for chat requests.
    Returns a single message from the agent.
    """
    try:
        logger.info(f"Chat request route called")
        return await chat_request_response(
            data=data,
            chat_db_session=chat_db_session,
            settings_db_session=settings_db_session,
            datasources_db_session=datasources_db_session,
            user_uuid=user_uuid
        )
    except Exception as e:
        logger.error(f"Error in chat request route: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in chat request route: {str(e)}"
        ) from e
