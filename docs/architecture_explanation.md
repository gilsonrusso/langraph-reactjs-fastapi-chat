# Arquitetura de Agentes: Network of Agents (LangGraph + DeepAgents)

Este documento formaliza o design pattern adotado para a nossa rede de múltiplos especialistas e detalha a escolha tecnológica atual.

## 1. Evolução: De LangChain para LangGraph
Anteriormente, o design seguia o padrão de *Hierarchical Agents with Tools* do LangChain clássico, onde sub-agentes eram escondidos dentro de ferramentas do supervisor.

### O Problema do "Efeito Caixa Preta":
- **Ocultação de Estado:** O supervisor não via o processo de pensamento do especialista.
- **Quebra de Streaming:** Eventos de sub-ferramentas não chegavam ao frontend.
- **Instabilidade HITL:** Dificuldade em pausar para aprovação humana dentro de uma execução de ferramenta.

## 2. O Motor: LangGraph
Adotamos o **LangGraph** como nosso motor principal. Ele transforma a IA em uma **Máquina de Estados (Grafo)**, permitindo:
- **Observabilidade Total:** Cada passo do agente é um nó visível no grafo.
- **Persistência (Memory):** Checkpointing nativo que permite retomar conversas meses depois.
- **Streaming de Eventos:** Suporte nativo ao protocolo `astream_events`, essencial para interfaces de chat modernas.

## 3. O Framework: DeepAgents
Embora o LangGraph seja o motor, usamos o **DeepAgents** como nosso chassi/framework de alto nível.

> [!IMPORTANT]
> **DeepAgents não substitui o LangGraph.** Ele roda em cima dele. Ao chamar `create_deep_agent`, o sistema gera automaticamente um grafo do LangGraph altamente otimizado.

### Vantagem Principal: Context Quarantine
O maior problema de grafos manuais é o "vazamento de contexto". O `deepagents` resolve isso isolando a execução dos sub-agentes. O supervisor delega uma tarefa via ferramenta `task()` e recebe apenas o resultado final limpo, economizando tokens e evitando que o histórico fique poluído com logs técnicos.

## 4. Arquitetura Atual: Semantic/Dynamic Routing (MCP)
Para gerenciar dezenas de ferramentas agrupadas em especialidades (tags), usamos:

1. **`EXPERTS_METADATA`**: Um mapa semântico que define o "currículo" de cada especialista.
2. **Model Context Protocol (MCP)**: O backend (FastMCP) expõe rotas FastAPI como ferramentas em runtime.
3. **Descoberta Dinâmica**: O sistema lê as ferramentas locais do MCP e as injeta nos sub-agentes baseados em suas tags (`products`, `sales`, etc).

### Fluxo de Execução:
1. **User**: "Quais produtos vendem mais?"
2. **Supervisor**: Analisa a intenção e usa a ferramenta `task` para chamar o sub-agente `sales`.
3. **Sub-agente Sales**: Recebe o contexto isolado, usa ferramentas MCP de histórico de vendas e processa o dado.
4. **Supervisor**: Recebe a resposta do especialista e a resume para o usuário final.

Este modelo garante escalabilidade infinita, baixo consumo de tokens e streaming perfeito para a UI.
