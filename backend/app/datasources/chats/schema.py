from pydantic import BaseModel
from typing import List, Optional, Literal
from datetime import datetime

class MessageResponse(BaseModel):
    id: int
    role: Literal["user", "assistant", "system"]
    content: str
    created_at: datetime
    is_upvoted: Optional[bool]

class ChatResponse(BaseModel):
    id: int
    title: str
    created_at: datetime
    last_opened_at: Optional[datetime]
    messages: Optional[List[MessageResponse]]

class MessageRequest(BaseModel):
    role: Literal["user", "assistant", "system"]
    message_content: str
