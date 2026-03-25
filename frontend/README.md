# ReactJS TanStack AI Frontend

Este é o cliente Web SPA projetado em React, Vite e Material UI para lidar com as premissas ricas de interatividade gráfica exigidas por conversas e fluxos de Agentes de IA Generativa.

## 🏛 Arquitetura

O frontend é pautado por um controle e sincronização perfeita de dados em camadas variadas. Isso combina o cache declarativo HTTP clássico com o rastreio contínuo e responsivo do fluxo de conversações e transições em Server-Sent Events (SSE).

- **React & Vite:** Base do ambiente de renderização reativo do SPA unido à rapidez de servidor (HMR) e empacotador de build otimizado contidos nativamente no Vite.
- **@tanstack/ai-react:** Orquestrador principal da conversa ao vivo. Lida fluidamente e sem falhas com canais SSE oriundos da rede. Esse provedor desacopla lógicas densas e mapeia imediatamente partes interativas (*textos, tool-calls, pensamentos visíveis*) em uma variação controlada e tipificada.
- **TanStack Query (React Query) & Axios:** Solução arquitetural para busca de dados convencionais como chamadas API fixas (Restaurar contatos do Chat Histórico ou Excluir uma conversa). Removeu o uso complexo e frágil dos hooks padrão (`useEffect`/`useState`) de requisição manual, entregando cache automático.
- **Material UI (MUI):** Toda folha de estilo (grids, botões, modais) é processada pelo Theme Provider do MUI fornecendo temas responsivos e tipografia flexível padronizada.
- **React Router:** Controla o status top-level manipulando a URL (ex: `/c/:uuid`). Qualquer variação na URL força recálculos coerentes garantindo estabilidade e reinício dos Web Workers dedicados ao canal da conversa sem causar bleed de dados ("vazar mensagens").

## ⚙️ Principais Funcionalidades

- **Conversões Stream-to-UI Sensíveis:** Através das "Parts" declaradas pelo framework da IA, o Frontend distingue imediatamente visualizações entre textos cruciais e "A IA Acabou de Ativar uma Ferramenta!" com caixas sombreadas limpas sem transbordar logs indesejados.
- **Ciclo de Vida a Prova de Falhas (Hard-Resets):** Mecânismos rigorosos unindo custom hooks limpam explicitamente buffers de IA da memória ao trocar o chat via Sidebar ou criar uma janela limpa Nova de conversa, eliminando retenção de contexto legado.
- **Suporte Multimídia (Markdown):** Exige forte interpretação local renderizando em tempo real com `react-markdown` elementos elaborados gerados por LLMs como Listas aninhadas e blocos destacados de códigos sintáticos em painéis formatados.
