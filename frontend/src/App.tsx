import React, { useState, useEffect } from 'react';
import { Box, ThemeProvider, CssBaseline } from '@mui/material';
import { Sidebar } from './components/layout/Sidebar';
import { useAppTheme } from './ui/theme';
import { chatService } from './services/chatService';
import { ConfirmDialog } from './components/ui/ConfirmDialog';
import { Routes, Route, useNavigate, useLocation } from 'react-router';
import { ChatRoute } from './routes/ChatRoute';

const App: React.FC = () => {
  const theme = useAppTheme();
  const [history, setHistory] = useState<{ id: string; title: string }[]>([]);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [chatToDelete, setChatToDelete] = useState<string | null>(null);
  
  const navigate = useNavigate();
  const location = useLocation();
  
  // Extract current chat ID from URL
  const currentId = location.pathname.startsWith('/c/') ? location.pathname.split('/')[2] : null;

  // A manual key that only changes when the user clicks the sidebar, 
  // explicitly preventing unmounts when the URL formalizes during streaming.
  const [routeKey, setRouteKey] = useState<string>(currentId || 'new');

  // Initial load of history
  useEffect(() => {
    chatService.getHistory().then(setHistory).catch(console.error);
  }, []);

  const handleSelectChat = (id: string | null) => {
    setRouteKey(id || `new-${Date.now()}`);
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

  const handleConfirmDelete = async () => {
    if (chatToDelete) {
      await chatService.deleteChat(chatToDelete);
      
      setHistory(prev => prev.filter(c => c.id !== chatToDelete));
      
      if (currentId === chatToDelete) {
        setRouteKey(`new-${Date.now()}`);
        navigate('/');
      }
    }
    setDeleteConfirmOpen(false);
    setChatToDelete(null);
  };

  const handleHistoryUpdate = () => {
    chatService.getHistory().then(setHistory).catch(console.error);
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
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
          <Routes>
            <Route path="/*" element={<ChatRoute key={routeKey} onHistoryUpdate={handleHistoryUpdate} />} />
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
