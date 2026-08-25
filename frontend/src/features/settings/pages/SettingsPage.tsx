import { Settings } from 'lucide-react';
export default function SettingsPage() {
  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '60vh', textAlign: 'center' }}>
      <div style={{ width: 80, height: 80, borderRadius: 20, background: 'rgba(148,163,184,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }} className="animate-float">
        <Settings size={36} style={{ color: '#94a3b8' }} />
      </div>
      <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 8 }} className="gradient-text">Settings</h1>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', maxWidth: 420, lineHeight: 1.6 }}>
        Manage your profile, organization settings, users, roles & permissions, security policies, AI configuration, and preferences.
      </p>
      <span className="badge badge-info" style={{ marginTop: 20, fontSize: '0.72rem' }}>Coming Soon</span>
    </div>
  );
}
