/**
 * Pivota 2FA Verification Page.
 *
 * After signup, the user is redirected here. Shows:
 * 1. A link to Auth Pivota (localhost:3001) to get the 6-digit code
 * 2. Six digit-input boxes for entering the TOTP code
 * 3. On success, redirects to dashboard
 */

import { useState, useRef, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, ArrowRight, Loader2, ExternalLink, CheckCircle } from 'lucide-react';
import { authApi } from '../api/authApi';
import { useAuthStore } from '../../../stores/authStore';

export default function Verify2FAPage() {
  const navigate = useNavigate();
  const { isAuthenticated, logout } = useAuthStore();
  const [otp, setOtp] = useState<string[]>(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    if (!isAuthenticated) navigate('/login');
  }, [isAuthenticated, navigate]);

  const handleBackToSignIn = async (e: React.MouseEvent) => {
    e.preventDefault();
    await logout();
    navigate('/login');
  };

  const handleChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    const newOtp = [...otp];
    for (let i = 0; i < pasted.length; i++) {
      newOtp[i] = pasted[i];
    }
    setOtp(newOtp);
    const nextIndex = Math.min(pasted.length, 5);
    inputRefs.current[nextIndex]?.focus();
  };

  const handleVerify = async () => {
    const code = otp.join('');
    if (code.length !== 6) {
      setError('Please enter the complete 6-digit code');
      return;
    }

    setLoading(true);
    setError('');
    try {
      await authApi.verify2FA(code);
      setSuccess(true);
      // Update local auth state
      const updatedUser = await authApi.getMe();
      const token = localStorage.getItem('pivota_access_token') || '';
      const refreshToken = localStorage.getItem('pivota_refresh_token') || '';
      useAuthStore.getState().setAuth(updatedUser, token, refreshToken);
      setTimeout(() => navigate('/dashboard'), 1000);
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid code. Please try again.';
      setError(msg);
      setOtp(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  // Auto-submit when all digits entered
  useEffect(() => {
    if (otp.every((d) => d !== '')) {
      handleVerify();
    }
  }, [otp]);

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
          maxWidth: 480,
          borderRadius: 8,
          border: '1px solid #000000',
          padding: '36px',
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
            <Shield size={28} color="white" />
          </div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 6 }}>
            Two-Factor Authentication
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem', lineHeight: 1.5 }}>
            Complete verification to access your Pivota dashboard
          </p>
        </div>

        {/* Success State */}
        {success && (
          <div
            style={{
              background: 'var(--status-success-bg)',
              color: 'var(--status-success)',
              padding: '14px 20px',
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
            <CheckCircle size={18} /> Verified! Redirecting to dashboard...
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
              marginBottom: 18,
              border: '1px solid var(--status-error)',
              textAlign: 'center',
            }}
          >
            {error}
          </div>
        )}

        {/* Step 1: Open Auth Pivota */}
        <div
          style={{
            background: 'var(--bg-elevated)',
            borderRadius: 8,
            padding: '16px 20px',
            marginBottom: 24,
            border: '1px solid var(--border-default)',
          }}
        >
          <p style={{ fontSize: '0.82rem', color: 'var(--text-primary)', marginBottom: 8, fontWeight: 600 }}>
            Step 1: Get your authentication code
          </p>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: 12, lineHeight: 1.5 }}>
            Open Auth Pivota, sign in with your credentials, verify your email, then copy the 6-digit code shown on screen.
          </p>
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
            style={{ padding: '8px 16px', fontSize: '0.8rem' }}
            id="pivota-auth-link"
          >
            <Shield size={14} /> Open Auth Pivota <ExternalLink size={12} />
          </a>
        </div>

        {/* Step 2: Enter Code */}
        <p style={{ fontSize: '0.82rem', color: 'var(--text-primary)', marginBottom: 12, fontWeight: 600 }}>
          Step 2: Enter the 6-digit code
        </p>

        <div
          style={{ display: 'flex', gap: 8, justifyContent: 'center', marginBottom: 24 }}
          onPaste={handlePaste}
        >
          {otp.map((digit, index) => (
            <input
              key={index}
              ref={(el) => { inputRefs.current[index] = el; }}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={digit}
              onChange={(e) => handleChange(index, e.target.value)}
              onKeyDown={(e) => handleKeyDown(index, e)}
              id={`pivota-2fa-digit-${index}`}
              style={{
                width: 52,
                height: 56,
                textAlign: 'center',
                fontSize: '1.4rem',
                fontWeight: 700,
                fontFamily: "'JetBrains Mono', monospace",
                background: '#ffffff',
                border: `1px solid ${digit ? 'var(--border-default)' : 'var(--text-disabled)'}`,
                borderRadius: 9999,
                color: 'var(--text-primary)',
                outline: 'none',
                transition: 'all var(--transition-fast)',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = 'var(--border-default)';
                e.target.style.boxShadow = '0 0 0 2px rgba(0, 0, 0, 0.05)';
              }}
              onBlur={(e) => {
                e.target.style.borderColor = digit ? 'var(--border-default)' : 'var(--text-disabled)';
                e.target.style.boxShadow = 'none';
              }}
            />
          ))}
        </div>

        <button
          onClick={handleVerify}
          disabled={loading || otp.some((d) => d === '') || success}
          className="btn-primary"
          style={{
            width: '100%',
            justifyContent: 'center',
            padding: '12px 24px',
            fontSize: '0.9rem',
            borderRadius: 9999,
          }}
          id="pivota-verify-2fa-submit"
        >
          {loading ? (
            <>
              <Loader2 size={18} className="animate-spin" /> Verifying...
            </>
          ) : (
            <>
              Verify & Continue <ArrowRight size={18} />
            </>
          )}
        </button>

        {/* Back to Login */}
        <p style={{ textAlign: 'center', marginTop: 22, fontSize: '0.78rem', color: 'var(--text-muted)' }}>
          <a
            href="/login"
            onClick={handleBackToSignIn}
            style={{ color: '#000000', textDecoration: 'none', fontWeight: 500, cursor: 'pointer' }}
          >
            ← Back to Sign In
          </a>
        </p>
      </div>
    </div>
  );
}
