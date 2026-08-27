/**
 * Pivota Settings Page.
 *
 * Provides Profile settings and IAM User Management tabs.
 */

import { useState } from 'react';
import { Settings as SettingsIcon, User as UserIcon, Shield } from 'lucide-react';
import { useAuthStore } from '../../../stores/authStore';
import IAMManagement from '../components/IAMManagement';

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'profile' | 'iam'>('profile');

  // Verify if they have administrative permissions to view IAM Management
  const isProfileOnly = user?.is_iam && !user?.permissions?.manage_iam_users;

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      {/* Header */}
      <div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, display: 'flex', alignItems: 'center', gap: 10 }}>
          <SettingsIcon size={24} /> Settings
        </h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', marginTop: 4 }}>
          Manage your personal profile, organization preferences, and employee access controls.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, borderBottom: '1px solid var(--border-default)', paddingBottom: 1 }}>
        <button
          onClick={() => setActiveTab('profile')}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 8,
            padding: '10px 18px',
            border: 'none',
            background: 'none',
            fontSize: '0.85rem',
            fontWeight: 600,
            cursor: 'pointer',
            color: activeTab === 'profile' ? 'var(--text-primary)' : 'var(--text-muted)',
            borderBottom: activeTab === 'profile' ? '2px solid var(--brand-primary)' : '2px solid transparent',
            transition: 'all 0.2s',
          }}
        >
          <UserIcon size={16} /> My Profile
        </button>

        {!isProfileOnly && (
          <button
            onClick={() => setActiveTab('iam')}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 8,
              padding: '10px 18px',
              border: 'none',
              background: 'none',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              color: activeTab === 'iam' ? 'var(--text-primary)' : 'var(--text-muted)',
              borderBottom: activeTab === 'iam' ? '2px solid var(--brand-primary)' : '2px solid transparent',
              transition: 'all 0.2s',
            }}
          >
            <Shield size={16} /> IAM Access Management
          </button>
        )}
      </div>

      {/* Tab Content */}
      <div style={{ marginTop: 8 }}>
        {activeTab === 'profile' && (
          <div style={{ border: '1px solid var(--border-default)', borderRadius: 8, padding: 32, background: 'var(--bg-surface)', textAlign: 'center' }}>
            <div style={{ width: 64, height: 64, borderRadius: '50%', background: 'var(--bg-elevated)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 16 }}>
              <UserIcon size={28} style={{ color: 'var(--text-disabled)' }} />
            </div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: 6 }}>{user?.full_name}</h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: 4 }}>{user?.email}</p>
            <span style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)', padding: '3px 12px', borderRadius: 9999, fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', border: '1px solid var(--border-default)' }}>
              {user?.role === 'iam' ? 'IAM User' : 'Admin'}
            </span>
          </div>
        )}

        {activeTab === 'iam' && !isProfileOnly && <IAMManagement />}
      </div>
    </div>
  );
}
