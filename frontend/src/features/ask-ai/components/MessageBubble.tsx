import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Sparkles, AlertCircle, Clock } from 'lucide-react';

import SQLBlock from './SQLBlock';
import ResultTable from './ResultTable';
import type { MessageResponse } from '../api/aiApi';
import { useAIStore } from '../stores/aiStore';

interface MessageBubbleProps {
  message: MessageResponse;
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const { selectedContext } = useAIStore();
  const isUser = message.role === 'user';
  const hasMetadata = !!message.metadata_json;

  const formatTime = (timeStr: string) => {
    try {
      const d = new Date(timeStr);
      return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return '';
    }
  };

  return (
    <div
      style={{
        display: 'flex',
        gap: '16px',
        margin: '24px 0',
        flexDirection: isUser ? 'row-reverse' : 'row',
        alignItems: 'flex-start',
      }}
      className="animate-fade-in"
    >
      {/* Icon Avatar with Gemini/User styling */}
      <div
        style={{
          width: 36,
          height: 36,
          borderRadius: '50%',
          background: isUser ? '#f3f4f6' : 'linear-gradient(135deg, #4285f4, #9b51e0, #e051a8)',
          border: isUser ? '1px solid var(--border-default)' : 'none',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          boxShadow: isUser ? 'none' : '0 2px 8px rgba(155, 81, 224, 0.3)',
        }}
      >
        {isUser ? (
          <User size={18} style={{ color: 'var(--text-primary)' }} />
        ) : (
          <Sparkles size={18} color="white" />
        )}
      </div>

      {/* Message Bubble container */}
      <div
        style={{
          maxWidth: '75%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: isUser ? 'flex-end' : 'flex-start',
          gap: 6,
        }}
      >
        <div
          style={{
            padding: isUser ? '12px 18px' : '0px 4px', // Assistant message has no border box for Gemini AI integrated feel
            borderRadius: isUser ? '20px 20px 4px 20px' : '0',
            background: isUser ? '#000000' : 'transparent',
            color: isUser ? '#ffffff' : 'var(--text-primary)',
            fontSize: '0.92rem',
            lineHeight: 1.6,
            border: 'none',
            boxShadow: 'none',
          }}
        >
          {/* Main Answer Text or Loaders */}
          {message.content === '' && message.role === 'assistant' ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '12px 0' }}>
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: '#9b51e0',
                  animation: 'bounce 1.2s infinite ease-in-out',
                }}
              />
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: '#e051a8',
                  animation: 'bounce 1.2s infinite ease-in-out 0.2s',
                }}
              />
              <div
                style={{
                  width: 8,
                  height: 8,
                  borderRadius: '50%',
                  background: '#4285f4',
                  animation: 'bounce 1.2s infinite ease-in-out 0.4s',
                }}
              />
              <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 500, marginLeft: 4 }}>
                Thinking...
              </span>
            </div>
          ) : message.message_type === 'error' ? (
            <div
              style={{
                display: 'flex',
                gap: 10,
                padding: '12px 16px',
                borderRadius: '12px',
                background: 'var(--status-error-bg)',
                border: '1px solid var(--status-error)',
                color: 'var(--status-error)',
                fontSize: '0.85rem',
                fontWeight: 500,
              }}
            >
              <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 1 }} />
              <div>{message.content}</div>
            </div>
          ) : (
            <div className="prose prose-sm max-w-none text-inherit dark:prose-invert font-sans">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Render SQL Block */}
          {hasMetadata && message.metadata_json?.sql && (
            <SQLBlock
              sql={message.metadata_json.sql}
              queryType={message.metadata_json.query_type}
              databaseId={selectedContext?.dataSourceId}
              databaseName={selectedContext?.database}
            />
          )}

          {/* Render Query Results Table */}
          {hasMetadata && message.metadata_json?.rows && message.metadata_json.rows.length > 0 && (
            <div style={{ marginTop: 14 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 700, color: 'var(--text-muted)', letterSpacing: '0.05em' }}>
                  QUERY RUN SUMMARY
                </span>
                {message.metadata_json.execution_time_ms && (
                  <span style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: '0.68rem', color: 'var(--text-muted)' }}>
                    <Clock size={10} />
                    Executed in {message.metadata_json.execution_time_ms}ms
                  </span>
                )}
              </div>
              <ResultTable
                columns={message.metadata_json.columns || []}
                rows={message.metadata_json.rows}
              />
            </div>
          )}
        </div>

        {/* Timestamp */}
        <span
          style={{
            fontSize: '0.68rem',
            color: 'var(--text-muted)',
            padding: '0 4px',
            marginTop: 2,
          }}
        >
          {formatTime(message.created_at)}
        </span>
      </div>
    </div>
  );
}
