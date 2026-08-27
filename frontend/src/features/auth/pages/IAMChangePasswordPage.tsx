/**
 * Pivota IAM First-Time Password Change Page.
 *
 * Mandatory password change screen for invited employee logins.
 */

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Key, Eye, EyeOff, CheckCircle, Loader2 } from 'lucide-react';
import { authApi } from '../api/authApi';
import { useAuthStore } from '../../../stores/authStore';

export default function IAMChangePasswordPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const [tempPassword, setTempPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const tempToken = sessionStorage.getItem('pivota_iam_temp_token') || '';
  const autofilledTempPass = sessionStorage.getItem('pivota_iam_temp_pass') || '';

  useEffect(() => {
    if (!tempToken) {
      navigate('/iam/login');
    } else if (autofilledTempPass) {
      setTempPassword(autofilledTempPass);
    }
  }, [tempToken, autofilledTempPass, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (newPassword.length < 8) {
      setError('New password must be at least 8 characters long');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const response = await authApi.iamResetPassword(
        {
          temp_password: tempPassword,
          new_password: newPassword,
          confirm_password: confirmPassword,
        },
        tempToken
      );

      setSuccess(true);
      sessionStorage.removeItem('pivota_iam_temp_token');
      sessionStorage.removeItem('pivota_iam_temp_pass');

      // Save auth tokens
      setTimeout(() => {
        setAuth(response.user, response.access_token, response.refresh_token);
        navigate('/dashboard');
      }, 1200);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to change password. Please verify details.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#ffffff',
        padding: '40px 20px',
      }}
    >
      <div
        className="animate-fade-in"
        style={{
          width: '100%',
          maxWidth: 440,
          borderRadius: 8,
          border: '1px solid #000000',
          padding: '40px 36px',
          background: '#ffffff',
        }}
      >
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: 9999,
              background: '#000000',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 16,
            }}
          >
            <Key size={26} color="white" />
          </div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 6 }}>
            Set Permanent Password
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', lineHeight: 1.5 }}>
            This is your first login. Please choose a secure password to activate your account.
          </p>
        </div>

        {/* Success */}
        {success && (
          <div
            style={{
              background: 'var(--status-success-bg)',
              color: 'var(--status-success)',
              padding: '12px 20px',
              borderRadius: 9999,
              fontSize: '0.85rem',
              fontWeight: 600,
              marginBottom: 20,
              textAlign: 'center',
              border: '1px solid var(--status-success)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
            }}
          >
            <CheckCircle size={18} /> Password updated successfully!
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            style={{
              background: 'var(--status-error-bg)',
              color: 'var(--status-error)',
              padding: '10px 20px',
              borderRadius: 9999,
              fontSize: '0.8rem',
              marginBottom: 20,
              border: '1px solid var(--status-error)',
              textAlign: 'center',
            }}
          >
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          {/* Temporary Password */}
          <div style={{ marginBottom: 16 }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.8rem',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: 6,
              }}
            >
              Temporary Password
            </label>
            <input
              type="password"
              value={tempPassword}
              onChange={(e) => setTempPassword(e.target.value)}
              placeholder="Enter the temp password"
              required
              id="iam-change-temp-pass"
              className="input-field"
            />
          </div>

          {/* New Password */}
          <div style={{ marginBottom: 16 }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.8rem',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: 6,
              }}
            >
              New Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Choose a strong password"
                required
                id="iam-change-new-pass"
                className="input-field"
                style={{ paddingRight: 44 }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: 16,
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-muted)',
                  cursor: 'pointer',
                  padding: 4,
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          {/* Confirm New Password */}
          <div style={{ marginBottom: 24 }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.8rem',
                fontWeight: 500,
                color: 'var(--text-secondary)',
                marginBottom: 6,
              }}
            >
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Verify your new password"
              required
              id="iam-change-confirm-pass"
              className="input-field"
            />
          </div>

          <button
            type="submit"
            disabled={loading || success}
            className="btn-primary"
            style={{
              width: '100%',
              justifyContent: 'center',
              padding: '12px 24px',
              fontSize: '0.9rem',
              borderRadius: 9999,
            }}
            id="iam-change-submit"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" /> Updating...
              </>
            ) : (
              'Activate Account'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
