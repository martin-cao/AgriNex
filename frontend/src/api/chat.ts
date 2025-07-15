import { http } from './http';
import type { ChatMessage, SendMessageRequest, ApiResponse } from '@/types';

export const chatApi = {
  // 发送消息
  sendMessage: (data: SendMessageRequest): Promise<ApiResponse<{
    message: string;
    type?: string;
    chart_title?: string;
    chart_data?: any;
    table_columns?: any[];
    table_data?: any[];
    actions?: Array<{ label: string; action: string; params?: any }>;
  }>> => {
    return http.post('/api/llm/message', data);
  },

  // 获取对话历史
  getConversation: (conversationId: string): Promise<ApiResponse<ChatMessage[]>> => {
    return http.get(`/api/llm/conversation/${conversationId}`);
  },

  // 获取对话列表
  getConversations: (): Promise<ApiResponse<Array<{
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
  }>>> => {
    return http.get('/api/llm/conversations');
  },

  // 创建新对话
  createConversation: (title?: string): Promise<ApiResponse<{
    id: string;
    title: string;
    created_at: string;
  }>> => {
    return http.post('/api/llm/conversation', { title });
  },

  // 删除对话
  deleteConversation: (conversationId: string): Promise<ApiResponse<void>> => {
    return http.delete(`/api/llm/conversation/${conversationId}`);
  },

  // 获取建议问题
  getSuggestions: (): Promise<ApiResponse<string[]>> => {
    return http.get('/api/llm/suggestions');
  }
};
