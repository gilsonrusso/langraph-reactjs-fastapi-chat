# Padrão Arquitetural: Generative UI (GenUI) com LangGraph e React

Este documento descreve o padrão recomendado para renderizar componentes de Interface Dinâmicos (Cards, Tabelas, Gráficos) dentro do chat da aplicação, baseado no protocolo de **Chamadas de Ferramenta (Tool Calls)**.

---

## O que é Generative UI (GenUI)?

Em vez da Inteligência Artificial formatar uma lista longa e genérica de texto usando Markdown natural, a IA invoca uma ferramenta (Tool). O único objetivo dessa ferramenta é estruturar um JSON rígido e passar a responsabilidade da renderização visual para um componente React desenhado por você, combinando o raciocínio inteligente da IA com o visual nativo do seu Frontend.

## Fluxo de Execução

1. **O Usuário pede:** "Me mostre opções de planos."
2. **O LangGraph raciocina:** Ao invés de escrever, ele chama a ferramenta `/mostrar_cards_planos` fornecendo um JSON populado com as respostas adequadas.
3. **O FastAPI intercepta:** A interceptação do nó não processa nenhum scraper real; ela emite ("stream") o JSON puro ao canal Server-Sent Events (SSE).
4. **O TanStack/Vercel AI intercepta:** Coloca na lista de mensagens uma tag de Tool Call.
5. **O React reage:** A tela do chat mapeia o array, enxerga essa tag, destrói a visualização em Markdown, e instancia `<CardsPlanos dados={json} />`.

---

## Passo a Passo para Implementação

### 1. Preparar o Backend (Langgraph)

Crie uma "ferramenta cega" (dummy tool), cujo único objetivo seja declarar o Schema (Pydantic/Tipagem) que força a IA a entregar a estrutura JSON perfeita.

```python
# backend/tools/ui_tools.py
from langchain_core.tools import tool

@tool
def render_product_cards(produtos: list[dict]):
    """
    Use esta ferramenta APENAS quando o usuário pedir para ver uma lista de produtos.
    A entrada deve ser estruturada com 'titulo', 'preco', e 'descricao'.
    """
    # A ferramenta não executa nenhuma inteligência de busca.
    # O próprio ato de receber a chamada é o resultado de retorno para a interface!
    return "UI injetada na tela com sucesso."
```

Adicione essa ferramenta ao array de ferramentas (`tools = [..., render_product_cards]`) do seu agente LangGraph.

### 2. Modificar o Streaming no FastAPI

No seu gerador assíncrono `stream_agui_events` (em `backend/main.py`), intercepte essa chamada de ferramenta *antes* que a IA escreva uma resposta completa:

```python
# Em backend/main.py
elif kind == "on_tool_end":
    tool_call_id = event.get("run_id", "unknown_id")
    input_data = event["data"].get("input", {}) 
    # Aqui em 'input_data' está o JSON preenchido pela IA!
    
    name = event["name"]
    
    if name == "render_product_cards":
        # Formata o output para o frontend entender que é uma UI Dinâmica
        yield f"data: {json.dumps({'type': 'UI_COMPONENT', 'component': 'ProductCards', 'props': input_data})}\n\n"
    else:
        # Mantém a rotina normal para ferramentas invisíveis (Ex: Web Search)
        yield f"data: {json.dumps({'type': 'TOOL_CALL_END', 'toolCallId': tool_call_id, 'toolName': name, 'result': 'Sucesso'})}\n\n"
```

### 3. Parse e Tipagem no React (Frontend)

Atualize seu `MessagePart` na interface tipada (`frontend/src/types/chat.ts`) para suportar a montagem deste interceptador de interface:

```typescript
export interface MessagePart {
  type: string;        // Pode ser 'text', 'UI_COMPONENT'
  text?: string;       // Conteúdo se for markdown
  component?: string;  // Nome do componente React ('ProductCards')
  props?: any;         // JSON contendo os dados injetados
}
```

### 4. Desenhar no Mapa de Mensagens

Localize onde o Array de Histórico é inteirado (ex: `ChatMessage.tsx` ou em `ChatContainer.tsx`), faça um by-pass na renderização Padrão.

```tsx
// frontend/src/components/chat/ChatMessage.tsx
import ProductCards from './ui-components/ProductCards';

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  // Passa por todas as partes que o Backend montou para esta mensagem temporal
  const uiPart = message.parts?.find(p => p.type === 'UI_COMPONENT');

  if (uiPart) {
    if (uiPart.component === 'ProductCards') {
       // Em vez de retornar ReactMarkdown, retorna seu super Componente
       return (
         <div className="genui-wrapper">
             <ProductCards dados={uiPart.props.produtos} />
         </div>
       );
    }
  }

  // Fallback seguro: se não tiver UI Component, rederiza Markdown puro.
  const textContent = message.parts?.filter(p => p.type === 'text').map(p => p.text).join('') || message.content;
  
  return <MarkdownRenderer content={textContent} />;
};
```

## Conclusão

Essa rotação de lógica tira do LLM o esforço inútil de tentar acertar formatações ricas em Markdown, e coloca o design nas mãos do React moderno. Seus botões podem ter links para Carrinho, pop-ups, loaders reais, e o chat atuará de maneira "Agentic", sendo não apenas um papo, mas um navegador operado por texto.
