import React, { useState } from 'react';
import { Box, ThemeProvider, CssBaseline } from '@mui/material';
import { Sidebar } from './components/layout/Sidebar';
import { useAppTheme } from './ui/theme';
import { ConfirmDialog } from './components/ui/ConfirmDialog';
import { Routes, Route, useNavigate, useLocation } from 'react-router';
import { ChatRoute } from './routes/ChatRoute';

import { useQueryClient } from '@tanstack/react-query';
import { useChatHistoryList, useDeleteChat } from './hooks/useChatQueries';

const App: React.FC = () => {
  const theme = useAppTheme();
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<string | null>(null);

  const queryClient = useQueryClient();
  const { data: history = [] } = useChatHistoryList();
  const deleteChatMutation = useDeleteChat();
  
  const navigate = useNavigate();
  const location = useLocation();
  
  // Extract current chat ID from URL
  const currentId = location.pathname.startsWith('/c/') ? location.pathname.split('/')[2] : null;

  // A manual key that only changes when the user clicks the sidebar, 
  // Initial load of history is handled automatically by useChatHistoryList hook

  const handleSelectChat = (id: string | null) => {
    if (id) {
      navigate(`/c/${id}`);
    } else {
      navigate('/');
    }
  };

  const handleDeleteRequest = (id: string) => {
    setChatToDelete(id);
    setDeleteConfirmOpen(true);
  };

  const handleConfirmDelete = () => {
    if (chatToDelete) {
      deleteChatMutation.mutate(chatToDelete, {
        onSuccess: () => {
          if (currentId === chatToDelete) {
            navigate('/');
          }
        }
      });
    }
    setDeleteConfirmOpen(false);
    setChatToDelete(null);
  };

  const handleHistoryUpdate = () => {
    queryClient.invalidateQueries({ queryKey: ['chatHistoryList'] });
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
        <Sidebar
          history={history}
          currentId={currentId}
          onSelectChat={handleSelectChat}
          onDeleteChat={handleDeleteRequest}
        />
        <Box
          sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}
        >
          <Routes>
            <Route path="/*" element={<ChatRoute onHistoryUpdate={handleHistoryUpdate} />} />
          </Routes>
        </Box>
      </Box>

      <ConfirmDialog
        open={deleteConfirmOpen}
        title="Excluir Conversa"
        content="Tem certeza que deseja excluir esta conversa? Esta ação não pode ser desfeita."
        onConfirm={handleConfirmDelete}
        onCancel={() => {
          setDeleteConfirmOpen(false);
          setChatToDelete(null);
        }}
      />
    </ThemeProvider>
  );
};

export default App;
