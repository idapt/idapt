from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Annotated

from app.auth.dependencies import get_user_uuid_from_token
from app.datasources.chats.service import get_all_chats, get_chat, add_message_to_chat, create_chat, update_chat_title, delete_chat
from app.datasources.chats.database.session import get_datasources_chats_db_session
from app.datasources.chats.dependencies import validate_datasource_is_of_type_chats
from app.datasources.chats.schemas import ChatResponse, MessageResponse, MessageCreate

import logging
logger = logging.getLogger("uvicorn")

chats_router = r = APIRouter()

@r.get(
    "",
    response_model=List[ChatResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all chats"
)
async def get_all_chats_route(
    _: Annotated[str, Depends(validate_datasource_is_of_type_chats)],
    chats_session: Annotated[Session, Depends(get_datasources_chats_db_session)],
    include_messages: bool = False,
):
    try:
        logger.info(f"Getting all chats")
        return get_all_chats(chats_session, include_messages)
    except Exception as e:
        logger.error(f"Error getting all chats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@r.get(
    "/{chat_uuid}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a chat"
)
async def get_chat_route(
    chat_uuid: str,
    _: Annotated[str, Depends(validate_datasource_is_of_type_chats)],
    chats_session: Annotated[Session, Depends(get_datasources_chats_db_session)],
    include_messages: bool = False,
    create_if_not_found: bool = False,
    update_last_opened_at: bool = False,
) -> ChatResponse:
    try:
        logger.info(f"Getting chat {chat_uuid}")
        return get_chat(
            chats_session=chats_session,
            chat_uuid=chat_uuid,
            include_messages=include_messages,
            create_if_not_found=create_if_not_found,
            update_last_opened_at=update_last_opened_at
        )
    except Exception as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail="Chat not found")
        logger.error(f"Error getting chat {chat_uuid}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@r.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat"
)
async def create_chat_route(
    _: Annotated[str, Depends(validate_datasource_is_of_type_chats)],
    chats_session: Annotated[Session, Depends(get_datasources_chats_db_session)],
    chat_uuid: str = None,
):
    try:
        logger.info(f"Creating chat")
        return create_chat(chats_session, uuid=chat_uuid)
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@r.post(
    "/{chat_uuid}/messages",
    status_code=status.HTTP_201_CREATED,
    summary="Add a message to a chat"
)
async def add_message_to_chat_route(
    chat_uuid: str,
    message: MessageCreate,
    _: Annotated[str, Depends(validate_datasource_is_of_type_chats)],
    chats_session: Annotated[Session, Depends(get_datasources_chats_db_session)],
) -> None:
    try:
        logger.info(f"Adding message to chat {chat_uuid}")
        add_message_to_chat(chats_session, chat_uuid, message)
    except Exception as e:
        logger.error(f"Error adding message to chat {chat_uuid}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@r.put(
    "/{chat_uuid}",
    status_code=status.HTTP_200_OK,
    summary="Update a chat title"
)
async def update_chat_title_route(
    chat_uuid: str,
    title: str,
    _: Annotated[str, Depends(validate_datasource_is_of_type_chats)],
    chats_session: Annotated[Session, Depends(get_datasources_chats_db_session)],
) -> None:
    try:
        logger.info(f"Updating chat {chat_uuid} title to {title}")
        return update_chat_title(chats_session, chat_uuid, title)
    except Exception as e:
        logger.error(f"Error updating chat {chat_uuid} title: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@r.delete(
    "/{chat_uuid}",
    status_code=status.HTTP_200_OK,
    summary="Delete a chat"
)
async def delete_chat_route(
    chat_uuid: str,
    _: Annotated[str, Depends(validate_datasource_is_of_type_chats)],
    chats_session: Annotated[Session, Depends(get_datasources_chats_db_session)],
):
    try:
        logger.info(f"Deleting chat {chat_uuid}")
        delete_chat(chats_session, chat_uuid)
    except Exception as e:
        logger.error(f"Error deleting chat {chat_uuid}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
