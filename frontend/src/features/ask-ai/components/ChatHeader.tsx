import { Sparkles } from 'lucide-react';
import DataContextSelector from './DataContextSelector';
import { useAIStore } from '../stores/aiStore';

export default function ChatHeader() {
  const { selectedContext } = useAIStore();

  return (
    <header
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        height: 'var(--topbar-height)',
        padding: '0 24px',
        borderBottom: '1px solid var(--border-default)',
        background: 'var(--bg-surface)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <div
          style={{
            width: 32,
            height: 32,
            borderRadius: 8,
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-default)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Sparkles size={16} style={{ color: 'var(--text-primary)' }} />
        </div>
        <div>
          <h2 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-primary)' }}>Pivota AI</h2>
          {selectedContext && (
            <p style={{ fontSize: '0.68rem', color: 'var(--text-muted)' }}>
              Active Database: <span style={{ fontWeight: 600, color: 'var(--text-secondary)' }}>{selectedContext.database}</span>
            </p>
          )}
        </div>
      </div>

      <DataContextSelector />
    </header>
  );
}
