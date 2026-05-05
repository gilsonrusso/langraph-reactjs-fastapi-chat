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

    async def get_tools(self, tag: Optional[str] = None, mcp_server: Any = None) -> List[StructuredTool]:
        """
        Descobre as ferramentas. Se mcp_server for fornecido, usa-o localmente.
        Caso contrário, conecta via SSE na URL configurada.
        """
        lc_tools = []
        try:
            if mcp_server:
                logger.info(f"Descobrindo ferramentas localmente do servidor MCP: {mcp_server.name}")
                mcp_tools = await mcp_server.list_tools()
                logger.info(f"Total de ferramentas encontradas no servidor: {len(mcp_tools)}")
                
                for mcp_tool in mcp_tools:
                    logger.info(f"Inspecionando ferramenta MCP: {mcp_tool.name}, Meta: {getattr(mcp_tool, 'meta', 'N/A')}")
                    if tag:
                        tool_tags = []
                        # 1. Tenta atributo direto (comum em execução local)
                        if hasattr(mcp_tool, "tags") and mcp_tool.tags:
                            tool_tags = list(mcp_tool.tags)
                        
                        # 2. Tenta atributo meta (comum em execução remota)
                        elif hasattr(mcp_tool, "meta") and isinstance(mcp_tool.meta, dict):
                            fastmcp_meta = mcp_tool.meta.get("fastmcp", {})
                            if isinstance(fastmcp_meta, dict):
                                tool_tags = fastmcp_meta.get("tags", [])
                            
                            if not tool_tags:
                                tool_tags = mcp_tool.meta.get("tags", [])
                        
                        if tag not in tool_tags:
                            logger.debug(f"Ferramenta {mcp_tool.name} não possui a tag {tag}. Tags encontradas: {tool_tags}")
                            continue
                    
                    logger.info(f"Convertendo ferramenta MCP local: {mcp_tool.name} (Tags: {tag})")
                    lc_tools.append(self._convert_to_langchain_tool(mcp_tool, mcp_server=mcp_server))
            else:
                client = Client(self.url)
                async with client:
                    mcp_tools = await client.list_tools()
                    logger.info(f"Total de ferramentas remotas encontradas: {len(mcp_tools)}")
                    
                    for mcp_tool in mcp_tools:
                        if tag:
                            tool_tags = []
                            # 1. Tenta atributo direto
                            if hasattr(mcp_tool, "tags") and mcp_tool.tags:
                                tool_tags = list(mcp_tool.tags)
                            
                            # 2. Tenta atributo meta
                            elif hasattr(mcp_tool, "meta") and isinstance(mcp_tool.meta, dict):
                                fastmcp_meta = mcp_tool.meta.get("fastmcp", {})
                                if isinstance(fastmcp_meta, dict):
                                    tool_tags = fastmcp_meta.get("tags", [])
                                if not tool_tags:
                                    tool_tags = mcp_tool.meta.get("tags", [])
                            
                            if tag not in tool_tags:
                                continue
                        
                        logger.info(f"Convertendo ferramenta MCP remota: {mcp_tool.name} (Tags: {tag})")
                        lc_tools.append(self._convert_to_langchain_tool(mcp_tool))
                    
            return lc_tools
        except Exception as e:
            logger.exception(f"Erro ao buscar ferramentas do MCP: {e}")
            return []

    def _convert_to_langchain_tool(self, mcp_tool, mcp_server: Any = None) -> StructuredTool:
        """
        Converte uma ferramenta MCP individual em uma StructuredTool do LangChain.
        """
        
        async def call_tool_wrapper(**kwargs):
            logger.info(f"Executando ferramenta MCP {mcp_tool.name} com args: {kwargs}")
            
            if mcp_server:
                # Execução local direta
                result = await mcp_server.call_tool(mcp_tool.name, kwargs)
            else:
                # Execução remota via SSE Client
                client = Client(self.url)
                async with client:
                    result = await client.call_tool(mcp_tool.name, kwargs)
            
            logger.info(f"Resultado da ferramenta MCP {mcp_tool.name}: {result}")
            
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
