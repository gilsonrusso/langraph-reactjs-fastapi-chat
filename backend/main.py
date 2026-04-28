from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from agents import (
    SUPERVISOR_PROMPT,
    initialize_global_agents,
    manage_email,
    schedule_event,
)
from config import DB_NAME, settings

# Módulos locais
from llm import get_llm
from logger import logger
from routes import router
from tools import get_weather


# --- Ciclo de Vida ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup da memória (SQLite)
    async with AsyncSqliteSaver.from_conn_string(DB_NAME) as saver:
        # 1. Inicializa os sub-agentes globais para as ferramentas
        initialize_global_agents()

        # 2. Inicializa o supervisor como agente principal da aplicação
        app.state.agent = create_agent(
            get_llm(),
            tools=[schedule_event, manage_email, get_weather],
            system_prompt=SUPERVISOR_PROMPT,
            checkpointer=saver,
        )
        yield


app = FastAPI(lifespan=lifespan)

# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui as rotas modularizadas
app.include_router(router)

if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Iniciando servidor em http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
