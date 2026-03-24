import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
  Divider,
  Button,
  IconButton,
} from '@mui/material';
import ChatBubbleOutlineIcon from '@mui/icons-material/ChatBubbleOutline';
import AddIcon from '@mui/icons-material/Add';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';

const DRAWER_WIDTH = 280;

interface SidebarProps {
  history: { id: string; title: string }[];
  currentId: string | null;
  onSelectChat: (id: string | null) => void;
  onDeleteChat: (id: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  history,
  currentId,
  onSelectChat,
  onDeleteChat,
}) => {
  return (
    <Drawer
      variant="permanent"
      sx={(theme) => ({
        width: DRAWER_WIDTH,
        flexShrink: 0,
        [`& .MuiDrawer-paper`]: {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          backgroundColor: theme.palette.background.default,
          borderRight: `1px solid ${theme.palette.divider}`,
        },
      })}
    >
      <Box sx={{ p: 2 }}>
        <Button
          fullWidth
          variant="outlined"
          startIcon={<AddIcon />}
          onClick={() => onSelectChat(null)}
          sx={{
            borderRadius: '12px',
            textTransform: 'none',
            py: 1,
            color: '#444',
            borderColor: '#ddd',
            '&:hover': {
              backgroundColor: '#eee',
              borderColor: '#ccc',
            },
          }}
        >
          Nova conversa
        </Button>
      </Box>

      <Divider />

      <Box sx={{ overflow: 'auto', flexGrow: 1 }}>
        <List sx={{ px: 1 }}>
          <Typography variant="overline" sx={{ px: 2, py: 1, color: '#666', fontWeight: 'bold' }}>
            Recentes
          </Typography>
          {history.map((chat) => (
            <ListItem
              key={chat.id}
              disablePadding
              secondaryAction={
                <IconButton
                  edge="end"
                  aria-label="delete"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteChat(chat.id);
                  }}
                  size="small"
                  sx={{
                    opacity: 0,
                    transition: 'opacity 0.2s',
                    color: 'text.secondary',
                    '&:hover': { color: 'error.main' },
                  }}
                  className="delete-button"
                >
                  <DeleteOutlineIcon fontSize="small" />
                </IconButton>
              }
              sx={{
                mb: 0.5,
                '&:hover .delete-button': { opacity: 1 },
              }}
            >
              <ListItemButton
                selected={currentId === chat.id}
                onClick={() => onSelectChat(chat.id)}
                sx={{
                  borderRadius: '8px',
                  pr: 5, // Espaço para o botão de deletar
                  '&.Mui-selected': {
                    backgroundColor: '#e3f2fd',
                    color: '#1976d2',
                    '&:hover': {
                      backgroundColor: '#daebf7',
                    },
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: 'inherit' }}>
                  <ChatBubbleOutlineIcon fontSize="small" />
                </ListItemIcon>
                <ListItemText
                  primary={chat.title}
                  primaryTypographyProps={{
                    variant: 'body2',
                    noWrap: true,
                    fontWeight: currentId === chat.id ? '600' : '400',
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Box>
    </Drawer>
  );
};
