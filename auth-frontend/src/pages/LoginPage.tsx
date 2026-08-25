/**
 * Auth Pivota Login Page.
 *
 * Validates user credentials against the shared Pivota database.
 * On success, redirects to email verification or TOTP home page.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react';
import { authServiceApi } from '../services/api';

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authServiceApi.login(email, password);

      // Store session
      sessionStorage.setItem('auth_pivota_token', response.access_token);
      sessionStorage.setItem('auth_pivota_user_id', response.user_id);
      sessionStorage.setItem('auth_pivota_email', response.email);

      if (response.is_email_verified) {
        // Already verified — go straight to TOTP
        navigate('/home');
      } else {
        // Need email verification first
        navigate('/verify-email');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid credentials. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
      {/* Ambient Background */}
      <div className="ambient-bg">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      <div className="auth-card animate-fade-in">
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <div style={{
            width: 60, height: 60, borderRadius: '50%',
            background: 'linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: 16, boxShadow: '0 0 40px rgba(255,255,255,0.08)',
          }}>
            <Shield size={28} color="#0a0a0a" />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: 6 }}>
            Auth Pivota
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Two-Factor Authentication Service
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="status-error" style={{ marginBottom: 20 }}>
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@company.com"
              required
              className="input-field"
              id="auth-login-email"
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-secondary)', marginBottom: 6, fontWeight: 500 }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
                className="input-field"
                style={{ paddingRight: 44 }}
                id="auth-login-password"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute', right: 16, top: '50%', transform: 'translateY(-50%)',
                  background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 4,
                }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '12px 24px', fontSize: '0.9rem' }}
            id="auth-login-submit"
          >
            {loading ? (
              <><Loader2 size={18} className="animate-spin" /> Signing in...</>
            ) : (
              <>Sign In <ArrowRight size={18} /></>
            )}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 28, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Use your Pivota account credentials
        </p>
      </div>
    </div>
  );
}
