import { useEffect } from 'react';
import { AlertTriangle, ServerCrash, RefreshCw } from 'lucide-react';

import ChatSidebar from '../components/ChatSidebar';
import ChatHeader from '../components/ChatHeader';
import ChatMessages from '../components/ChatMessages';
import ChatInput from '../components/ChatInput';
import EmptyState from '../components/EmptyState';

import { useAIStore } from '../stores/aiStore';
import { useChat } from '../hooks/useChat';

export default function AskAIPage() {
  const {
    messages,
    fetchConversations,
    fetchContexts,
    checkHealth,
    health,
    isInitialLoading,
  } = useAIStore();

  const { sendMessage, stopStreaming } = useChat();

  useEffect(() => {
    // Initial fetch of contexts, conversation histories, and model health
    const initializePage = async () => {
      await Promise.all([
        fetchContexts(),
        fetchConversations(),
        checkHealth(),
      ]);
    };
    initializePage();
  }, []);

  const handlePromptClick = (prompt: string) => {
    sendMessage(prompt);
  };

  // 1. Loading State
  if (isInitialLoading) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '80vh', gap: 16 }}>
        <RefreshCw size={36} className="animate-spin" style={{ color: 'var(--text-primary)' }} />
        <span style={{ fontSize: '0.88rem', fontWeight: 600, color: 'var(--text-secondary)' }}>
          Loading Pivota AI Workspace...
        </span>
      </div>
    );
  }

  // 2. Offline / Unavailable Ollama health block
  const isOffline = health?.status === 'unavailable';
  if (isOffline) {
    return (
      <div
        className="animate-fade-in"
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '70vh',
          textAlign: 'center',
          maxWidth: 480,
          margin: '0 auto',
          padding: '0 24px',
        }}
      >
        <div style={{ width: 80, height: 80, borderRadius: 20, background: 'var(--status-error-bg)', border: '1px solid var(--status-error)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
          <ServerCrash size={36} style={{ color: 'var(--status-error)' }} />
        </div>
        <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 8, color: 'var(--text-primary)' }}>
          Pivota AI is Offline
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.88rem', lineHeight: 1.6, marginBottom: 24 }}>
          Pivota AI is currently unavailable because the local AI model service (Ollama) cannot be reached at <b>{health?.llm_model ? 'http://localhost:11434' : 'configured URL'}</b>.
        </p>
        <div style={{ padding: '12px 16px', borderRadius: '8px', background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', width: '100%', fontSize: '0.8rem', textAlign: 'left', marginBottom: 20 }}>
          <div style={{ fontWeight: 700, marginBottom: 6 }}>Suggested Troubleshooting:</div>
          <ol style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: 4 }}>
            <li>Verify Ollama is installed and running locally.</li>
            <li>Ensure the <b>llama3.2:3b</b> model is pulled: <code>ollama pull llama3.2:3b</code></li>
            <li>Refresh this browser tab once Ollama starts.</li>
          </ol>
        </div>
        <button
          onClick={() => checkHealth()}
          style={{
            padding: '8px 20px',
            borderRadius: '9999px',
            background: '#000000',
            color: '#ffffff',
            border: 'none',
            fontSize: '0.8rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          Check Service Status Again
        </button>
      </div>
    );
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: 'calc(100vh - var(--topbar-height))', // Full-bleed height matching the negative margins
        margin: '-28px', // Break out of app shell main padding
        background: 'var(--bg-app)',
        overflow: 'hidden',
      }}
    >
      <ChatHeader />

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Sidebar history list */}
        <ChatSidebar />

        {/* Center Panel chat window */}
        <div
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            position: 'relative',
            background: 'var(--bg-app)',
            overflow: 'hidden',
          }}
        >
          {/* Degraded service notification strip */}
          {health?.status === 'degraded' && (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 8,
                padding: '6px 16px',
                background: 'var(--status-warning-bg)',
                borderBottom: '1px solid var(--status-warning)',
                color: 'var(--status-warning)',
                fontSize: '0.75rem',
                fontWeight: 600,
                zIndex: 10,
              }}
            >
              <AlertTriangle size={14} />
              <span>{health.message || 'AI service degraded. Vector index or embedding offline.'}</span>
            </div>
          )}

          {/* Messages list feed */}
          {messages.length === 0 ? (
            <EmptyState onPromptClick={handlePromptClick} />
          ) : (
            <ChatMessages messages={messages} />
          )}

          {/* Bottom input area */}
          <div
            style={{
              padding: '16px 24px 24px',
              maxWidth: '840px',
              width: '100%',
              margin: '0 auto',
            }}
          >
            <ChatInput onSend={sendMessage} onStop={stopStreaming} />
            <p style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: 8 }}>
              Pivota AI executes read-only queries. Review results for accuracy.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
