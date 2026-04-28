# LangGraph ReactJS & FastAPI Chat

Um ecossistema completo de Chatbot inteligente utilizando a stack moderna de IA: **LangGraph**, **FastAPI** e **React**.

## 🚀 Visão Geral

Este projeto demonstra como construir uma aplicação de chat "Agentic" de ponta a ponta. O sistema utiliza um **Supervisor Agent** para orquestrar sub-agentes especialistas (Calendário e E-mail), integrando-se com uma interface React fluida e responsiva.

## 🏗 Estrutura do Projeto

O repositório é dividido em duas partes principais:

- **`/backend`**: Servidor FastAPI modularizado que gerencia os agentes LangGraph, ferramentas e persistência em SQLite.
- **`/frontend`**: Aplicação React com TanStack Query e componentes modernos para streaming de mensagens em tempo real.

## 🛠 Principais Tecnologias

### Backend
- **LangGraph & LangChain:** Orquestração de grafos de estado e agentes.
- **FastAPI:** Framework web assíncrono de alta performance.
- **SQLite:** Persistência de memória (checkpoints) das conversas.
- **Langfuse:** Observabilidade e rastreamento de traces de IA.

### Frontend
- **React:** Biblioteca de interface de usuário.
- **TanStack AI / Query:** Gerenciamento de estado e streaming de dados.
- **Material UI / Tailwind:** Estilização moderna e responsiva.

## 🏁 Como Começar

### Pré-requisitos
- Python 3.10+
- Node.js 18+
- Docker (opcional, para Langfuse)

### Configuração do Backend
1. Entre na pasta `backend/`.
2. Crie um arquivo `.env` baseado no `.env.example`.
3. Instale as dependências: `pip install -r requirements.txt` (ou use `uv sync`).
4. Inicie o servidor: `uvicorn main:app --reload`.

### Configuração do Frontend
1. Entre na pasta `frontend/`.
2. Instale as dependências: `npm install`.
3. Inicie o servidor de desenvolvimento: `npm run dev`.

---

## 🏛 Arquitetura de Agentes

O projeto utiliza o padrão **Supervisor-Worker**:
1. **Supervisor:** Recebe a entrada do usuário e decide qual ferramenta/especialista acionar.
2. **Workers (Sub-agentes):** Agentes especialistas em Calendário e E-mail que executam tarefas específicas com segurança e aprovação humana (Middlewares).

---
Desenvolvido com ❤️ usando a stack mais moderna de IA.
