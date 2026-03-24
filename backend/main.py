import uuid
import json
import time
import sqlite3
import aiosqlite
from collections.abc import AsyncIterable
from contextlib import asynccontextmanager
from typing import Any, List, Optional, Union
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.sse import EventSourceResponse
from langchain.agents import create_agent
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from llm import get_llm
from pydantic import BaseModel

DB_NAME = "checkpoints.sqlite"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize the async checkpointer
    async with AsyncSqliteSaver.from_conn_string(DB_NAME) as saver:
        # Initialize the search tool
        tools = [TavilySearchResults(max_results=2)]
        
        # Create the agent with the checkpointer
        agent = create_agent(
            model=get_llm(),
            system_prompt="You are a helpful assistant.",
            tools=tools,
            checkpointer=saver,
        )
        
        app.state.agent = agent
        app.state.saver = saver
        yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

# Add CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MessagePart(BaseModel):
    type: str
    text: Optional[str] = None
    content: Optional[str] = None


class Message(BaseModel):
    id: Optional[str] = None
    role: str
    parts: list[MessagePart]


class ChatRequest(BaseModel):
    messages: list[Message]
    data: Optional[dict] = None
    checkpoint_id: Optional[str] = None


# Initialize the search tool. Make sure TAVILY_API_KEY is in your environment.


def format_agui_event(event_type: str, data: Any = None) -> str:
    """Formats an AG-UI event as an SSE message."""
    event_dict = {"type": event_type}
    if data is not None:
        event_dict["data"] = data
    return f"data: {json.dumps(event_dict)}\n\n"


async def stream_agui_events(agent, message_text: str, thread_id: str) -> AsyncIterable[str]:
    """Streams LangGraph events and transforms them into the AG-UI protocol."""
    config = {"configurable": {"thread_id": thread_id}}

    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message_text)]}, config, version="v2"
        ):
            kind = event["event"]
            name = event["name"]

            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content:
                    # Garantir que o conteúdo seja uma string para o TanStack AI agregar corretamente
                    text_content = content if isinstance(content, str) else "".join(
                        c.get("text", "") if isinstance(c, dict) else str(c) for c in (content if isinstance(content, list) else [content])
                    )
                    yield f"data: {json.dumps({'type': 'TEXT_MESSAGE_CONTENT', 'delta': text_content})}\n\n"

            elif kind == "on_tool_start":
                tool_call_id = event.get("run_id", "unknown_id")
                yield f"data: {json.dumps({'type': 'TOOL_CALL_START', 'toolCallId': tool_call_id, 'toolName': name})}\n\n"

            elif kind == "on_tool_end":
                tool_call_id = event.get("run_id", "unknown_id")
                input_data = event["data"].get("input", {})
                
                # O backend só precisa informar ao frontend que a ferramenta terminou.
                # O resultado bruto (milhares de caracteres de pesquisa) polui o SSE e
                # quebra o renderizador Markdown do frontend.
                yield f"data: {json.dumps({'type': 'TOOL_CALL_END', 'toolCallId': tool_call_id, 'toolName': name, 'input': input_data, 'result': 'Ferramenta concluida'})}\n\n"

        yield f"data: {json.dumps({'type': 'checkpoint', 'checkpoint_id': thread_id})}\n\n"
    except Exception as e:
        print(f"Streaming error: {e}")
        error_msg = str(e)
        if "503" in error_msg or "high demand" in error_msg.lower():
            error_msg = "O modelo está com alta demanda no momento. Por favor, tente novamente em instantes."
        yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
    
    yield "data: [DONE]\n\n"


def get_message_text(message: Message) -> str:
    """Extrai o texto combinado de todas as partes de uma mensagem."""
    return "".join(p.text or p.content or "" for p in message.parts if p.type == "text")


@app.get("/api/history")
async def get_history():
    """List conversations from checkpoint database."""
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute("SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id DESC") as cursor:
                threads = await cursor.fetchall()
                return [{"id": t[0], "title": f"Chat {t[0][:8]}"} for t in threads if t[0]]
    except Exception as e:
        print(f"Error reading history: {e}")
        return []


@app.get("/api/chat/{thread_id}")
async def get_chat_history(thread_id: str, request: Request):
    """Retrieve full message history for a thread."""
    agent = request.app.state.agent
    config = {"configurable": {"thread_id": thread_id}}
    state = await agent.aget_state(config)
    
    if not state.values:
        raise HTTPException(status_code=404, detail="Conversation not found")
        
    messages = state.values.get("messages", [])
    
    formatted = []
    for m in messages:
        if isinstance(m, HumanMessage):
            role = "user"
        elif isinstance(m, AIMessage):
            role = "assistant"
        elif isinstance(m, ToolMessage):
            role = "tool"
        else:
            role = "assistant"
            
        content_str = ""
        if isinstance(m.content, str):
            content_str = m.content
        elif isinstance(m.content, list):
            for c in m.content:
                if isinstance(c, str):
                    content_str += c
                elif isinstance(c, dict) and "text" in c:
                    content_str += c.get("text", "")
                    
        if role == "tool":
            content_str = "*Ferramenta executada com sucesso*"
            
        formatted.append({
            "id": getattr(m, "id", None),
            "role": role,
            "parts": [{"type": "text", "text": content_str}]
        })
    
    return {"messages": formatted}


@app.delete("/api/chat/{thread_id}")
async def delete_chat(thread_id: str):
    """Delete a conversation from the database."""
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("DELETE FROM checkpoints WHERE thread_id = ?", (thread_id,))
            await db.execute("DELETE FROM writes WHERE thread_id = ?", (thread_id,))
            await db.commit()
        return {"status": "success"}
    except Exception as e:
        print(f"Error deleting chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat")
async def chat(request: ChatRequest, fast_request: Request) -> EventSourceResponse:
    if not request.messages:
        raise HTTPException(status_code=400, detail="No messages provided")

    message_text = get_message_text(request.messages[-1])
    
    # Extract the UUID. TanStack AI nests options.body inside a 'data' property
    client_id = request.checkpoint_id
    if not client_id and request.data:
        client_id = request.data.get("checkpoint_id")
        
    thread_id = client_id or str(uuid.uuid4())
    agent = fast_request.app.state.agent

    return EventSourceResponse(stream_agui_events(agent, message_text, thread_id))
