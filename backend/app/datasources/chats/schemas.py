from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime

from app.chat.schemas import Annotation
from llama_index.core.llms import MessageRole


class MessageCreate(BaseModel):
    """
    Used in the backend to create a message / add a message to a chat
    """
    uuid: str
    role: MessageRole
    content: str
    annotations: Optional[List[Annotation]]
    created_at: datetime

class MessageResponse(BaseModel):
    """
    Used in the backend to get a message
    """
    uuid: str
    role: Literal["system", "user", "assistant", "function", "tool", "chatbot", "model"]
    content: str
    annotations: Optional[List[Annotation]]
    is_upvoted: Optional[bool]
    created_at: datetime

class ChatResponse(BaseModel):
    """
    Used in the backend to get a chat
    """
    uuid: str
    title: str
    created_at: datetime
    last_opened_at: datetime

    messages: List[MessageResponse]
