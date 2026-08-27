/**
 * Zustand store for Pivota AI Copilot.
 */

import { create } from 'zustand';
import { aiApi } from '../api/aiApi';
import type {
  ConversationResponse,
  MessageResponse,
  DataSourceContextItem,
  AIHealthResponse,
} from '../api/aiApi';

interface DataContext {
  dataSourceId: string;
  dataSourceName: string;
  provider: string;
  database: string;
  schema?: string;
}

interface AIState {
  conversations: ConversationResponse[];
  activeConversation: ConversationResponse | null;
  messages: MessageResponse[];
  dataSources: DataSourceContextItem[];
  selectedContext: DataContext | null;
  health: AIHealthResponse | null;
  
  // Statuses
  isLoadingConversations: boolean;
  isLoadingMessages: boolean;
  isStreaming: boolean;
  isInitialLoading: boolean;

  // Actions
  fetchConversations: () => Promise<void>;
  fetchMessages: (conversationId: string) => Promise<void>;
  fetchContexts: () => Promise<void>;
  checkHealth: () => Promise<void>;
  
  setActiveConversation: (conv: ConversationResponse | null) => void;
  setSelectedContext: (context: DataContext | null) => void;
  
  startNewConversation: (data: { dataSourceId: string; database: string; schema?: string }) => Promise<ConversationResponse>;
  deleteConversation: (id: string) => Promise<void>;
  
  addTempMessage: (message: MessageResponse) => void;
  updateLastMessageContent: (content: string) => void;
  appendLastMessageEvent: (event: any) => void;
  setStreamingState: (streaming: boolean) => void;
  resetChat: () => void;
}

export const useAIStore = create<AIState>((set, get) => ({
  conversations: [],
  activeConversation: null,
  messages: [],
  dataSources: [],
  selectedContext: null,
  health: null,

  isLoadingConversations: false,
  isLoadingMessages: false,
  isStreaming: false,
  isInitialLoading: true,

  fetchConversations: async () => {
    set({ isLoadingConversations: true });
    try {
      const data = await aiApi.listConversations();
      set({ conversations: data.conversations, isInitialLoading: false });
    } catch (err) {
      console.error('Failed to load AI conversations:', err);
    } finally {
      set({ isLoadingConversations: false });
    }
  },

  fetchMessages: async (conversationId: string) => {
    set({ isLoadingMessages: true });
    try {
      const data = await aiApi.listMessages(conversationId);
      set({ messages: data.messages });
    } catch (err) {
      console.error('Failed to load messages:', err);
    } finally {
      set({ isLoadingMessages: false });
    }
  },

  fetchContexts: async () => {
    try {
      const data = await aiApi.getDataContexts();
      set({ dataSources: data.data_sources });
      
      // Auto-select first context if none is active
      if (data.data_sources.length > 0 && !get().selectedContext) {
        const ds = data.data_sources[0];
        const db = ds.databases[0] || { name: 'default', schemas: ['public'] };
        const schema = db.schemas[0] || 'public';
        
        set({
          selectedContext: {
            dataSourceId: ds.id,
            dataSourceName: ds.name,
            provider: ds.provider,
            database: db.name,
            schema,
          },
        });
      }
    } catch (err) {
      console.error('Failed to load data contexts:', err);
    }
  },

  checkHealth: async () => {
    try {
      const data = await aiApi.getHealth();
      set({ health: data });
    } catch (err) {
      console.error('AI Health check failed:', err);
      set({
        health: {
          status: 'unavailable',
          llm_available: false,
          llm_model: 'unknown',
          embedding_available: false,
          embedding_model: 'unknown',
          vector_store_available: false,
        },
      });
    }
  },

  setActiveConversation: (conv) => {
    set({ activeConversation: conv });
    if (conv) {
      get().fetchMessages(conv.id);
      
      // Update selected context to match conversation context
      const matchedDs = get().dataSources.find(ds => ds.id === conv.data_source_id);
      set({
        selectedContext: {
          dataSourceId: conv.data_source_id,
          dataSourceName: matchedDs ? matchedDs.name : 'Database Connection',
          provider: conv.provider,
          database: conv.database_name,
          schema: conv.schema_name,
        },
      });
    } else {
      set({ messages: [] });
    }
  },

  setSelectedContext: (context) => {
    set({ selectedContext: context });
  },

  startNewConversation: async (data) => {
    const res = await aiApi.createConversation({
      data_source_id: data.dataSourceId,
      database: data.database,
      schema_name: data.schema,
    });
    
    // Refresh conversation list
    await get().fetchConversations();
    
    // Initialize active conversation state directly without calling async fetchMessages (avoids race condition)
    const matchedDs = get().dataSources.find(ds => ds.id === res.data_source_id);
    set({
      activeConversation: res,
      messages: [],
      selectedContext: {
        dataSourceId: res.data_source_id,
        dataSourceName: matchedDs ? matchedDs.name : 'Database Connection',
        provider: res.provider,
        database: res.database_name,
        schema: res.schema_name,
      }
    });
    
    return res;
  },

  deleteConversation: async (id) => {
    await aiApi.deleteConversation(id);
    const active = get().activeConversation;
    
    if (active && active.id === id) {
      set({ activeConversation: null, messages: [] });
    }
    
    await get().fetchConversations();
  },

  addTempMessage: (message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },

  updateLastMessageContent: (content) => {
    set((state) => {
      const msgs = [...state.messages];
      if (msgs.length === 0) return { messages: msgs };
      
      const last = msgs[msgs.length - 1];
      if (last.role === 'assistant') {
        last.content = content;
      }
      return { messages: msgs };
    });
  },

  appendLastMessageEvent: (event) => {
    set((state) => {
      const msgs = [...state.messages];
      if (msgs.length === 0) return { messages: msgs };
      
      const last = msgs[msgs.length - 1];
      if (last.role === 'assistant') {
        // Update type and metadata depending on event
        if (event.type === 'sql_generated') {
          last.message_type = 'sql';
          last.metadata_json = {
            ...last.metadata_json,
            sql: event.sql,
            query_type: event.query_type,
          };
        } else if (event.type === 'query_completed') {
          last.message_type = 'sql';
          last.metadata_json = {
            ...last.metadata_json,
            row_count: event.row_count,
            columns: event.columns,
            rows: event.rows,
            execution_time_ms: event.execution_time_ms,
          };
        } else if (event.type === 'error') {
          last.message_type = 'error';
        }
      }
      return { messages: msgs };
    });
  },

  setStreamingState: (streaming) => set({ isStreaming: streaming }),

  resetChat: () => {
    set({ activeConversation: null, messages: [] });
  },
}));
