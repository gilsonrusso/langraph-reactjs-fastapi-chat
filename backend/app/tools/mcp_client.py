from typing import List, Optional, Any
import logging
from fastmcp import Client
from langchain_core.tools import StructuredTool

logger = logging.getLogger(__name__)

class MCPToolDiscovery:
    """
    Utilitário para descobrir e converter ferramentas de um servidor MCP SSE
    em ferramentas compatíveis com LangChain/LangGraph.
    Utiliza o fastmcp.Client para uma interface mais estável e simplificada.
    """

    def __init__(self, url: str = "http://localhost:8000/mcp/sse"):
        # O Client do FastMCP infere o transporte automaticamente (SSE para HTTP URLs)
        self.url = url

    async def get_tools(self, tag: Optional[str] = None) -> List[StructuredTool]:
        """
        Conecta ao servidor MCP, lista as ferramentas e as filtra por tag.
        Retorna uma lista de StructuredTool prontas para uso em agentes LangChain.
        """
        lc_tools = []
        try:
            client = Client(self.url)
            async with client:
                mcp_tools = await client.list_tools()
                
                for mcp_tool in mcp_tools:
                    # Filtro por tag (usando o padrão FastMCP extraído na inspeção)
                    if tag:
                        tool_tags = []
                        if hasattr(mcp_tool, "meta") and isinstance(mcp_tool.meta, dict):
                            tool_tags = mcp_tool.meta.get("fastmcp", {}).get("tags", [])
                        
                        if tag not in tool_tags:
                            continue
                    
                    logger.info(f"Convertendo ferramenta MCP: {mcp_tool.name} (Tags: {tag})")
                    lc_tools.append(self._convert_to_langchain_tool(mcp_tool))
                    
            return lc_tools
        except Exception as e:
            logger.exception(f"Erro ao buscar ferramentas do MCP: {e}")
            return []

    def _convert_to_langchain_tool(self, mcp_tool) -> StructuredTool:
        """
        Converte uma ferramenta MCP individual em uma StructuredTool do LangChain.
        """
        
        async def call_tool_wrapper(**kwargs):
            # Wrapper para chamar a ferramenta remotamente via fastmcp.Client
            logger.info(f"Executando ferramenta MCP {mcp_tool.name} com args: {kwargs}")
            client = Client(self.url)
            async with client:
                result = await client.call_tool(mcp_tool.name, kwargs)
                logger.info(f"Resultado da ferramenta MCP {mcp_tool.name}: {result}")
                
                # O resultado do FastMCP Client costuma ter o atributo 'data'
                if hasattr(result, "data"):
                    return str(result.data)
                if hasattr(result, "text"):
                    return result.text
                return str(result)

        return StructuredTool.from_function(
            func=None,
            coroutine=call_tool_wrapper,
            name=mcp_tool.name,
            description=mcp_tool.description or f"Ferramenta MCP: {mcp_tool.name}",
        )

mcp_discovery = MCPToolDiscovery()
