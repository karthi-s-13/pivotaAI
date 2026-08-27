/**
 * Custom chat integration hook for Pivota AI.
 * Handles dispatching messages, triggering the SSE reader, and updating the Zustand store.
 */

import { useAIStore } from '../stores/aiStore';
import { useStreamingResponse } from './useStreamingResponse';

export function useChat() {
  const {
    activeConversation,
    startNewConversation,
    selectedContext,
    addTempMessage,
    updateLastMessageContent,
    appendLastMessageEvent,
    setStreamingState,
    fetchConversations,
  } = useAIStore();

  const { streamMessage, stopStreaming, isStreaming } = useStreamingResponse();

  const sendMessage = async (content: string) => {
    if (!content.trim()) return;

    let conv = activeConversation;

    // 1. If no active conversation, create a new one first
    if (!conv) {
      if (!selectedContext) {
        console.error('No database context selected');
        return;
      }
      try {
        conv = await startNewConversation({
          dataSourceId: selectedContext.dataSourceId,
          database: selectedContext.database,
          schema: selectedContext.schema,
        });
      } catch (err) {
        console.error('Failed to auto-create conversation context:', err);
        return;
      }
    }

    // 2. Add the user's message to the store for display
    const tempUserMsg = {
      id: Math.random().toString(36).slice(2, 9),
      role: 'user' as const,
      content,
      message_type: 'text' as const,
      created_at: new Date().toISOString(),
    };
    addTempMessage(tempUserMsg);

    // 3. Add an empty assistant placeholder to receive the stream
    const tempAssistantMsg = {
      id: 'temp-assistant-id',
      role: 'assistant' as const,
      content: '',
      message_type: 'text' as const,
      created_at: new Date().toISOString(),
    };
    addTempMessage(tempAssistantMsg);

    setStreamingState(true);
    let accumulatedText = '';

    // 4. Stream response
    try {
      await streamMessage(conv.id, content, {
        onMessageStart: () => {
          accumulatedText = '';
          updateLastMessageContent('');
        },
        onTextDelta: (delta) => {
          accumulatedText += delta;
          updateLastMessageContent(accumulatedText);
        },
        onSQLGenerated: (sql, queryType) => {
          appendLastMessageEvent({ type: 'sql_generated', sql, queryType });
        },
        onQueryStarted: () => {
          // Option to display loading spinner inside message bubbles
        },
        onQueryCompleted: (result) => {
          appendLastMessageEvent({
            type: 'query_completed',
            columns: result.columns,
            rows: result.rows,
            row_count: result.rowCount,
            execution_time_ms: result.executionTimeMs,
          });
        },
        onMessageComplete: async () => {
          // Refresh conversation list to get updated titles/timestamp
          await fetchConversations();
          
          // Re-sync messages from db to ensure IDs match
          const store = useAIStore.getState();
          if (store.activeConversation) {
            await store.fetchMessages(store.activeConversation.id);
          }
        },
        onError: (err) => {
          appendLastMessageEvent({ type: 'error' });
          updateLastMessageContent(`⚠️ Connection Error: ${err}`);
        },
      });
    } finally {
      setStreamingState(false);
    }
  };

  return {
    sendMessage,
    stopStreaming,
    isStreaming,
  };
}
