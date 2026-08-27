/**
* Pivota AI Copilot API.
*/

import apiClient from '../../../services/api/apiClient';

export interface ConversationCreate {
  data_source_id: string;
  database: string;
  schema_name?: string;
}

export interface ConversationResponse {
  id: string;
  title: string;
  provider: string;
  database_name: string;
  schema_name?: string;
  data_source_id: string;
  data_source_name?: string;
  created_at: string;
  updated_at: string;
  last_message?: string;
  message_count: number;
}

export interface ConversationListResponse {
  conversations: ConversationResponse[];
  total: number;
}

export interface MessageResponse {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  message_type: 'text' | 'sql' | 'query_result' | 'error';
  metadata_json?: {
    sql?: string;
    query_type?: string;
    row_count?: number;
    execution_time_ms?: number;
    columns?: string[];
    rows?: Record<string, any>[];
  };
  created_at: string;
}

export interface DatabaseContextItem {
  name: string;
  schemas: string[];
}

export interface DataSourceContextItem {
  id: string;
  name: string;
  provider: string;
  health_status: string;
  databases: DatabaseContextItem[];
}

export interface DataContextResponse {
  data_sources: DataSourceContextItem[];
}

export interface AIHealthResponse {
  status: 'ready' | 'degraded' | 'unavailable';
  llm_available: boolean;
  llm_model: string;
  embedding_available: boolean;
  embedding_model: string;
  vector_store_available: boolean;
  message?: string;
}

export const aiApi = {
  createConversation: async (data: ConversationCreate): Promise<ConversationResponse> => {
    const response = await apiClient.post('/ai/conversations', data);
    return response.data;
  },

  listConversations: async (): Promise<ConversationListResponse> => {
    const response = await apiClient.get('/ai/conversations');
    return response.data;
  },

  getConversation: async (id: string): Promise<ConversationResponse> => {
    const response = await apiClient.get(`/ai/conversations/${id}`);
    return response.data;
  },

  deleteConversation: async (id: string): Promise<{ status: string; message: string }> => {
    const response = await apiClient.delete(`/ai/conversations/${id}`);
    return response.data;
  },

  listMessages: async (conversationId: string): Promise<{ messages: MessageResponse[]; conversation_id: string }> => {
    const response = await apiClient.get(`/ai/conversations/${conversationId}/messages`);
    return response.data;
  },

  getDataContexts: async (): Promise<DataContextResponse> => {
    const response = await apiClient.get('/ai/context');
    return response.data;
  },

  getHealth: async (): Promise<AIHealthResponse> => {
    const response = await apiClient.get('/ai/health');
    return response.data;
  },

  triggerIndexing: async (
    dataSourceId: string,
    params?: { database?: string; schema_name?: string }
  ): Promise<{ status: string; documents_indexed: number; message?: string }> => {
    const response = await apiClient.post(`/ai/index/${dataSourceId}`, null, { params });
    return response.data;
  },
};
