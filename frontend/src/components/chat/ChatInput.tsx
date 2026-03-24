import AttachFileIcon from '@mui/icons-material/AttachFile';
import MicIcon from '@mui/icons-material/Mic';
import SendIcon from '@mui/icons-material/Send';
import { Box, IconButton, TextField } from '@mui/material';
import React, { useState } from 'react';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSendMessage, disabled }) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    if (message.trim()) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box
      sx={{
        p: 2,
        pb: 4,
        position: 'sticky',
        bottom: 0,
        bgcolor: 'background.default',
        width: '100%',
        maxWidth: '800px',
        mx: 'auto',
      }}
    >
      <Box className="gemini-input-wrapper">
        <Box className="gemini-input-inner">
          <IconButton size="small" sx={{ ml: 1, color: 'text.secondary' }}>
            <AttachFileIcon fontSize="small" />
          </IconButton>

          <TextField
            fullWidth
            multiline
            maxRows={10}
            placeholder="Digite um comando aqui"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={disabled}
            variant="outlined"
            autoFocus
            sx={{
              '& .MuiOutlinedInput-root': {
                color: 'text.primary',
                '& fieldset': {
                  border: 'none',
                },
              },
            }}
            slotProps={{
              input: {
                sx: {
                  px: 2,
                  py: 1.5,
                  fontSize: '1rem',
                }
              }
            }}
          />

          <Box sx={{ display: 'flex', gap: 0.5, mr: 1 }}>
            <IconButton size="small" sx={{ color: 'text.secondary' }}>
              <MicIcon fontSize="small" />
            </IconButton>
            <IconButton
              onClick={handleSend}
              disabled={!message.trim() || disabled}
              size="small"
              sx={{
                bgcolor: message.trim() ? '#fff' : 'transparent',
                color: message.trim() ? '#000' : 'action.disabled',
                transition: 'all 0.3s ease',
                '&:hover': {
                  bgcolor: message.trim() ? '#eee' : 'action.hover',
                  transform: message.trim() ? 'scale(1.05)' : 'none',
                },
              }}
            >
              <SendIcon fontSize="small" />
            </IconButton>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default ChatInput;
