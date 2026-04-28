# LangGraph FastAPI Chat Backend

Este diretório contém o servidor backend responsável por gerenciar a lógica de Inteligência Artificial usando LangGraph, LangChain e FastAPI.

## 🏛 Arquitetura Modular

Recentemente, o backend foi refatorado para uma estrutura modular de nível profissional, separando as preocupações em arquivos especializados:

- **`main.py`**: Ponto de entrada, configuração do FastAPI e ciclo de vida (Lifespan).
- **`routes.py`**: Definição de todos os endpoints da API (`/chat`, `/history`, etc.) usando `APIRouter`.
- **`agents.py`**: Fábrica de agentes, prompts do sistema e definição do **Supervisor**.
- **`services.py`**: Lógica de negócio e processamento de streaming de eventos.
- **`tools.py`**: Definição das ferramentas base (clima, calendário, e-mail).
- **`schemas.py`**: Modelos Pydantic para validação de dados.
- **`utils.py`**: Funções utilitárias de conversão e formatação.

## 🤖 Padrão de Supervisor

O backend utiliza uma arquitetura de múltiplos agentes orquestrados por um **Supervisor**:

1. **Supervisor Agent:** Atua como o roteador central. Ele analisa a intenção do usuário e decide qual sub-agente ou ferramenta deve ser utilizado.
2. **Calendar Agent:** Especialista em processamento de linguagem natural para agendamentos, verificação de disponibilidade e criação de eventos.
3. **Email Agent:** Especialista em composição de e-mails profissionais e extração de destinatários.

### Middlewares & Segurança
- **Human-in-the-Loop (HITL):** Implementamos middlewares que interrompem a execução de ferramentas críticas (como `send_email` ou `create_calendar_event`) para solicitar aprovação do usuário antes da ação final.
- **Persistência SQLite:** O histórico da conversa é mantido de forma segura no arquivo `checkpoints.sqlite`, permitindo retomar diálogos mesmo após o reinício do servidor.

## ⚙️ Tecnologias Utilizadas

- **FastAPI:** Framework web assíncrono.
- **LangGraph:** Orquestração de grafos de estado para agentes.
- **SQLite (AsyncSqliteSaver):** Persistência de memória.
- **Langfuse:** Observabilidade e rastreamento de traces.

## 🚀 Como Rodar

1. Certifique-se de ter as variáveis de ambiente configuradas no `.env`.
2. Execute o servidor:
   ```bash
   uv run uvicorn main:app --reload
   ```
   *Nota: O servidor agora roda por padrão em `127.0.0.1` por segurança.*

## 🛠 Qualidade de Código (Lint & Format)

Utilizamos o **Ruff** para garantir que o código esteja limpo e siga as melhores práticas:

- **Checagem de erros:** `uv run ruff check .`
- **Auto-correção:** `uv run ruff check --fix .`
- **Formatação:** `uv run ruff format .`

---
Este backend foi projetado para ser escalável, modular e resiliente.
