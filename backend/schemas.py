from typing import List, Optional
from pydantic import BaseModel

class MessagePart(BaseModel):
    type: str
    content: Optional[str] = None

class Message(BaseModel):
    role: str
    parts: List[MessagePart]

class ChatRequest(BaseModel):
    messages: List[Message]
    checkpoint_id: Optional[str] = None
