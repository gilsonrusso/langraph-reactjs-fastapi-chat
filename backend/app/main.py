from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import FastMCP
from fastmcp.server.providers.openapi import RouteMap, MCPType
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from .agents.graph import build_main_graph
from .core.config import DB_NAME, settings

# Módulos locais
from .core.logger import logger
from .api.chat import router
from .api.products import router as products_router
from .api.sales import router as sales_router


# --- Ciclo de Vida ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup da memória (SQLite)
    async with AsyncSqliteSaver.from_conn_string(DB_NAME) as saver:
        # Inicializa o supervisor como um StateGraph compilado dinamicamente
        logger.info("Construindo Network of Agents...")
        app.state.agent = await build_main_graph(checkpointer=saver, mcp_server=mcp)
        logger.info("Grafo construído com sucesso.")
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
# Definimos regras de segurança para filtrar quais rotas da API 
# serão expostas como ferramentas para o agente.
route_maps = [
    # Somente permite ferramentas de consulta (GET) para as tags específicas
    RouteMap(
        methods=["GET"], 
        tags={"products"}, 
        mcp_type=MCPType.TOOL,
        mcp_tags={"read-only", "catalog"}
    ),
    RouteMap(
        methods=["GET"], 
        tags={"sales"}, 
        mcp_type=MCPType.TOOL,
        mcp_tags={"read-only", "analytics"}
    ),
    # EXCLUI qualquer outra rota (como /chat ou POST/PUT/DELETE)
    RouteMap(mcp_type=MCPType.EXCLUDE)
]

# Cria o servidor MCP a partir do app FastAPI existente com as restrições
mcp = FastMCP.from_fastapi(
    app,
    name="LangGraph Backend MCP",
    route_maps=route_maps
)

# Monta o sub-app MCP na rota /mcp
# Isso expõe os endpoints SSE necessários para o protocolo MCP
app.mount("/mcp", mcp.http_app(transport="sse"))

if __name__ == "__main__":
    import uvicorn

    logger.info(f"🚀 Iniciando servidor em http://{settings.HOST}:{settings.PORT}")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
