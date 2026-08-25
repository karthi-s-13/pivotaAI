/**
 * IAM Management Component.
 *
 * Rendered inside SettingsPage. Displays:
 * 1. IAM User list for organization
 * 2. Form to invite/create a new employee IAM account
 * 3. Send Access Details action (triggers temporary password email generation)
 */

import { useState, useEffect } from 'react';
import { Shield, Plus, Mail, Trash2, Send, CheckCircle, RefreshCw, Loader2 } from 'lucide-react';
import { authApi } from '../../auth/api/authApi';
import type { IAMUser, IAMPolicy } from '../../auth/api/authApi';

export default function IAMManagement() {
  const [users, setUsers] = useState<IAMUser[]>([]);
  const [policies, setPolicies] = useState<IAMPolicy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Form State
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [policyId, setPolicyId] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Status mapping colors
  const statusColors: Record<string, { bg: string; text: string }> = {
    INVITED: { bg: 'rgba(245,158,11,0.1)', text: '#f59e0b' },
    FIRST_LOGIN: { bg: 'rgba(59,130,246,0.1)', text: '#3b82f6' },
    PASSWORD_CHANGE_REQUIRED: { bg: 'rgba(239,68,68,0.1)', text: '#ef4444' },
    ACTIVE: { bg: 'rgba(34,197,94,0.1)', text: '#22c55e' },
  };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    setError('');
    try {
      const [usersData, policiesData] = await Promise.all([
        authApi.getIAMUsers(),
        authApi.getIAMPolicies(),
      ]);
      setUsers(usersData);
      setPolicies(policiesData);
      if (policiesData.length > 0) {
        setPolicyId(policiesData[0].id);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch IAM management data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setSubmitting(true);

    try {
      const newUser = await authApi.createIAMUser({
        full_name: fullName,
        email,
        policy_id: policyId,
      });

      // Update state
      setUsers([...users, newUser]);
      setFullName('');
      setEmail('');
      setSuccess(`IAM User ${newUser.iam_id} created successfully! Don't forget to click "Send Access Details" below to invite them.`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create IAM user');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendDetails = async (userId: string) => {
    setError('');
    setSuccess('');
    
    // Find user name for logs
    const u = users.find(x => x.id === userId);
    if (!u) return;

    try {
      const res = await authApi.sendIAMUserDetails(userId);
      setSuccess(res.message);
      
      // Reload users to show updated invited status
      const updated = await authApi.getIAMUsers();
      setUsers(updated);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send credentials details email');
    }
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this IAM user account? This action cannot be undone.')) return;
    setError('');
    setSuccess('');

    try {
      await authApi.deleteIAMUser(userId);
      setUsers(users.filter((x) => x.id !== userId));
      setSuccess('IAM User account deleted successfully.');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete IAM user');
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '60px 0' }}>
        <Loader2 size={32} className="animate-spin" style={{ color: '#000' }} />
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
      {/* Alert notifications */}
      {error && (
        <div style={{ background: '#fef2f2', border: '1px solid #ef4444', color: '#ef4444', padding: '12px 18px', borderRadius: 8, fontSize: '0.85rem' }}>
          {error}
        </div>
      )}
      {success && (
        <div style={{ background: '#f0fdf4', border: '1px solid #22c55e', color: '#15803d', padding: '12px 18px', borderRadius: 8, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: 8 }}>
          <CheckCircle size={16} /> {success}
        </div>
      )}

      {/* Grid: Create User Form + Policy list */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Create User Card */}
        <div style={{ border: '1px solid #e0e0e0', borderRadius: 8, padding: 24, background: '#ffffff' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Plus size={18} /> Create IAM User Account
          </h2>
          <form onSubmit={handleCreateUser} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#4b5563', marginBottom: 4 }}>Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                required
                style={{ width: '100%', padding: '10px 14px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.85rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#4b5563', marginBottom: 4 }}>Gmail Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="employee@gmail.com"
                required
                style={{ width: '100%', padding: '10px 14px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.85rem', outline: 'none' }}
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: '#4b5563', marginBottom: 4 }}>Access Policy</label>
              <select
                value={policyId}
                onChange={(e) => setPolicyId(e.target.value)}
                style={{ width: '100%', padding: '10px 14px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: '0.85rem', outline: 'none', background: '#fff' }}
              >
                {policies.map((p) => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="btn-primary"
              style={{ padding: '10px 20px', fontSize: '0.82rem', borderRadius: 6, width: 'fit-content', marginTop: 6 }}
            >
              {submitting ? 'Creating...' : 'Create Account'}
            </button>
          </form>
        </div>

        {/* Info Box / Policies List */}
        <div style={{ border: '1px solid #e0e0e0', borderRadius: 8, padding: 24, background: '#f9fafb' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Shield size={18} /> Active Policies & Permissions
          </h2>
          <p style={{ fontSize: '0.78rem', color: '#6b7280', marginBottom: 16 }}>
            Access Policies define what resources and catalog items can be viewed or edited.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {policies.map((p) => (
              <div key={p.id} style={{ borderBottom: '1px solid #e5e7eb', paddingBottom: 10 }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#111827' }}>{p.name}</span>
                <p style={{ fontSize: '0.75rem', color: '#4b5563', marginTop: 2 }}>{p.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* IAM User Accounts Table */}
      <div style={{ border: '1px solid #e0e0e0', borderRadius: 8, background: '#ffffff', overflow: 'hidden' }}>
        <div style={{ padding: '18px 24px', borderBottom: '1px solid #e5e7eb', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>IAM User Accounts</h3>
          <button onClick={fetchData} className="btn-secondary" style={{ padding: '6px 12px', fontSize: '0.75rem', borderRadius: 6 }}>
            <RefreshCw size={12} /> Refresh
          </button>
        </div>
        
        {users.length === 0 ? (
          <div style={{ padding: '40px 0', textAlign: 'center', color: '#6b7280', fontSize: '0.85rem' }}>
            No IAM User accounts found. Use the form above to invite employees.
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.82rem' }}>
            <thead>
              <tr style={{ background: '#f9fafb', borderBottom: '1px solid #e5e7eb', color: '#374151' }}>
                <th style={{ padding: '12px 24px', fontWeight: 600 }}>Employee</th>
                <th style={{ padding: '12px 24px', fontWeight: 600 }}>IAM User ID</th>
                <th style={{ padding: '12px 24px', fontWeight: 600 }}>Gmail</th>
                <th style={{ padding: '12px 24px', fontWeight: 600 }}>Policy</th>
                <th style={{ padding: '12px 24px', fontWeight: 600 }}>Status</th>
                <th style={{ padding: '12px 24px', fontWeight: 600, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const status = statusColors[u.status] || { bg: '#eee', text: '#666' };
                return (
                  <tr key={u.id} style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <td style={{ padding: '14px 24px', fontWeight: 600, color: '#111827' }}>{u.full_name}</td>
                    <td style={{ padding: '14px 24px', fontFamily: 'monospace' }}>{u.iam_id}</td>
                    <td style={{ padding: '14px 24px', color: '#4b5563' }}>{u.email}</td>
                    <td style={{ padding: '14px 24px' }}>
                      <span style={{ background: '#f3f4f6', color: '#1f2937', padding: '2px 8px', borderRadius: 9999, fontSize: '0.72rem', fontWeight: 500 }}>
                        {u.policy_name}
                      </span>
                    </td>
                    <td style={{ padding: '14px 24px' }}>
                      <span style={{ background: status.bg, color: status.text, padding: '2px 8px', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.02em' }}>
                        {u.status}
                      </span>
                    </td>
                    <td style={{ padding: '14px 24px', textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: 8 }}>
                        <button
                          onClick={() => handleSendDetails(u.id)}
                          title="Send access credentials email invitation"
                          style={{
                            display: 'inline-flex', alignItems: 'center', gap: 4, padding: '6px 12px',
                            background: '#000000', color: '#ffffff', border: 'none', borderRadius: 6,
                            cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600, transition: 'opacity 0.2s'
                          }}
                          onMouseEnter={e => { e.currentTarget.style.opacity = '0.9'; }}
                          onMouseLeave={e => { e.currentTarget.style.opacity = '1'; }}
                        >
                          <Send size={12} /> Send Details
                        </button>
                        <button
                          onClick={() => handleDeleteUser(u.id)}
                          title="Delete employee access account"
                          style={{
                            display: 'inline-flex', alignItems: 'center', padding: '6px',
                            background: '#fef2f2', color: '#ef4444', border: '1px solid rgba(239,68,68,0.2)',
                            borderRadius: 6, cursor: 'pointer'
                          }}
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
