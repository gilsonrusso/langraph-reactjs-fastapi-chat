import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp/sse") as client:
        tools = await client.list_tools()
        print(f"\nEncontradas {len(tools)} ferramentas:")
        for tool in tools:
            tags = tool.meta.get('fastmcp', {}).get('tags', [])
            print(f"- {tool.name} (Tags: {tags})")
            
if __name__ == "__main__":
    asyncio.run(main())
