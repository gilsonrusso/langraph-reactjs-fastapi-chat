from pydantic import BaseModel


class MessagePart(BaseModel):
    type: str
    content: str | None = None


class Message(BaseModel):
    role: str
    parts: list[MessagePart]


class Decision(BaseModel):
    type: str  # "approve", "reject", "edit"
    edited_action: dict | None = None
    message: str | None = None


class ChatRequest(BaseModel):
    messages: list[Message]
    checkpoint_id: str | None = None
    decision: Decision | None = None
