/**
 * IAM Management Component.
 *
 * Rendered inside SettingsPage. Displays:
 * 1. IAM User list for organization
 * 2. Form to invite/create a new employee IAM account
 * 3. Send Access Details action (triggers temporary password email generation)
 */

import { useState, useEffect } from 'react';
import { Shield, Plus, Trash2, Send, CheckCircle, RefreshCw, Loader2 } from 'lucide-react';
import { authApi } from '../../auth/api/authApi';
import type { IAMUser, IAMPolicy } from '../../auth/api/authApi';
import './iam.css';

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

  // Status mapping — mapped onto the shared semantic status tokens:
  // INVITED = pending action (warning), FIRST_LOGIN = neutral in-progress state (info/black),
  // PASSWORD_CHANGE_REQUIRED = blocking, must resolve before use (error), ACTIVE = healthy (success)
  const statusColors: Record<string, { bg: string; text: string }> = {
    INVITED: { bg: 'var(--status-warning-bg)', text: 'var(--status-warning)' },
    FIRST_LOGIN: { bg: 'var(--status-info-bg)', text: 'var(--status-info)' },
    PASSWORD_CHANGE_REQUIRED: { bg: 'var(--status-error-bg)', text: 'var(--status-error)' },
    ACTIVE: { bg: 'var(--status-success-bg)', text: 'var(--status-success)' },
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
        <Loader2 size={32} className="animate-spin" style={{ color: 'var(--brand-primary)' }} />
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 32 }}>
      {/* Alert notifications */}
      {error && (
        <div style={{ background: 'var(--status-error-bg)', border: '1px solid var(--status-error)', color: 'var(--status-error)', padding: '12px 20px', borderRadius: 9999, fontSize: '0.85rem' }}>
          {error}
        </div>
      )}
      {success && (
        <div style={{ background: 'var(--status-success-bg)', border: '1px solid var(--status-success)', color: 'var(--status-success)', padding: '12px 20px', borderRadius: 9999, fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: 8 }}>
          <CheckCircle size={16} /> {success}
        </div>
      )}

      {/* Grid: Create User Form + Policy list */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Create User Card */}
        <div style={{ border: '1px solid var(--border-default)', borderRadius: 8, padding: 24, background: 'var(--bg-surface)' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 16, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Plus size={18} /> Create IAM User Account
          </h2>
          <form onSubmit={handleCreateUser} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>Full Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="John Doe"
                required
                className="input-field"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>Gmail Address</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="employee@gmail.com"
                required
                className="input-field"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 4 }}>Access Policy</label>
              <select
                value={policyId}
                onChange={(e) => setPolicyId(e.target.value)}
                className="input-field"
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
              style={{ padding: '10px 20px', fontSize: '0.82rem', width: 'fit-content', marginTop: 6 }}
            >
              {submitting ? 'Creating...' : 'Create Account'}
            </button>
          </form>
        </div>

        {/* Info Box / Policies List */}
        <div style={{ border: '1px solid var(--border-default)', borderRadius: 8, padding: 24, background: 'var(--bg-elevated)' }}>
          <h2 style={{ fontSize: '1.05rem', fontWeight: 700, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Shield size={18} /> Active Policies & Permissions
          </h2>
          <p style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginBottom: 16 }}>
            Access Policies define what resources and catalog items can be viewed or edited.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {policies.map((p) => (
              <div key={p.id} style={{ borderBottom: '1px solid var(--border-default)', paddingBottom: 10 }}>
                <span style={{ fontSize: '0.82rem', fontWeight: 700, color: 'var(--text-primary)' }}>{p.name}</span>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: 2 }}>{p.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* IAM User Accounts Table */}
      <div className="iam-table-wrap">
        <div style={{ padding: '18px 24px', borderBottom: '1px solid var(--border-default)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 700 }}>IAM User Accounts</h3>
          <button onClick={fetchData} className="btn-ghost" style={{ padding: '6px 16px', fontSize: '0.75rem' }}>
            <RefreshCw size={12} /> Refresh
          </button>
        </div>

        {users.length === 0 ? (
          <div style={{ padding: '40px 0', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            No IAM User accounts found. Use the form above to invite employees.
          </div>
        ) : (
          <table className="iam-table">
            <thead>
              <tr>
                <th>Employee</th>
                <th>IAM User ID</th>
                <th>Gmail</th>
                <th>Policy</th>
                <th>Status</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => {
                const status = statusColors[u.status] || { bg: 'var(--bg-elevated)', text: 'var(--text-muted)' };
                return (
                  <tr key={u.id}>
                    <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{u.full_name}</td>
                    <td className="mono" style={{ color: 'var(--text-secondary)' }}>{u.iam_id}</td>
                    <td style={{ color: 'var(--text-secondary)' }}>{u.email}</td>
                    <td>
                      <span style={{ background: 'var(--bg-elevated)', color: 'var(--text-primary)', padding: '3px 12px', borderRadius: 9999, fontSize: '0.72rem', fontWeight: 500, border: '1px solid var(--border-default)' }}>
                        {u.policy_name}
                      </span>
                    </td>
                    <td>
                      <span style={{ background: status.bg, color: status.text, padding: '3px 12px', borderRadius: 9999, fontSize: '0.7rem', fontWeight: 600, letterSpacing: '0.02em', border: `1px solid ${status.text}` }}>
                        {u.status}
                      </span>
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: 8 }}>
                        <button
                          onClick={() => handleSendDetails(u.id)}
                          title="Send access credentials email invitation"
                          className="btn-primary"
                          style={{ padding: '6px 16px', fontSize: '0.75rem', gap: 4 }}
                        >
                          <Send size={12} /> Send Details
                        </button>
                        <button
                          onClick={() => handleDeleteUser(u.id)}
                          title="Delete employee access account"
                          style={{
                            display: 'inline-flex', alignItems: 'center', justifyContent: 'center', padding: '6px 10px',
                            background: 'var(--status-error-bg)', color: 'var(--status-error)', border: '1px solid var(--status-error)',
                            borderRadius: 9999, cursor: 'pointer'
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
