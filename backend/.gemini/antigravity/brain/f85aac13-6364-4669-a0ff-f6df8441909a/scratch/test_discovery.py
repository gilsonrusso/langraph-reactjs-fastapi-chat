import asyncio
import sys
import os

# Adiciona o diretório backend ao path
sys.path.append(os.path.abspath("backend"))

from app.tools.mcp_client import MCPToolDiscovery

async def test():
    print("🔍 Testando descoberta de ferramentas via FastMCP Client...")
    # Usando a URL SSE explicitamente
    discovery = MCPToolDiscovery(url="http://localhost:8000/mcp/sse")
    try:
        # Testa produtos
        print("\n--- Produtos ---")
        product_tools = await discovery.get_tools(prefix="")
        for t in product_tools:
            if "products" in t.name:
                print(f"✅ Encontrada: {t.name}")
        
        # Testa vendas
        print("\n--- Vendas ---")
        sales_tools = await discovery.get_tools(prefix="")
        for t in sales_tools:
            if "sales" in t.name:
                print(f"✅ Encontrada: {t.name}")
            
    except Exception as e:
        import traceback
        print(f"❌ Erro na descoberta: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
