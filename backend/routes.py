import uuid
import aiosqlite
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from schemas import ChatRequest
from utils import _convert_msg_to_tanstack
from services import stream_chat
from config import DB_NAME

router = APIRouter(prefix="/api")

@router.post("/chat")
async def chat(request: ChatRequest, fast_request: Request):
    if not request.messages:
        raise HTTPException(status_code=400, detail="Sem mensagens")

    last_msg = request.messages[-1]
    message_text = "".join(p.content for p in last_msg.parts if p.type == "text")

    thread_id = request.checkpoint_id or str(uuid.uuid4())
    agent = fast_request.app.state.agent

    return StreamingResponse(
        stream_chat(agent, message_text, thread_id), media_type="text/event-stream"
    )

@router.get("/history")
async def get_history():
    """Lista IDs de conversas salvas."""
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(
                "SELECT DISTINCT thread_id FROM checkpoints"
            ) as cursor:
                threads = await cursor.fetchall()
                return [{"id": t[0]} for t in threads if t[0]]
    except Exception as e:
        print(f"Error fetching threads: {e}")
        return []

@router.get("/chat/{thread_id}")
async def get_chat_history(thread_id: str, fast_request: Request):
    """Retorna o histórico de mensagens de uma conversa."""
    agent = fast_request.app.state.agent
    try:
        state = await agent.aget_state({"configurable": {"thread_id": thread_id}})
        if not state or not hasattr(state, "values") or not state.values:
            return {"messages": []}

        messages = [
            _convert_msg_to_tanstack(msg) for msg in state.values.get("messages", [])
        ]
        return {"messages": messages}
    except Exception as e:
        print(f"Error fetching history: {e}")
        return {"messages": []}

@router.delete("/chat/{thread_id}")
async def delete_chat(thread_id: str):
    """Deleta o histórico de uma conversa."""
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute(
                "DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,)
            )
            await db.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            await db.commit()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
