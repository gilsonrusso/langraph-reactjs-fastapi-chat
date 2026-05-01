import requests
import json
import uuid

def test_sales():
    url = "http://localhost:8000/api/chat"
    payload = {
        "messages": [
            {
                "role": "user",
                "parts": [{"type": "text", "content": "Como foram as vendas recentemente?"}]
            }
        ]
    }
    
    print("\n🌐 Testando Orquestração de Vendas...")
    
    try:
        with requests.post(url, json=payload, stream=True) as response:
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith("data: "):
                        data_str = line_str[6:]
                        try:
                            msg = json.loads(data_str)
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
    test_sales()
