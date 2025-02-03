from typing import List
from sqlalchemy.orm import Session
import uuid
from datetime import datetime

from app.datasources.chats.database.models import Chat, Message
from app.datasources.chats.schemas import ChatResponse, MessageResponse, MessageCreate

import logging
logger = logging.getLogger("uvicorn")


def get_all_chats(chats_session: Session, include_messages: bool = False) -> List[ChatResponse]:
    try:
        all_chats_responses : List[ChatResponse] = []
        chats = chats_session.query(Chat).all()
        for chat in chats:
            chat_response = ChatResponse(
                uuid=chat.uuid,
                title=chat.title,
                created_at=chat.created_at,
                last_message_at=chat.last_message_at,
                last_opened_at=chat.last_opened_at,
                messages=[]
            )
            if include_messages:
                chat_response.messages = []
                chat_messages = chats_session.query(Message).filter(Message.chat_id == chat.id).all()
                for message in chat_messages:
                    chat_response.messages.append(
                        MessageResponse(
                            uuid=message.uuid,
                            role=message.role,
                            content=message.content,
                            annotations=message.annotations,
                            is_upvoted=message.is_upvoted,
                            created_at=message.created_at,
                        )
                    )
            all_chats_responses.append(chat_response)
        return all_chats_responses
    except Exception as e:
        logger.error(f"Error getting all chats: {str(e)}")
        raise

def get_chat(chats_session: Session, chat_uuid: str, include_messages: bool = False, create_if_not_found: bool = False, update_last_opened_at: bool = True) -> ChatResponse:
    try:
        chat = chats_session.query(Chat).filter(Chat.uuid == chat_uuid).first()
        if not chat and create_if_not_found:
            create_chat(chats_session, uuid=chat_uuid)
            # Reget it from the database
            chat = chats_session.query(Chat).filter(Chat.uuid == chat_uuid).first()
        if not chat:
            raise ValueError(f"Chat with id {chat_uuid} not found")
        
        # Update the last opened at time if the option is enabled
        if update_last_opened_at:
            chat.last_opened_at = datetime.now()
            chats_session.commit()

        chat_response = ChatResponse(
            uuid=chat.uuid,
            title=chat.title,
            created_at=chat.created_at,
            last_message_at=chat.last_message_at,
            last_opened_at=chat.last_opened_at,
            messages=[]
        )
        if include_messages:
            chat_messages = chats_session.query(Message).filter(Message.chat_id == chat.id).all()
            for message in chat_messages:
                chat_response.messages.append(
                    MessageResponse(
                        uuid=message.uuid,
                        role=message.role,
                        content=message.content,
                        annotations=message.annotations,
                        created_at=message.created_at,
                        is_upvoted=message.is_upvoted
                    )
                )
        return chat_response
    except Exception as e:
        logger.error(f"Error getting chat {chat_uuid}: {str(e)}")
        raise

def create_chat(chats_session: Session, uuid: str = None) -> ChatResponse:
    try:
        logger.debug(f"Creating chat with uuid: {uuid}")
        chat = Chat(
            uuid=uuid or str(uuid.uuid4()),
            title="New Chat"
        )
        chats_session.add(chat)
        chats_session.commit()
        chats_session.refresh(chat)
        return ChatResponse(
            uuid=chat.uuid,
            title=chat.title,
            created_at=chat.created_at,
            last_message_at=chat.last_message_at,
            last_opened_at=chat.last_opened_at,
            messages=[]
        )
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        raise

def add_message_to_chat(chats_session: Session, chat_uuid: str, message: MessageCreate) -> None:
    try:
        chat = chats_session.query(Chat).filter(Chat.uuid == chat_uuid).first()
        if not chat:
            raise ValueError(f"Chat with id {chat_uuid} not found")
        message_model = Message(
            uuid=message.uuid,
            role=message.role,
            content=message.content,
            annotations=message.annotations,
            created_at=message.created_at,
            chat_id=chat.id,
        )
        chats_session.add(message_model)
        # Update the last message at time
        chat.last_message_at = datetime.now()
        chats_session.commit()
        #chats_session.refresh(message_model)
    except Exception as e:
        logger.error(f"Error adding message to chat {chat_uuid}: {str(e)}")
        raise

def update_chat_title(chats_session: Session, chat_uuid: str, title: str) -> None:
    try:
        chat = chats_session.query(Chat).filter(Chat.uuid == chat_uuid).first()
        chat.title = title
        chats_session.commit()
    except Exception as e:
        logger.error(f"Error updating chat {chat_uuid} title: {str(e)}")
        raise

def delete_chat(chats_session: Session, chat_uuid: str) -> None:
    try:
        # Delete all messages in the chat
        chat = chats_session.query(Chat).filter(Chat.uuid == chat_uuid).first()
        if not chat:
            raise ValueError(f"Chat with id {chat_uuid} not found")
        # Delete all messages in the chat
        messages = chats_session.query(Message).filter(Message.chat_id == chat.id).all()
        for message in messages:
            chats_session.delete(message)
        # Delete the chat
        chats_session.delete(chat)
        chats_session.commit()
    except Exception as e:
        logger.error(f"Error deleting chat {chat_uuid}: {str(e)}")
        raise