import { Box, Divider, Typography } from '@mui/material';
import React, { useEffect, useRef } from 'react';
import ChatInput from './ChatInput';
import ChatMessage, { type MessageProps } from './ChatMessage';

interface ChatContainerProps {
  messages: MessageProps[];
  onSendMessage: (message: string) => void;
  isLoading?: boolean;
}

const ChatContainer: React.FC<ChatContainerProps> = ({ messages, onSendMessage, isLoading }) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
        bgcolor: 'background.default',
        overflow: 'hidden',
      }}
    >
      {/* Header */}
      <Box sx={{ py: 2, px: 3, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="h6" sx={{ fontWeight: 500, color: 'text.primary' }}>
          AI
        </Typography>
        <Typography variant="body2" sx={{ color: 'text.secondary', fontWeight: 400 }}>
          Assistent
        </Typography>
      </Box>

      <Divider />

      {/* Messages Area */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          py: 4,
          display: 'flex',
          flexDirection: 'column',
          gap: 1,
        }}
      >
        {messages.length === 0 ? (
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              opacity: 0.6,
            }}
          >
            <Typography variant="h4" sx={{ mb: 2, fontWeight: 500, textAlign: 'center' }}>
              Olá,
            </Typography>
            <Typography variant="h6" sx={{ color: 'text.secondary', textAlign: 'center' }}>
              Como posso ajudar você hoje?
            </Typography>
          </Box>
        ) : (
          messages.map((msg, index) => (
            <ChatMessage key={index} role={msg.role} content={msg.content} />
          ))
        )}

        {isLoading && (
          <Box sx={{ width: '100%', maxWidth: '800px', mx: 'auto', px: 2, mb: 3 }}>
            {/* Simple loading indicator or skeleton could go here */}
            <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
              AI está pensando...
            </Typography>
          </Box>
        )}

        <div ref={messagesEndRef} />
      </Box>

      {/* Input Area */}
      <ChatInput onSendMessage={onSendMessage} disabled={isLoading} />
    </Box>
  );
};

export default ChatContainer;
