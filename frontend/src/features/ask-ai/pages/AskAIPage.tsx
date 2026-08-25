import { Sparkles } from 'lucide-react';
export default function AskAIPage() {
  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', textAlign: 'center' }}>
      <div style={{ width: 80, height: 80, borderRadius: 20, background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(139,92,246,0.15))', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }} className="animate-float">
        <Sparkles size={36} style={{ color: '#8b5cf6' }} />
      </div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 8 }} className="gradient-text">Ask Pivota AI</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: 420, lineHeight: 1.6 }}>
        Ask natural language questions about your data landscape. Pivota AI uses retrieval-augmented generation to locate data and explain relationships.
      </p>
      <span className="badge badge-info" style={{ marginTop: 20, fontSize: '0.72rem' }}>Coming Soon</span>
    </div>
  );
}
