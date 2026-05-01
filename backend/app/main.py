from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from langchain.agents import create_agent
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from .agents.graph import (
    SUPERVISOR_PROMPT,
    analyze_sales,
    consult_products,
    initialize_global_agents,
    manage_email,
    schedule_event,
)
from .core.config import DB_NAME, settings

# Módulos locais
from .core.llm import get_llm
from .core.logger import logger
from .api.chat import router
from .api.products import router as products_router
from .api.sales import router as sales_router
from .tools.tools import get_weather


# --- Ciclo de Vida ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup da memória (SQLite)
    async with AsyncSqliteSaver.from_conn_string(DB_NAME) as saver:
        # 1. Inicializa os sub-agentes globais para as ferramentas
        initialize_global_agents(checkpointer=saver)

        # 2. Inicializa o supervisor como agente principal da aplicação
        app.state.agent = create_agent(
            get_llm(),
            tools=[
                schedule_event,
                manage_email,
                get_weather,
                consult_products,
                analyze_sales,
            ],
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
app.include_router(products_router)
app.include_router(sales_router)

# --- Integração MCP (SSE) ---
# Cria o servidor MCP a partir do app FastAPI existente
mcp = FastMCP.from_fastapi(
    app,
    name="LangGraph Backend MCP",
)

# Monta o sub-app MCP na rota /mcp
# Isso expõe os endpoints SSE necessários para o protocolo MCP
app.mount("/mcp", mcp.http_app(transport="sse"))

if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Iniciando servidor em http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
