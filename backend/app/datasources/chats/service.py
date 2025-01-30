from typing import List
from sqlalchemy.orm import Session

from app.datasources.chats.schema import ChatResponse, MessageResponse, MessageRequest
from app.datasources.chats.database.models import Chat, Message

import logging
logger = logging.getLogger("uvicorn")


def get_all_chats(chats_session: Session, include_messages: bool = False) -> List[ChatResponse]:
    try:
        all_chats_responses : List[ChatResponse] = []
        chats = chats_session.query(Chat).all()
        for chat in chats:
            chat_response = ChatResponse(
                id=chat.id,
                title=chat.title,
                created_at=chat.created_at,
                last_opened_at=chat.last_opened_at,
                messages=None
            )
            if include_messages:
                chat_response.messages = []
                chat_messages = chats_session.query(Message).filter(Message.chat_id == chat.id).all()
                for message in chat_messages:
                    chat_response.messages.append(
                        MessageResponse(
                            id=message.id,
                            role=message.role,
                            content=message.content,
                            created_at=message.created_at,
                            is_upvoted=message.is_upvoted
                        )
                    )
            all_chats_responses.append(chat_response)
        return all_chats_responses
    except Exception as e:
        logger.error(f"Error getting all chats: {str(e)}")
        raise

def get_chat(chats_session: Session, chat_id: int, include_messages: bool = False) -> ChatResponse:
    try:
        chat = chats_session.query(Chat).filter(Chat.id == chat_id).first()
        chat_response = ChatResponse(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
            last_opened_at=chat.last_opened_at,
            messages=[]
        )
        if include_messages:
            chat_messages = chats_session.query(Message).filter(Message.chat_id == chat_id).all()
            for message in chat_messages:
                chat_response.messages.append(
                    MessageResponse(
                        id=message.id,
                        role=message.role,
                        content=message.content,
                        created_at=message.created_at,
                        is_upvoted=message.is_upvoted
                    )
                )
        return chat_response
    except Exception as e:
        logger.error(f"Error getting chat {chat_id}: {str(e)}")
        raise

def create_chat(chats_session: Session) -> ChatResponse:
    try:
        chat = Chat(
            title="New Chat"
        )
        chats_session.add(chat)
        chats_session.commit()
        chats_session.refresh(chat)
        return ChatResponse(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
            last_opened_at=chat.last_opened_at,
            messages=[]
        )
    except Exception as e:
        logger.error(f"Error creating chat: {str(e)}")
        raise

def add_message_to_chat(chats_session: Session, chat_id: int, message: MessageRequest) -> MessageResponse:
    try:
        message_model = Message(
            role=message.role,
            content=message.message_content,
            chat_id=chat_id,
        )
        chats_session.add(message_model)
        chats_session.commit()
        chats_session.refresh(message_model)
        return MessageResponse(
            id=message_model.id,
            role=message_model.role,
            content=message_model.content,
            created_at=message_model.created_at,
            is_upvoted=message_model.is_upvoted
        )
    except Exception as e:
        logger.error(f"Error adding message to chat {chat_id}: {str(e)}")
        raise

def update_chat_title(chats_session: Session, chat_id: int, title: str) -> None:
    try:
        chat = chats_session.query(Chat).filter(Chat.id == chat_id).first()
        chat.title = title
        chats_session.commit()
    except Exception as e:
        logger.error(f"Error updating chat {chat_id} title: {str(e)}")
        raise

def delete_chat(chats_session: Session, chat_id: int) -> None:
    try:
        # Delete all messages in the chat
        messages = chats_session.query(Message).filter(Message.chat_id == chat_id).all()
        for message in messages:
            chats_session.delete(message)
        # Delete the chat
        chat = chats_session.query(Chat).filter(Chat.id == chat_id).first()
        chats_session.delete(chat)
        chats_session.commit()
    except Exception as e:
        logger.error(f"Error deleting chat {chat_id}: {str(e)}")
        raise