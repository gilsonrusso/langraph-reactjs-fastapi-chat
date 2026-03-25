import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { chatService } from '../services/chatService';

export const useChatHistoryList = () => {
  return useQuery({
    queryKey: ['chatHistoryList'],
    queryFn: chatService.getHistory,
  });
};

export const useChatDetail = (threadId?: string) => {
  return useQuery({
    queryKey: ['chatHistory', threadId],
    queryFn: () => chatService.getChatHistory(threadId!),
    enabled: !!threadId,
  });
};

export const useDeleteChat = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: chatService.deleteChat,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['chatHistoryList'] });
    },
  });
};
