import asyncio
import httpx
import json

async def test_api_orchestration():
    print("🌐 Testando Orquestração via API (Supervisor -> Sub-agente -> MCP)...")
    
    url = "http://localhost:8000/api/chat"
    payload = {
        "messages": [
            {
                "role": "user",
                "parts": [{"type": "text", "content": "Quais produtos você tem disponíveis?"}]
            }
        ]
    }
    
    print("\n--- Usuário: Quais produtos você tem disponíveis? ---")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json=payload) as response:
                if response.status_code != 200:
                    print(f"❌ Erro na API: {response.status_code}")
                    print(await response.aread())
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data == "[DONE]":
                            break
                        try:
                            msg = json.loads(data)
                            chunk = msg.get("chunk", [])
                            if isinstance(chunk, list):
                                for part in chunk:
                                    if part.get("type") == "text":
                                        print(part.get("text", ""), end="", flush=True)
                            elif isinstance(chunk, str):
                                print(chunk, end="", flush=True)
                        except:
                            pass
    except Exception as e:
        print(f"\n❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_api_orchestration())
