import { Bell } from 'lucide-react';
export default function AlertsPage() {
  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', textAlign: 'center' }}>
      <div style={{ width: 80, height: 80, borderRadius: 20, background: 'rgba(245,158,11,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }} className="animate-float">
        <Bell size={36} style={{ color: '#f59e0b' }} />
      </div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 8 }} className="gradient-text">Alerts</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: 420, lineHeight: 1.6 }}>
        Monitor connection failures, sync issues, metadata drift, and credential expirations. Stay informed about your data infrastructure health.
      </p>
      <span className="badge badge-info" style={{ marginTop: 20, fontSize: '0.72rem' }}>Coming Soon</span>
    </div>
  );
}
