import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import PersonIcon from '@mui/icons-material/Person';
import SearchIcon from '@mui/icons-material/Search';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import { Avatar, Box, Link, Paper, Typography } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export interface MessageProps {
  role: 'user' | 'assistant' | 'tool';
  content: string;
  metadata?: {
    urls?: string[];
  };
}

const ChatMessage: React.FC<MessageProps> = ({ role, content, metadata }) => {
  const isAssistant = role === 'assistant';
  const isTool = role === 'tool';

  if (isTool) {
    return (
      <Box sx={{ display: 'flex', flexDirection: 'row', gap: 2, mb: 1, maxWidth: '800px', width: '100%', mx: 'auto', px: 2, opacity: 0.7 }}>
        <Box sx={{ width: 32, display: 'flex', justifyContent: 'center' }}>
          <SearchIcon sx={{ fontSize: 18, color: 'text.secondary' }} />
        </Box>
        <Typography variant="caption" sx={{ fontStyle: 'italic', pt: 0.2 }}>
          {content}
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'row',
        gap: 2,
        mb: 3,
        maxWidth: '800px',
        width: '100%',
        mx: 'auto',
        px: 2,
      }}
    >
      <Avatar
        sx={{
          bgcolor: isAssistant ? 'primary.main' : 'secondary.main',
          width: 32,
          height: 32,
          mt: 0.5,
        }}
      >
        {isAssistant ? <SmartToyIcon sx={{ fontSize: 20 }} /> : <PersonIcon sx={{ fontSize: 20 }} />}
      </Avatar>

      <Box sx={{ flex: 1 }}>
        <Typography
          variant="subtitle2"
          sx={{ fontWeight: 'bold', mb: 0.5, color: 'text.secondary', fontSize: '0.75rem', textTransform: 'uppercase' }}
        >
          {isAssistant ? 'AI' : 'Você'}
        </Typography>
        <Paper
          elevation={0}
          sx={{
            p: 2,
            borderRadius: 2,
            bgcolor: isAssistant ? 'action.hover' : 'transparent',
            border: isAssistant ? '1px solid' : 'none',
            borderColor: 'divider',
            '& p': { mb: 1.5, '&:last-child': { mb: 0 } },
            '& code': {
              bgcolor: 'action.selected',
              px: 0.5,
              py: 0.2,
              borderRadius: 1,
              fontFamily: 'monospace',
              fontSize: '0.9em'
            },
            '& pre': {
              bgcolor: 'action.selected',
              p: 2,
              borderRadius: 1,
              overflowX: 'auto',
              my: 2,
              '& code': { bgcolor: 'transparent', p: 0 }
            },
            '& ul, & ol': {
              pl: 3,
              mb: 1.5
            }
          }}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({ children }) => (
                <Typography variant="body1" sx={{ lineHeight: 1.6 }}>
                  {children}
                </Typography>
              ),
              // Support additional overrides if needed
            }}
          >
            {content}
          </ReactMarkdown>

          {isAssistant && metadata?.urls && metadata.urls.length > 0 && (
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
              <Typography variant="caption" sx={{ fontWeight: 'bold', display: 'block', mb: 1, color: 'text.secondary' }}>
                FONTES:
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                {metadata.urls.map((url, index) => (
                  <Link
                    key={index}
                    href={url}
                    target="_blank"
                    rel="noopener noreferrer"
                    sx={{
                      fontSize: '0.75rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 0.5,
                      textDecoration: 'none',
                      '&:hover': { textDecoration: 'underline' }
                    }}
                  >
                    <OpenInNewIcon sx={{ fontSize: 12 }} />
                    {new URL(url).hostname}
                  </Link>
                ))}
              </Box>
            </Box>
          )}
        </Paper>
      </Box>
    </Box>
  );
};

export default ChatMessage;
