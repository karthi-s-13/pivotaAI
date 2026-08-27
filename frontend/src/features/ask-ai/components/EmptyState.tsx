import { Sparkles, Database, Code, Compass, HelpCircle } from 'lucide-react';
import { useAIStore } from '../stores/aiStore';

interface EmptyStateProps {
  onPromptClick: (prompt: string) => void;
}

export default function EmptyState({ onPromptClick }: EmptyStateProps) {
  const { selectedContext } = useAIStore();

  const getSuggestedPrompts = () => {
    if (!selectedContext) return [];
    const dbName = selectedContext.database;
    const provider = selectedContext.provider.toUpperCase();

    const basePrompts = [
      {
        text: `Explain the ${dbName} database structure`,
        desc: "Get an overview of tables and schemas",
        icon: <Compass size={16} />
      },
      {
        text: "What tables are available in this schema?",
        desc: "List discovered objects in active scope",
        icon: <Database size={16} />
      }
    ];

    if (provider === 'MONGODB') {
      return [
        ...basePrompts,
        {
          text: "Show me the latest 10 documents from my collection",
          desc: "Inspect raw collection records",
          icon: <Code size={16} />
        },
        {
          text: "Write a Mongo query to filter items",
          desc: "Generate aggregate pipeline",
          icon: <Sparkles size={16} />
        }
      ];
    }

    return [
      ...basePrompts,
      {
        text: "How many total records do we have?",
        desc: "Run aggregate counts across datasets",
        icon: <HelpCircle size={16} />
      },
      {
        text: "Write a SQL query to find duplicate emails",
        desc: "Create read-only SELECT filters",
        icon: <Code size={16} />
      }
    ];
  };

  const prompts = getSuggestedPrompts();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        flex: 1,
        maxWidth: '720px',
        margin: '0 auto',
        padding: '40px 24px',
        textAlign: 'center',
      }}
      className="animate-fade-in"
    >
      {/* Gemini Glowing Sphere Logo */}
      <div style={{ position: 'relative', marginBottom: 28 }}>
        <div
          style={{
            width: 72,
            height: 72,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #4285f4, #9b51e0, #e051a8, #3b82f6)',
            backgroundSize: '300% 300%',
            animation: 'gemini-gradient 8s ease infinite, pulse 3s ease-in-out infinite',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 24px rgba(155, 81, 224, 0.4)',
          }}
        >
          <Sparkles size={32} color="white" />
        </div>
        {/* Secondary decorative orbit rings */}
        <div
          style={{
            position: 'absolute',
            top: -6,
            left: -6,
            right: -6,
            bottom: -6,
            borderRadius: '50%',
            border: '1px solid rgba(155, 81, 224, 0.15)',
            animation: 'spin 12s linear infinite',
            pointerEvents: 'none',
          }}
        />
      </div>

      <h1
        style={{
          fontSize: '1.9rem',
          fontWeight: 800,
          marginBottom: 10,
          background: 'linear-gradient(90deg, #4285f4, #9b51e0, #e051a8)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '-0.02em',
        }}
      >
        How can I help you today?
      </h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.6, maxWidth: 520, margin: '0 auto 36px', fontWeight: 500 }}>
        Ask natural questions to analyze database schemas, generate read-only SQL, or visualize result tables in real-time.
      </p>

      {selectedContext ? (
        <div style={{ width: '100%' }}>
          <div style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', display: 'grid', gap: '12px' }}>
            {prompts.map((p, idx) => (
              <button
                key={idx}
                onClick={() => onPromptClick(p.text)}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '12px',
                  padding: '16px',
                  borderRadius: '12px',
                  border: '1px solid var(--border-default)',
                  background: 'var(--bg-surface)',
                  color: 'var(--text-primary)',
                  fontSize: '0.85rem',
                  textAlign: 'left',
                  cursor: 'pointer',
                  transition: 'all var(--transition-base)',
                  boxShadow: 'none',
                }}
                onMouseEnter={e => {
                  e.currentTarget.style.borderColor = '#9b51e0';
                  e.currentTarget.style.background = 'var(--bg-elevated)';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={e => {
                  e.currentTarget.style.borderColor = 'var(--border-default)';
                  e.currentTarget.style.background = 'var(--bg-surface)';
                  e.currentTarget.style.transform = 'none';
                }}
              >
                <div
                  style={{
                    padding: '8px',
                    borderRadius: '8px',
                    background: 'var(--bg-elevated)',
                    color: 'var(--text-secondary)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  {p.icon}
                </div>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>{p.text}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{p.desc}</div>
                </div>
              </button>
            ))}
          </div>
        </div>
      ) : (
        <div
          style={{
            padding: '16px 20px',
            borderRadius: '12px',
            background: 'var(--status-warning-bg)',
            border: '1px solid var(--status-warning)',
            color: 'var(--status-warning)',
            fontSize: '0.85rem',
            fontWeight: 500,
            maxWidth: 480,
            margin: '0 auto',
          }}
        >
          ⚠️ Please select a database connection context in the top-right menu to enable the AI capabilities.
        </div>
      )}
    </div>
  );
}
