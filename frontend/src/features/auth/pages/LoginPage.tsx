/**
 * Pivota Login Page.
 *
 * Email + password login with animated constellation background,
 * validation, loading states, and redirect on success.
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Compass, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react';
import { authApi } from '../api/authApi';
import { useAuthStore } from '../../../stores/authStore';

export default function LoginPage() {
  const navigate = useNavigate();
  const { setAuth, isAuthenticated } = useAuthStore();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isAuthenticated) navigate('/dashboard');
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authApi.login({ email, password });
      setAuth(response.user, response.access_token, response.refresh_token);

      // Redirect based on 2FA status
      if (response.user.is_2fa_verified) {
        navigate('/dashboard');
      } else {
        navigate('/verify-2fa');
      }
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Invalid credentials. Please try again.';
      setError(msg);
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
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Login Card */}
      <div
        className="animate-fade-in"
        style={{
          width: '100%',
          maxWidth: 440,
          borderRadius: 8,
          border: '1px solid #000000',
          padding: '40px 36px',
          background: '#ffffff',
          position: 'relative',
          zIndex: 10,
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
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
            <Compass size={28} color="white" />
          </div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, marginBottom: 4 }}>
            Welcome to Pivota
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Sign in to navigate your data
          </p>
        </div>

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

          <button
            type="submit"
            disabled={loading}
            className="btn-primary"
            style={{ width: '100%', justifyContent: 'center', padding: '12px 24px', fontSize: '0.9rem', borderRadius: 9999 }}
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" /> Signing in...
              </>
            ) : (
              <>
                Sign In <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Signup Link */}
        <p style={{ textAlign: 'center', marginTop: 24, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Don't have an account?{' '}
          <Link
            to="/signup"
            style={{
              color: '#000000',
              textDecoration: 'none',
              fontWeight: 600,
            }}
          >
            Create one
          </Link>
        </p>

        {/* IAM Login Link */}
        <p style={{ textAlign: 'center', marginTop: 12, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Are you an employee?{' '}
          <Link
            to="/iam/login"
            style={{
              color: '#000000',
              textDecoration: 'none',
              fontWeight: 600,
            }}
          >
            Employee IAM Login
          </Link>
        </p>
      </div>
    </div>
  );
}

function ConstellationBg() {
  return null;
}
