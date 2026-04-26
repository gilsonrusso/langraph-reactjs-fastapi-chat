# 📌 Evolução Arquitetural — Chat com LangChain + SSE + TanStack AI

## 🎯 Objetivo

Este documento descreve as melhorias técnicas necessárias para evoluir a implementação atual de um chat com agente, focando em padronização de protocolos, robustez e manutenibilidade.

A arquitetura base utiliza:
- **Backend**: FastAPI com streaming SSE e LangGraph.
- **Frontend**: React com TanStack AI (`@tanstack/ai-react`).
- **Persistência**: SQLite via LangGraph Checkpointer.

---

# 🧠 Diagnóstico Técnico (Veredito)

A base atual é sólida, utilizando `astream_events` (v2) e persistência assíncrona. No entanto, existe um **desacoplamento de protocolo** entre o que o backend emite e o que o TanStack AI espera nativamente.

### Pontos Críticos Identificados:
1. **Inconsistência de Tipos SSE**: O backend usa `TEXT_MESSAGE_CONTENT`, enquanto o padrão esperado pelo ecossistema AI SDK / TanStack tende a `content`.
2. **Tool Calls Manuais**: O frontend reconstrói o estado da ferramenta manualmente porque o backend não envia os eventos no formato `tool-call` / `tool-result` esperado.
3. **Parsing Inseguro**: O uso de `ast.literal_eval` para processar outputs de ferramentas é um risco de segurança e instabilidade.
4. **Falta de Heartbeat**: Conexões SSE sem keep-alive são propensas a interrupções por proxies/gateways.

---

# 🚀 Estratégias de Evolução (3 Opções Técnicas)

## 🔵 Opção 1: Padronização Nativa (Protocolo TanStack/AI-SDK) - **Recomendado**

Esta opção elimina a necessidade de parsing manual no frontend, fazendo com que o backend fale a "língua nativa" das abstrações do TanStack AI.

### Implementação Backend (FastAPI):
- **Mensagens de Texto**: 
  ```python
  yield f"data: {json.dumps({'type': 'content', 'delta': text})}\n\n"
  ```
- **Tool Calls**:
  ```python
  yield f"data: {json.dumps({
      'type': 'tool_call',
      'id': tool_call_id,
      'name': tool_name,
      'args': args
  })}\n\n"
  ```
- **Tool Results**:
  ```python
  yield f"data: {json.dumps({
      'type': 'tool_result',
      'tool_call_id': tool_call_id,
      'result': result_data
  })}\n\n"
  ```

### Benefícios:
- O hook `useChat` do TanStack AI processa automaticamente as partes da mensagem.
- Redução drástica na lógica de `mappedMessages` no frontend.

---

## 🔴 Opção 2: Camada de Adaptação (Adapter Pattern)

Se o backend precisar suportar múltiplos clientes ou formatos internos legados, implementamos uma camada de tradução antes do `yield`.

### Implementação:
Criar uma classe utilitária `TanStackEventAdapter` para encapsular a criação dos envelopes JSON.

```python
class TanStackEventAdapter:
    @staticmethod
    def text_delta(content: str) -> str:
        return json.dumps({"type": "content", "delta": content})

    @staticmethod
    def tool_start(call_id: str, name: str, args: dict) -> str:
        return json.dumps({"type": "tool_call", "id": call_id, "name": name, "args": args})
```

### Benefícios:
- Isola a lógica do LangGraph da lógica de transporte (SSE).
- Facilita testes unitários da camada de streaming.

---

## 🟡 Opção 3: Padronização de Output e Segurança (Tool Output Logic)

Foca em resolver a instabilidade do parsing de ferramentas e garantir que o contrato de dados seja rigoroso.

### Implementação:
1. **Substituir `ast.literal_eval` por `json.loads`**: Garantir que todas as ferramentas retornem strings JSON válidas ou dicionários que o LangChain serializa corretamente.
2. **Strict Tools**: Forçar as ferramentas a retornarem modelos Pydantic ou JSON estruturado.
   ```python
   @tool
   def get_weather(location: str) -> str:
       # Sempre retorna JSON serializado
       return json.dumps({"temp": 25, "unit": "C"})
   ```

---

# ⚙️ Melhorias de Infraestrutura (Produção-Grade)

### 1. SSE Keep-Alive (Heartbeat)
Para evitar que a conexão caia em timeouts de 30s/60s (comum em Heroku/Vercel/NGINX):
```python
async def heartbeat():
    while True:
        yield ": ping\n\n"
        await asyncio.sleep(15)
```

### 2. Tratamento de Erros Estruturado
Enviar eventos do tipo `error` que o TanStack AI possa capturar no callback `onError`.

---

# 📊 Avaliação Técnica de Impacto

| Critério | Estado Atual | Pós-Evolução | Nota (Evolução) |
| :--- | :---: | :---: | :---: |
| **Arquitetura** | 8.5 | 9.5 | ⭐⭐⭐⭐⭐ |
| **Manutenibilidade** | 6.5 | 9.0 | ⭐⭐⭐⭐ |
| **Robustez (Produção)** | 6.0 | 9.0 | ⭐⭐⭐⭐⭐ |
| **DX (Developer Experience)** | 6.0 | 9.5 | ⭐⭐⭐⭐⭐ |

---

# 🧠 Conclusão e Próximos Passos

A evolução proposta remove o "acoplamento frágil" entre o streaming customizado e o frontend, transformando o sistema em uma solução robusta pronta para escala.

**Próximos Passos:**
1. Refatorar `stream_agui_events` em `backend/main.py`.
2. Simplificar o `useMemo` de mensagens em `ChatRoute.tsx`.
3. Implementar o heartbeat no loop de streaming.
