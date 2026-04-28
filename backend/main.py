import uuid
import json
import time
import aiosqlite
from collections.abc import AsyncIterable
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langchain_core.messages import HumanMessage
from langchain.tools import tool
from langchain.agents.middleware import HumanInTheLoopMiddleware 
from langgraph.checkpoint.memory import InMemorySaver 

from langchain.agents import create_agent

from langfuse.langchain import CallbackHandler

import os
from dotenv import load_dotenv

# Carrega o .env antes de qualquer outra coisa
load_dotenv()

# O Langfuse agora lê as chaves diretamente do arquivo .env
os.environ["LANGFUSE_HOST"] = "http://localhost:3031"

langfuse_handler = CallbackHandler()

from llm import get_llm

# --- Configuração ---
DB_NAME = "checkpoints.sqlite"


# --- Ferramentas (Exemplo Simples) ---
@tool
def get_weather(location: str) -> str:
    """Retorna a previsão do tempo para uma localização."""
    return f"O tempo em {location} está ensolarado com 25°C."

@tool
def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    attendees: list[str],
    location: str = ""
) -> str:
    """Create a calendar event. Requires exact ISO datetime format."""
    # Stub: In practice, this would call Google Calendar API, Outook, etc...
    return f"Event created: {title} from {start_time} to {end_time} with {len(attendees)} attendees."

@tool
def send_email(
    to: list[str], #email addresses
    subject: str,
    boddy: str,
    cc: list[str] = []
) -> str:
    """Send an email via email API. Requires properly formated addresses."""
    # Stub: In practice, this would call SendGrid, Gmail API, etc.

@tool
def get_available_time_slots(
    attendees: list[str],
    date: str,  # ISO format: "2024-01-15"
    duration_minutes: int
) -> list[str]:
    """Check calendar availability for given attendees on a specific date."""
    # Stub: In practice, this would query calendar APIs
    return ["09:00", "14:00", "16:00"]  


# --- Agentes e Ferramentas ---

# 1. Sub-agentes (Especialistas)
CALENDAR_AGENT_PROMPT = (
    "You are a calendar scheduling assistant. "
    "Parse natural language scheduling requests (e.g., 'next Tuesday at 2pm') "
    "into proper ISO datetime formats. "
    "Use get_available_time_slots to check availability when needed. "
    "If there is no suitable time slot, stop and confirm unavailability in your response. "
    "Use create_calendar_event to schedule events. "
    "Always confirm what was scheduled in your final response."
)

EMAIL_AGENT_PROMPT = (
    "You are an email assistant. "
    "Compose professional emails based on natural language requests. "
    "Extract recipient information and craft appropriate subject lines and body text. "
    "Use send_email to send the message. "
    "Always confirm what was sent in your final response."
)

# Nota: Criamos os agentes aqui, mas eles serão usados dentro das ferramentas.
def create_sub_agents():
    llm = get_llm()
    
    calendar_agent = create_agent(
        llm,
        tools=[create_calendar_event, get_available_time_slots],
        system_prompt=CALENDAR_AGENT_PROMPT,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={"create_calendar_event": True},
                description_prefix="Calendar event pending approval",
            ),
        ],
    )

    email_agent = create_agent(
        llm,
        tools=[send_email],
        system_prompt=EMAIL_AGENT_PROMPT,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={"send_email": True},
                description_prefix="Outbound email pending approval",
            ),
        ],
    )
    
    return calendar_agent, email_agent

# Precisamos instanciar os sub-agentes para que as ferramentas possam referenciá-los.
# Para evitar problemas de escopo no lifespan, vamos definir as ferramentas aqui
# e capturar os agentes via closure ou definir depois.
_calendar_agent = None
_email_agent = None

@tool
async def schedule_event(request: str) -> str:
    """Schedule calendar events using natural language.
    Use this when the user wants to create, modify, or check calendar appointments.
    """
    if _calendar_agent is None:
        return "Erro: Agente de calendário não inicializado."
    result = await _calendar_agent.ainvoke({"messages": [HumanMessage(content=request)]})
    return result["messages"][-1].content

@tool
async def manage_email(request: str) -> str:
    """Send emails using natural language.
    Use this when the user wants to send notifications, reminders, or any email communication.
    """
    if _email_agent is None:
        return "Erro: Agente de e-mail não inicializado."
    result = await _email_agent.ainvoke({"messages": [HumanMessage(content=request)]})
    return result["messages"][-1].content

SUPERVISOR_PROMPT = (
    "You are a helpful personal assistant. "
    "You can schedule calendar events and send emails. "
    "Break down user requests into appropriate tool calls and coordinate the results. "
    "When a request involves multiple actions, use multiple tools in sequence."
)

# --- Modelos Pydantic (Minimalistas) ---
class MessagePart(BaseModel):
    type: str
    content: Optional[str] = None


class Message(BaseModel):
    role: str
    parts: List[MessagePart]


class ChatRequest(BaseModel):
    messages: List[Message]
    checkpoint_id: Optional[str] = None


# --- Lógica de Streaming ---
def _extract_stream_text(content) -> str:
    """Extrai texto de um chunk, lidando com formatos de lista ou string."""
    if not content:
        return ""
    if isinstance(content, list):
        return "".join(
            c.get("text", "") if isinstance(c, dict) else str(c) for c in content
        )
    return str(content)


def _build_sse_event(type_: str, **kwargs) -> str:
    """Constrói um ServerSentEvent com tipo, timestamp e dados adicionais."""
    data = {"type": type_, "timestamp": int(time.time() * 1000)}
    data.update(kwargs)
    return f"data: {json.dumps(data)}\n\n"


async def stream_chat(agent, message_text: str, thread_id: str) -> AsyncIterable[str]:
    config = {"configurable": {"thread_id": thread_id}, "callbacks": [langfuse_handler]}
    run_id = str(uuid.uuid4())
    msg_id = str(uuid.uuid4())

    yield _build_sse_event("RUN_STARTED", runId=run_id)
    yield _build_sse_event("TEXT_MESSAGE_START", messageId=msg_id, role="assistant")

    try:
        async for event in agent.astream_events(
            {"messages": [HumanMessage(content=message_text)]}, config, version="v2"
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                text = _extract_stream_text(event["data"]["chunk"].content)
                if text:
                    yield _build_sse_event(
                        "TEXT_MESSAGE_CONTENT", messageId=msg_id, delta=text
                    )

            elif kind == "on_tool_start":
                yield _build_sse_event(
                    "TOOL_CALL_START",
                    toolCallId=event.get("run_id", str(uuid.uuid4())),
                    toolName=event.get("name", "tool"),
                    parentMessageId=msg_id,
                )

            elif kind == "on_tool_end":
                result_data = event.get("data", {}).get("output")
                result_str = (
                    str(result_data.content)
                    if hasattr(result_data, "content")
                    else str(result_data)
                )

                yield _build_sse_event(
                    "TOOL_CALL_END",
                    toolCallId=event.get("run_id", str(uuid.uuid4())),
                    toolName=event.get("name", "tool"),
                    result=result_str,
                )

    except Exception as e:
        yield _build_sse_event("RUN_ERROR", runId=run_id, error={"message": str(e)})

    yield _build_sse_event("TEXT_MESSAGE_END", messageId=msg_id)
    yield _build_sse_event("RUN_FINISHED", runId=run_id, finishReason="stop")


# --- Ciclo de Vida e Agente ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global _calendar_agent, _email_agent
    
    # Setup da memória (SQLite)
    async with AsyncSqliteSaver.from_conn_string(DB_NAME) as saver:
        # 1. Inicializa os sub-agentes
        _calendar_agent, _email_agent = create_sub_agents()
        
        # 2. Inicializa o supervisor com o checkpointer persistente
        app.state.agent = create_agent(
            get_llm(),
            tools=[schedule_event, manage_email, get_weather], # Incluímos o clima no supervisor também
            system_prompt=SUPERVISOR_PROMPT,
            checkpointer=saver,
        )
        yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Endpoints ---


@app.post("/api/chat")
async def chat(request: ChatRequest, fast_request: Request):
    if not request.messages:
        raise HTTPException(status_code=400, detail="Sem mensagens")

    # Pega o texto da última mensagem do usuário
    last_msg = request.messages[-1]
    message_text = "".join(p.content for p in last_msg.parts if p.type == "text")

    # ID da conversa para memória
    thread_id = request.checkpoint_id or str(uuid.uuid4())
    agent = fast_request.app.state.agent

    return StreamingResponse(
        stream_chat(agent, message_text, thread_id), media_type="text/event-stream"
    )


@app.get("/api/history")
async def get_history():
    """Lista IDs de conversas salvas."""
    try:
        async with aiosqlite.connect(DB_NAME) as db:
            async with db.execute(
                "SELECT DISTINCT thread_id FROM checkpoints"
            ) as cursor:
                threads = await cursor.fetchall()
                return [{"id": t[0]} for t in threads if t[0]]
    except:
        return []


def _extract_msg_text_parts(content) -> list:
    """Extrai as partes de texto de um conteúdo de mensagem do LangChain."""
    if isinstance(content, str) and content:
        return [{"type": "text", "content": content}]

    parts = []
    if isinstance(content, list):
        for c in content:
            if isinstance(c, str):
                parts.append({"type": "text", "content": c})
            elif isinstance(c, dict) and "text" in c:
                parts.append({"type": "text", "content": c["text"]})
    return parts


def _convert_msg_to_tanstack(msg) -> dict:
    """Converte uma mensagem do LangChain para o formato esperado pelo TanStack UI."""
    role_map = {"human": "user", "ai": "assistant", "tool": "tool"}
    role = role_map.get(msg.type, "assistant")

    parts = _extract_msg_text_parts(msg.content)

    if hasattr(msg, "tool_calls") and msg.tool_calls:
        for tc in msg.tool_calls:
            parts.append(
                {
                    "type": "tool-call",
                    "name": tc.get("name"),
                    "toolCallId": tc.get("id"),
                    "args": tc.get("args"),
                }
            )

    if msg.type == "tool":
        parts.append(
            {
                "type": "tool-result",
                "name": getattr(msg, "name", ""),
                "toolCallId": getattr(msg, "tool_call_id", ""),
                "result": msg.content,
            }
        )

    return {"id": getattr(msg, "id", str(uuid.uuid4())), "role": role, "parts": parts}


@app.get("/api/chat/{thread_id}")
async def get_chat_history(thread_id: str, fast_request: Request):
    """Retorna o histórico de mensagens de uma conversa a partir do LangGraph."""
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


@app.delete("/api/chat/{thread_id}")
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
