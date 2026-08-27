import { FileText } from 'lucide-react';
export default function AuditLogsPage() {
  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', textAlign: 'center' }}>
      <div style={{ width: 80, height: 80, borderRadius: 20, background: 'var(--bg-elevated)', border: '1px solid var(--border-default)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
        <FileText size={36} style={{ color: 'var(--text-primary)' }} />
      </div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 8, color: 'var(--text-primary)' }}>Audit Logs</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: 420, lineHeight: 1.6 }}>
        Track all system activity with detailed audit trails. Filter by user, action type, resource, and time range for full traceability.
      </p>
      <span className="badge badge-info" style={{ marginTop: 20, fontSize: '0.72rem' }}>Coming Soon</span>
    </div>
  );
}
