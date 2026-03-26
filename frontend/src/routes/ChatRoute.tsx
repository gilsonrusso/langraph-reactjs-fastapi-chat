import { Box, CircularProgress, Typography } from '@mui/material';
import type { StreamChunk } from '@tanstack/ai';
import { createChatClientOptions, fetchServerSentEvents, type InferChatMessages } from '@tanstack/ai-client';
import { useChat } from '@tanstack/ai-react';
import React, { useEffect, useMemo, useState, useRef } from 'react';
import { useLocation, useNavigate } from 'react-router';
import ChatContainer from '../components/chat/ChatContainer';
import { useChatDetail } from '../hooks/useChatQueries';
import type { Role } from '../types/chat';
import { v4 as uuidv4 } from 'uuid';

interface ChatRouteProps {
  onHistoryUpdate: () => void;
}

const ChatRouteReady: React.FC<{
  id: string;
  initialMsgs: any[];
  onHistoryUpdate: () => void;
  isNewChatUrl: boolean;
  onFormalize: (id: string) => void;
}> = ({ id, initialMsgs, onHistoryUpdate, isNewChatUrl, onFormalize }) => {
  const navigate = useNavigate();

  // Configurações mestre instanciadas para ancorar o link ao endpoint de Chat streaming (TanStack).
  // Exige um array de 'initialMessages' ao carregar conversas passadas restauradas pelo cache Query.
  const chatOptions = createChatClientOptions({
    id: id,
    connection: fetchServerSentEvents('http://localhost:8000/api/chat'),
    initialMessages: initialMsgs,
    body: {
      checkpoint_id: id,
    },
    onChunk: (chunk: StreamChunk) => {
      const c = chunk as unknown as Record<string, unknown>;
      if (c.type === 'checkpoint' && typeof c.checkpoint_id === 'string') {
        onHistoryUpdate();
      }
    },
  });

  type RouteMessage = InferChatMessages<typeof chatOptions>[number];

  const { messages: tanstackMessages, sendMessage, isLoading, clear } = useChat(chatOptions);

  useEffect(() => {
    if (isNewChatUrl) {
      clear();
    }
  }, [id, isNewChatUrl, clear]);

  const handleSendMessage = (text: string) => {
    if (isNewChatUrl) {
      // Impede temporariamente o componente Chat de se desmontar destruindo a conexão.
      // Ele "formaliza" essa montagem nova e migra a URL com o respectivo UUID recém gerado.
      onFormalize(id);
      navigate(`/c/${id}`, { replace: true });
    }
    // Dispara a chamada nativa geradora pro SSE / API do OpenAI ou Agente no Backend
    sendMessage(text);
  };

  const mappedMessages = useMemo(() => {
    if (!tanstackMessages) return [];

    return tanstackMessages.map((msg: RouteMessage, idx: number) => {
      let content = '';
      let hasToolCall = false;
      let toolName = '';

      if (msg.parts && Array.isArray(msg.parts)) {
        msg.parts.forEach((part) => {
          if (part.type === 'tool-call') {
            hasToolCall = true;
            toolName = part.name || 'ferramenta';
          } else if (part.type === 'text' || (part as any).type === 'content') {
            content += (part as any).text || (part as any).content || '';
          } else if (part.type === 'thinking') {
            content += `\n> 🤔 **Pensando:** ${(part as any).content}\n\n`;
          }
        });
      } else {
        content = typeof (msg as any).content === 'string' ? (msg as any).content : typeof (msg as any).text === 'string' ? (msg as any).text : '';
      }

      if (hasToolCall && !content) {
        content = `Executando ${toolName}...`;
      }

      return {
        id: (msg.id as string) || `msg-${idx}`,
        role: (msg.role === 'user' || (msg as any).role === 'tool' ? (msg as any).role : hasToolCall && !content ? 'tool' : 'assistant') as Role,
        content: content || '',
        parts: msg.parts || [],
        metadata: (msg as any).metadata
      };
    }).filter(msg => {
       const isAssistant = msg.role === 'assistant';
       const hasText = msg.content.trim() !== '';
       const hasTools = msg.parts && Array.isArray(msg.parts) && msg.parts.some(p => p.type === 'tool-call');
       
       if (!isAssistant) return hasText;
       // Permite Assistant message ser renderizada se tiver texto OU tiver chamada de ferramenta (mesmo sem texto)
       return hasText || hasTools;
    });
  }, [tanstackMessages]);

  return (
    <Box
      sx={{
        flexGrow: 1,
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        bgcolor: 'background.default',
      }}
    >
      <ChatContainer
        messages={mappedMessages}
        isLoading={isLoading}
        onSendMessage={handleSendMessage}
      />
    </Box>
  );
};

export const ChatRoute: React.FC<ChatRouteProps> = ({ onHistoryUpdate }) => {
  const location = useLocation();
  const idFromUrl = location.pathname.startsWith('/c/') ? location.pathname.split('/')[2] : undefined;

  // UUID raiz. Fixado durante as rotas temporárias onde a URL pura ainda carece de formalização.
  const [activeId, setActiveId] = useState(() => idFromUrl || uuidv4());
  
  // Uma Ref invisível a renderizações. Previne a revalidação Query de apagar os balões do chat ao formalizar na primeira mensagem enviada.
  const justFormalizedIdRef = useRef<string | null>(null);
  
  // Efeito responsável pela vida íntegra da janela de navegação cruzada entre Sidebar Buttons e Voltar/Avançar Nativo do Browser
  useEffect(() => {
    if (idFromUrl) {
      setActiveId((prev) => {
        if (idFromUrl !== prev) {
          justFormalizedIdRef.current = null;
          return idFromUrl;
        }
        return prev;
      });
    } else {
      setActiveId(uuidv4());
      justFormalizedIdRef.current = null;
    }
  }, [idFromUrl]);

  const isNewChatUrl = !idFromUrl;

  const shouldFetch = !!idFromUrl && idFromUrl === activeId && justFormalizedIdRef.current !== activeId;
  const { data: msgs, isLoading } = useChatDetail(shouldFetch ? activeId : undefined);
  
  const isInitializing = shouldFetch && isLoading;

  const initialMsgs = useMemo(() => {
    if (!msgs) return [];
    return msgs.map(m => {
      let txt = '';
      if (m.parts && Array.isArray(m.parts)) {
        txt = m.parts.filter((p: any) => p.type === 'text' || p.type === 'content').map((p: any) => p.text || p.content || '').join('');
      }
      return {
        id: m.id || uuidv4(),
        role: m.role === 'tool' ? 'assistant' : m.role,
        content: txt || m.content || '',
        parts: m.parts || []
      };
    });
  }, [msgs]);

  if (isInitializing) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', gap: 2, bgcolor: 'background.default' }}>
        <CircularProgress size={40} sx={{ color: 'primary.main' }} />
        <Typography variant="body2" color="text.secondary">
          Carregando histórico...
        </Typography>
      </Box>
    );
  }

  return (
    <ChatRouteReady
      key={activeId}
      id={activeId}
      initialMsgs={initialMsgs}
      onHistoryUpdate={onHistoryUpdate}
      isNewChatUrl={isNewChatUrl}
      onFormalize={(id) => { justFormalizedIdRef.current = id; }}
    />
  );
};
