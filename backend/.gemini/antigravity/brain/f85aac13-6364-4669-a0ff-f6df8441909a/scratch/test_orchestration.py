import asyncio
import sys
import os

# Adiciona o diretório backend ao path
sys.path.append(os.path.abspath("backend"))

from app.agents.graph import graph
from langchain_core.messages import HumanMessage

async def test_orchestration():
    print("🤖 Testando Orquestração Hierárquica...")
    
    config = {"configurable": {"thread_id": "test_thread"}}
    
    # Pergunta que deve ser delegada ao agente de produtos
    inputs = {"messages": [HumanMessage(content="Quais produtos você tem disponíveis?")]}
    
    print("\n--- Usuário: Quais produtos você tem disponíveis? ---")
    async for event in graph.astream_events(inputs, config, version="v2"):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                print(content, end="", flush=True)
        elif kind == "on_tool_start":
            print(f"\n[Tool Start] {event['name']} with {event['data'].get('input')}")
        elif kind == "on_tool_end":
            print(f"\n[Tool End] {event['name']} finished.")

if __name__ == "__main__":
    asyncio.run(test_orchestration())
