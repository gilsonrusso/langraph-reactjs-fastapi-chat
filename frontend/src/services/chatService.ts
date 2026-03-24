import type { Message } from "../types/chat";

const API_BASE = 'http://localhost:8000';

export const chatService = {
  async getHistory(): Promise<{ id: string; title: string }[]> {
    const response = await fetch(`${API_BASE}/api/history`);
    if (!response.ok) throw new Error('Failed to fetch history');
    return response.json();
  },

  async getChatHistory(threadId: string): Promise<Message[]> {
    const response = await fetch(`${API_BASE}/api/chat/${threadId}`);
    if (!response.ok) throw new Error('Failed to fetch chat history');
    const data = await response.json();
    return data.messages;
  },

  async deleteChat(threadId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/api/chat/${threadId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete chat');
  },
};
