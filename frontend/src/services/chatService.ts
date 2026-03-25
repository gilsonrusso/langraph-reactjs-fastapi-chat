import type { Message } from "../types/chat";
import { api } from "../lib/axios";

export const chatService = {
  async getHistory(): Promise<{ id: string; title: string }[]> {
    const { data } = await api.get('/api/history');
    return data;
  },

  async getChatHistory(threadId: string): Promise<Message[]> {
    const { data } = await api.get(`/api/chat/${threadId}`);
    return data.messages;
  },

  async deleteChat(threadId: string): Promise<void> {
    await api.delete(`/api/chat/${threadId}`);
  },
};
