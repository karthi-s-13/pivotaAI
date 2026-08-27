/**
 * SSE Streaming hook for Pivota AI Copilot.
 * Connects to the POST /ai/chat endpoint and parses stream events.
 */

import { useState } from 'react';

export interface StreamHandlers {
  onMessageStart?: () => void;
  onTextDelta?: (text: string) => void;
  onSQLGenerated?: (sql: string, queryType: string) => void;
  onQueryStarted?: () => void;
  onQueryCompleted?: (result: { columns: string[]; rows: any[]; rowCount: number; executionTimeMs: number }) => void;
  onMessageComplete?: (messageId: string) => void;
  onError?: (error: string) => void;
}

export function useStreamingResponse() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [abortController, setAbortController] = useState<AbortController | null>(null);

  const streamMessage = async (
    conversationId: string,
    message: string,
    handlers: StreamHandlers
  ) => {
    setIsStreaming(true);
    const controller = new AbortController();
    setAbortController(controller);

    const token = localStorage.getItem('pivota_access_token');
    const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api/v1';

    try {
      const response = await fetch(`${API_BASE_URL}/ai/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          message,
        }),
        signal: controller.signal,
      });

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage = 'Failed to send message';
        try {
          const errObj = JSON.parse(errorText);
          errorMessage = errObj.detail || errObj.message || errorMessage;
        } catch {
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }

      if (!response.body) {
        throw new Error('ReadableStream not supported by server response');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        
        // Save the last incomplete line back to the buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data:')) continue;

          try {
            const jsonStr = trimmed.slice(5).trim();
            const data = JSON.parse(jsonStr);

            switch (data.type) {
              case 'message_start':
                handlers.onMessageStart?.();
                break;
              case 'text_delta':
                handlers.onTextDelta?.(data.content);
                break;
              case 'sql_generated':
                handlers.onSQLGenerated?.(data.sql, data.query_type);
                break;
              case 'query_started':
                handlers.onQueryStarted?.();
                break;
              case 'query_completed':
                handlers.onQueryCompleted?.({
                  columns: data.columns,
                  rows: data.rows,
                  rowCount: data.row_count,
                  executionTimeMs: data.execution_time_ms,
                });
                break;
              case 'message_complete':
                handlers.onMessageComplete?.(data.message_id);
                break;
              case 'error':
                handlers.onError?.(data.message);
                break;
            }
          } catch (e) {
            console.error('Failed to parse SSE stream line:', line, e);
          }
        }
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        logger('Stream aborted by user');
      } else {
        console.error('SSE Stream Error:', err);
        handlers.onError?.(err.message || 'Connection lost');
      }
    } finally {
      setIsStreaming(false);
      setAbortController(null);
    }
  };

  const stopStreaming = () => {
    if (abortController) {
      abortController.abort();
      setIsStreaming(false);
      setAbortController(null);
    }
  };

  return {
    streamMessage,
    stopStreaming,
    isStreaming,
  };
}

function logger(...args: any[]) {
  if (import.meta.env.DEV) {
    console.log('[SSE Stream]', ...args);
  }
}
