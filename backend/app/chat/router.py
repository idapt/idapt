import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Depends
from sqlalchemy.orm import Session

from app.chat.schemas import (
    ChatData
)
from app.api.utils import get_user_id
from app.chat.service import chat_streaming_response, chat_request_response
from app.settings.database.session import get_settings_db_session
from app.datasources.database.session import get_datasources_db_session
from app.datasources.chats.database.session import get_datasources_chats_db_session

chat_router = r = APIRouter()

logger = logging.getLogger("uvicorn")


# streaming endpoint - delete if not needed
@r.post("")
async def chat_streaming_route(
    request: Request,
    data: ChatData,
    background_tasks: BackgroundTasks,
    datasource_identifier: str = "Chats",
    user_id: str = Depends(get_user_id),
    settings_db_session: Session = Depends(get_settings_db_session),
    datasources_db_session: Session = Depends(get_datasources_db_session),
    chat_db_session: Session = Depends(get_datasources_chats_db_session),
):
    """
    Streaming endpoint for chat requests.
    Returns a stream of messages from the agent.
    """
    try:
        logger.info(f"Chat streaming route called for user {user_id}")
        return chat_streaming_response(
            data=data,
            settings_db_session=settings_db_session,
            datasources_db_session=datasources_db_session,
            request=request,
            background_tasks=background_tasks,
            user_id=user_id,
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
    user_id: str = Depends(get_user_id),
    datasource_identifier: str = "Chats",
    settings_db_session: Session = Depends(get_settings_db_session),
    datasources_db_session: Session = Depends(get_datasources_db_session),
    chat_db_session: Session = Depends(get_datasources_chats_db_session),
) -> ChatData:
    """
    Non-streaming endpoint for chat requests.
    Returns a single message from the agent.
    """
    try:
        logger.info(f"Chat request route called for user {user_id}")
        return await chat_request_response(
            data=data,
            chat_db_session=chat_db_session,
            settings_db_session=settings_db_session,
            datasources_db_session=datasources_db_session,
            user_id=user_id
        )
    except Exception as e:
        logger.error(f"Error in chat request route: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in chat request route: {str(e)}"
        ) from e
