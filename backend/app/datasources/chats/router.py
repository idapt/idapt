from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.datasources.chats.service import get_all_chats, get_chat, add_message_to_chat, create_chat, update_chat_title, delete_chat
from app.datasources.chats.utils import get_chats_db_session
from app.api.utils import get_user_id
from app.datasources.chats.schema import ChatResponse, MessageResponse, MessageRequest
from typing import List

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
    include_messages: bool = False,
    user_id: str = Depends(get_user_id),
    chats_session: Session = Depends(get_chats_db_session),
):
    try:
        logger.info(f"Getting all chats for user {user_id}")
        return get_all_chats(chats_session, include_messages)
    except Exception as e:
        logger.error(f"Error getting all chats: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@r.get(
    "/{chat_id}",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a chat"
)
async def get_chat_route(
    chat_id: int,
    include_messages: bool = False,
    user_id: str = Depends(get_user_id),
    chats_session: Session = Depends(get_chats_db_session),
):
    try:
        logger.info(f"Getting chat {chat_id} for user {user_id}")
        return get_chat(chats_session, chat_id, include_messages)
    except Exception as e:
        logger.error(f"Error getting chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@r.post(
    "",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat"
)
async def create_chat_route(
    user_id: str = Depends(get_user_id),
    chats_session: Session = Depends(get_chats_db_session),
):
    try:
        return create_chat(chats_session)
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@r.post(
    "/{chat_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a message to a chat"
)
async def add_message_to_chat_route(
    chat_id: int,
    message: MessageRequest,
    user_id: str = Depends(get_user_id),
    chats_session: Session = Depends(get_chats_db_session),
):
    try:
        return add_message_to_chat(chats_session, chat_id, message)
    except Exception as e:
        logger.error(f"Error adding message to chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
    
@r.put(
    "/{chat_id}",
    status_code=status.HTTP_200_OK,
    summary="Update a chat title"
)
async def update_chat_title_route(
    chat_id: int,
    title: str,
    user_id: str = Depends(get_user_id),
    chats_session: Session = Depends(get_chats_db_session),
) -> None:
    try:
        return update_chat_title(chats_session, chat_id, title)
    except Exception as e:
        logger.error(f"Error updating chat {chat_id} title: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@r.delete(
    "/{chat_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a chat"
)
async def delete_chat_route(
    chat_id: int,
    user_id: str = Depends(get_user_id),
    chats_session: Session = Depends(get_chats_db_session),
):
    try:
        delete_chat(chats_session, chat_id)
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
