# 📚 Documentação do Projeto: LangGraph + ReactJS + FastAPI Chat

Bem-vindo à documentação técnica do ecossistema de agentes inteligentes. Este projeto utiliza uma arquitetura de ponta baseada em grafos de estados e descoberta dinâmica de ferramentas.

## 📂 Estrutura de Documentação

### 🏗️ Arquitetura
- **[Explicação da Arquitetura](architecture_explanation.md)**: Detalha por que usamos LangGraph como motor e DeepAgents como framework de orquestração.
- **[Fluxo Técnico Passo a Passo](technical_flow.md)**: Um guia detalhado do ciclo de vida de uma mensagem, desde o FastAPI até o LLM.
- **[Design Patterns para Agentes](Optimizing%20Agent%20Design%20Patterns.md)**: Discussão sobre padrões de projeto para evitar abstrações prematuras.

### 🎨 Frontend & UI
- **[Padrão de Generative UI](generative_ui_pattern.md)**: Guia sobre como o frontend intercepta chamadas de ferramentas para renderizar componentes React ricos (Cards, Gráficos, Skeletons) em vez de apenas texto.

## 🛠️ Stack Tecnológica

| Camada | Tecnologia |
| :--- | :--- |
| **Engine de Agentes** | LangGraph |
| **Orquestrador** | DeepAgents (Network of Agents) |
| **Descoberta de Tools** | MCP (Model Context Protocol) via FastMCP |
| **Backend API** | FastAPI |
| **Frontend Chat** | React + TanStack AI (protocolo Vercel AI SDK) |
| **Persistência** | SQLite (Checkpointer assíncrono) |

## 🚀 Conceitos Chave

1. **Context Quarantine**: Técnica para isolar o histórico de ferramentas de sub-agentes, garantindo que o supervisor receba apenas o resultado processado.
2. **Dynamic Tool Discovery**: Uso do MCP para que o backend exponha rotas FastAPI como ferramentas para os agentes em tempo real, filtradas por tags.
3. **Human-In-The-Loop (HITL)**: Interrupções nativas do grafo para aprovação de ações sensíveis (como agendamentos ou envios de e-mail).
