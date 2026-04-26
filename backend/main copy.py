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
from langgraph.prebuilt import create_react_agent
from langchain_tavily import TavilySearch
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from llm import get_llm
from pydantic import BaseModel

DB_NAME = "checkpoints.sqlite"

from langchain.tools import tool

@tool
def get_weather(location: str) -> str:
    """Retorna a previsão do tempo atual para uma localização específica."""
    # Mock data para o exemplo de Generative UI
    import json
    return json.dumps({
        "temperature": 25,
        "conditions": "Ensolarado com algumas nuvens",
        "humidity": 60,
        "wind_speed": 15,
        "feels_like": 27
    })

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Garante a preparação assíncrona inicial da aplicação:
    1. Define o 'Saver' do LangGraph responsável pelo banco SQLite (checkpoints).
    2. Instancia o agente principal e as ferramentas operacionais (Ex: Tavily).
    3. Anexa o agente e o checkpointer livremente na aplicação via 'app.state'.
    """
    # Startup: Initialize the async checkpointer
    async with AsyncSqliteSaver.from_conn_string(DB_NAME) as saver:
        # Initialize the tools
        tools = [TavilySearch(max_results=2), get_weather]
        
        # Create the agent using official LangGraph prebuilt factory
        agent = create_react_agent(
            model=get_llm(),
            tools=tools,
            prompt="You are a helpful assistant.",
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


# --- SSE Protocol Schemas (Strong Typing) ---
from typing import Literal

class SSEEvent(BaseModel):
    type: str

class ContentEvent(BaseModel):
    type: Literal["content"] = "content"
    delta: str

class ToolCallEvent(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    id: str
    name: str
    args: Optional[dict] = None

class ToolResultEvent(BaseModel):
    type: Literal["tool_result"] = "tool_result"
    tool_call_id: str
    result: Any
    error: Optional[str] = None

class DoneEvent(BaseModel):
    type: Literal["done"] = "done"

class ErrorEvent(BaseModel):
    type: Literal["error"] = "error"
    message: str

class CheckpointEvent(BaseModel):
    type: Literal["checkpoint"] = "checkpoint"
    checkpoint_id: str

class SSEAdapter:
    """Encapsula a criação de mensagens SSE para garantir consistência no protocolo."""
    
    @staticmethod
    def json_event(event: Union[ContentEvent, ToolCallEvent, ToolResultEvent, DoneEvent, ErrorEvent, CheckpointEvent]) -> str:
        # Usamos model_dump para garantir que o Pydantic valide e serialize corretamente
        data = event.model_dump() if hasattr(event, "model_dump") else event
        return f"data: {json.dumps(data)}\n\n"
    
    @staticmethod
    def heartbeat() -> str:
        return ": heartbeat\n\n"

    @staticmethod
    def retry(ms: int = 3000) -> str:
        return f"retry: {ms}\n\n"

def format_agui_event(event_type: str, data: Any = None) -> str:
    """Formats an AG-UI event as an SSE message."""
    # Mantido para compatibilidade, mas SSEAdapter é preferido
    event_dict = {"type": event_type}
    if data is not None:
        event_dict["data"] = data
    return f"data: {json.dumps(event_dict)}\n\n"


async def stream_agui_events(agent, message_text: str, thread_id: str) -> AsyncIterable[str]:
    """
    Consome o iterador de streaming de grafos (astream_events) do Agente LangChain base.
    Traduz os fluxos de chunk disparados da IA em tempo real para o protocolo TanStack AI utilizando schemas fortes.
    """
    import asyncio
    config = {"configurable": {"thread_id": thread_id}}
    
    yield SSEAdapter.retry(3000)
    yield SSEAdapter.heartbeat()

    try:
        events = agent.astream_events(
            {"messages": [HumanMessage(content=message_text)]}, config, version="v2"
        )
        events_aiter = events.__aiter__()
        
        done = False
        while not done:
            try:
                event = await asyncio.wait_for(events_aiter.__anext__(), timeout=15.0)
                print(f"DEBUG: Received event: {event['event']} - {event['name']}")
                
                kind = event["event"]
                name = event["name"]

                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        text_content = content if isinstance(content, str) else "".join(
                            c.get("text", "") if isinstance(c, dict) else str(c) 
                            for c in (content if isinstance(content, list) else [content])
                        )
                        yield SSEAdapter.json_event(ContentEvent(delta=text_content))

                elif kind == "on_tool_start":
                    tool_call_id = event.get("run_id", "unknown_id")
                    input_data = event["data"].get("input", {})
                    yield SSEAdapter.json_event(ToolCallEvent(id=tool_call_id, name=name, args=input_data))

                elif kind == "on_tool_end":
                    tool_call_id = event.get("run_id", "unknown_id")
                    output = event["data"].get("output")
                    output_data = {}
                    error_msg = None
                    
                    if hasattr(output, "content"):
                        raw_content = output.content
                        if isinstance(raw_content, str):
                            try:
                                output_data = json.loads(raw_content)
                            except Exception:
                                # Fallback robusto para outputs malformados
                                output_data = {"raw": raw_content}
                                error_msg = "invalid_json_format"
                        else:
                            output_data = raw_content
                    else:
                        output_data = output
                        
                    yield SSEAdapter.json_event(ToolResultEvent(
                        tool_call_id=tool_call_id, 
                        result=output_data,
                        error=error_msg
                    ))

            except asyncio.TimeoutError:
                yield SSEAdapter.heartbeat()
            except StopAsyncIteration:
                done = True

        yield SSEAdapter.json_event(CheckpointEvent(checkpoint_id=thread_id))
    except Exception as e:
        print(f"Streaming error: {e}")
        error_msg = str(e)
        if "503" in error_msg or "high demand" in error_msg.lower():
            error_msg = "O modelo está com alta demanda no momento. Por favor, tente novamente em instantes."
        yield SSEAdapter.json_event(ErrorEvent(message=error_msg))
    
    # TanStack AI padrão para encerramento
    yield SSEAdapter.json_event(DoneEvent())


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
    """
    Recupera um histórico preexistente de conversa mapeado num sub-grafo ativo do LangChain.
    Faz a tradução das mensagens estritas em objetos base e unifica componentes de multimidia
    no schema nativo do ReactJS impedindo que ferramentas complexas quebrem o processador.
    """
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
    """
    Endpoint contínuo e núcleo central do envio de prompts. 
    1. Determina ou cria um respectivo Thread (ID/UUID da conversa).
    2. Extrai a String da última mensagem postada.
    3. Constrói de imediato a ponte infinita entre Client/Backend repassando para o Server-Sent Event provider.
    """
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
