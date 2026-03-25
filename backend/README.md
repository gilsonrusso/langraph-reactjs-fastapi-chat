# LangGraph FastAPI Chat Backend

Este diretório contém o servidor backend responsável por gerenciar a lógica de Inteligência Artificial usando LangGraph, LangChain e FastAPI.

## 🏛 Arquitetura

O backend segue uma arquitetura orientada a agentes (Agentic Architecture), onde um LLM (Large Language Model) atua como o "cérebro" das operações, utilizando ferramentas (Tools) para interagir com recursos externos (como buscas na internet).

- **FastAPI:** Framework web principal. Fornece uma API REST rápida e assíncrona, lidando com rotas HTTP tradicionais e Server-Sent Events (SSE) para streaming das respostas do modelo.
- **LangChain & LangGraph:** Os pilares da inteligência artificial. O LangGraph gerencia o "estado" e a "memória" multi-agente através de grafos controlados salvaguardando turnos sequenciais.
- **SQLite (AsyncSqliteSaver):** Banco de dados local empregado para salvar o contexto / histórico (Checkpoints) das conversas. Opera assincronamente para que múltiplas conexões não bloqueiem a thread principal do servidor web enquanto o LLM processa requisições.
- **Tavily Search:** Ferramenta integrada (via `TavilySearchResults`) que empodera o LLM a realizar buscas na web em tempo real durante a formulação das respostas de maneira isolada e segura.

## ⚙️ Principais Funcionalidades

- **Gerenciamento Unificado de Ferramentas:** Respostas da IA são envelopadas em um único fluxo de tokens que empacota o padrão, permitindo que a interface gráfica saiba exatamente se a IA está apenas "falando" (texto) ou executando ações/pesquisas (tool calls).
- **Streaming Bidirecional:** O endpoint principal de chat usa o modelo assíncrono padrão do setor (Server-Sent Events: `EventSourceResponse`) para atualizar o texto do cliente imediatamente à medida que a LLM vai "pensando" e redigindo seu contexto iterativamente.
- **Recuperação de Histórico Persistente (`/api/history` e `/api/chat/{id}`):** Endpoints tradicionais REST que extraem iterativamente dados brutos do SQLite (`checkpoints.sqlite`). Os arrays de mensagem brutos retidos pelo *checkpoint* da LangChain são refatorados localmente no JSON universal que o front end exibe como uma conversa íntegra resgatada.
