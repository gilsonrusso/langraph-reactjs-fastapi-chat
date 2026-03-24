import { Box, CircularProgress, Typography } from '@mui/material';
import type { StreamChunk } from '@tanstack/ai';
import { fetchServerSentEvents } from '@tanstack/ai-client';
import { useChat } from '@tanstack/ai-react';
import React, { useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router';
import ChatContainer from '../components/chat/ChatContainer';
import { chatService } from '../services/chatService';

interface ChatRouteProps {
  onHistoryUpdate: () => void;
}

interface MessagePart {
  type: string;
  text?: string;
  content?: string;
}

// ----------------------------------------------------
// INNER COMPONENT: Only mounts when history is READY
// ----------------------------------------------------
const ChatRouteReady: React.FC<{
  id: string; // Guaranteed to be a valid UUID explicitly
  initialMsgs: any[];
  onHistoryUpdate: () => void;
  isNewChatUrl: boolean;
}> = ({ id, initialMsgs, onHistoryUpdate, isNewChatUrl }) => {
  const navigate = useNavigate();
  
  const { messages: tanstackMessages, sendMessage, isLoading } = useChat({
    id: id, // Explicitly namespace the chat client to prevent cross-contamination!
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

  const handleSendMessage = (text: string) => {
    if (isNewChatUrl) {
      navigate(`/c/${id}`, { replace: true });
    }
    sendMessage(text);
  };

  const mappedMessages = useMemo(() => {
    if (!tanstackMessages) return [];
    
    return tanstackMessages.map((msg, idx: number) => {
      let content = '';
      let hasToolCall = false;
      let toolName = '';

      const anyMsg = msg as unknown as Record<string, unknown>;

      if (anyMsg.parts && Array.isArray(anyMsg.parts)) {
        // Extract tool calls
        const toolPart = anyMsg.parts.find((p: MessagePart | unknown) => {
          const part = p as MessagePart;
          return part.type === 'tool-call';
        }) as (MessagePart & { toolName?: string }) | undefined;
        
        if (toolPart) {
          hasToolCall = true;
          toolName = toolPart.toolName || 'ferramenta';
        }

        // Extract text
        content = anyMsg.parts
          .filter((p: MessagePart | unknown) => {
            const part = p as MessagePart;
            return part.type === 'text' || part.type === 'content';
          })
          .map((p: MessagePart | unknown) => {
            const part = p as MessagePart;
            return part.text || part.content || '';
          })
          .join('');
      } else {
        content = typeof anyMsg.content === 'string' ? anyMsg.content : typeof anyMsg.text === 'string' ? anyMsg.text : '';
      }

      if (hasToolCall && !content) {
        content = `Executando ${toolName}...`;
      }

      return {
        id: (anyMsg.id as string) || `msg-${idx}`,
        role: (anyMsg.role === 'user' ? 'user' : hasToolCall && !content ? 'tool' : 'assistant') as 'user' | 'assistant' | 'tool',
        content: content || '',
      };
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

// ----------------------------------------------------
// OUTER COMPONENT: Handles loading the history async
// ----------------------------------------------------
export const ChatRoute: React.FC<ChatRouteProps> = ({ onHistoryUpdate }) => {
  const location = useLocation();
  // Parse ID since we are using a wildcard route `/*`
  const idFromUrl = location.pathname.startsWith('/c/') ? location.pathname.split('/')[2] : undefined;
  
  // Guarantee an ID natively per component unmount lifespan. 
  // If the URL has no ID, establish a strong local UUID upfront!
  const [activeId] = useState(() => idFromUrl || crypto.randomUUID());
  const isNewChatUrl = !idFromUrl;

  const [initialMsgs, setInitialMsgs] = useState<any[]>([]);
  // Only stall rendering if we came with an explicit URL ID that needs verification
  const [isInitializing, setIsInitializing] = useState(!!idFromUrl);

  useEffect(() => {
    // If this component mounts WITH a requested URL ID, fetch its history strictly!
    if (idFromUrl) {
      chatService.getChatHistory(idFromUrl)
        .then(msgs => {
          // Format messages tightly so TanStack accepts them unconditionally
          const compatibleMsgs = msgs.map(m => {
            let txt = '';
            if (m.parts && Array.isArray(m.parts)) {
              txt = m.parts.filter((p: any) => p.type === 'text' || p.type === 'content').map((p: any) => p.text || p.content || '').join('');
            }
            return {
              id: m.id || crypto.randomUUID(),
              role: m.role === 'tool' ? 'assistant' : m.role,
              content: txt || m.content || '',
              parts: m.parts || []
            };
          });
          setInitialMsgs(compatibleMsgs);
          setIsInitializing(false);
        })
        .catch(err => {
          console.error('Failed to load history:', err);
          setIsInitializing(false);
        });
    }
  }, [idFromUrl]);

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
      id={activeId} 
      initialMsgs={initialMsgs} 
      onHistoryUpdate={onHistoryUpdate} 
      isNewChatUrl={isNewChatUrl} 
    />
  );
};
