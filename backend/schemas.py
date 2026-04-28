from pydantic import BaseModel


class MessagePart(BaseModel):
    type: str
    content: str | None = None


class Message(BaseModel):
    role: str
    parts: list[MessagePart]


class ChatRequest(BaseModel):
    messages: list[Message]
    checkpoint_id: str | None = None
