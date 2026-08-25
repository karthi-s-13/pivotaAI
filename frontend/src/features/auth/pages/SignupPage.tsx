/**
 * Pivota Signup Page.
 *
 * Full registration form: name, email, organization, password.
 * Creates user + organization, then redirects to login.
 */

import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Compass, Eye, EyeOff, ArrowRight, Loader2, CheckCircle } from 'lucide-react';
import { authApi } from '../api/authApi';
import { useAuthStore } from '../../../stores/authStore';

export default function SignupPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const [form, setForm] = useState({
    full_name: '',
    email: '',
    organization_name: '',
    password: '',
    confirmPassword: '',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const updateField = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
  };

  const passwordStrength = (): { label: string; color: string; percent: number } => {
    const pw = form.password;
    if (pw.length === 0) return { label: '', color: '', percent: 0 };
    if (pw.length < 8) return { label: 'Too short', color: 'var(--status-error)', percent: 20 };
    let score = 0;
    if (/[a-z]/.test(pw)) score++;
    if (/[A-Z]/.test(pw)) score++;
    if (/[0-9]/.test(pw)) score++;
    if (/[^a-zA-Z0-9]/.test(pw)) score++;
    if (pw.length >= 12) score++;
    if (score <= 2) return { label: 'Weak', color: 'var(--status-warning)', percent: 40 };
    if (score <= 3) return { label: 'Medium', color: 'var(--status-info)', percent: 65 };
    return { label: 'Strong', color: 'var(--status-success)', percent: 100 };
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    try {
      const response = await authApi.signup({
        full_name: form.full_name,
        email: form.email,
        password: form.password,
        organization_name: form.organization_name,
      });
      setAuth(response.user, response.access_token, response.refresh_token);
      navigate('/verify-2fa');
    } catch (err: any) {
      const msg = err.response?.data?.detail || 'Registration failed. Please try again.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const pw = passwordStrength();

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
        padding: '40px 20px',
      }}
    >
      {/* Signup Card */}
      <div
        className="animate-fade-in"
        style={{
          width: '100%',
          maxWidth: 480,
          borderRadius: 8,
          border: '1px solid #000000',
          padding: '36px',
          background: '#ffffff',
          position: 'relative',
          zIndex: 10,
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 28 }}>
          <div
            style={{
              width: 52,
              height: 52,
              borderRadius: 9999,
              background: '#000000',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: 14,
            }}
          >
            <Compass size={26} color="white" />
          </div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 4 }}>
            Create your account
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            Start navigating your data landscape
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
              marginBottom: 18,
              border: '1px solid var(--status-error)',
              textAlign: 'center',
            }}
          >
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 14 }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: 5, fontWeight: 500 }}>
                Full Name
              </label>
              <input
                type="text"
                value={form.full_name}
                onChange={(e) => updateField('full_name', e.target.value)}
                placeholder="John Doe"
                required
                className="input-field"
              />
            </div>
            <div>
              <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: 5, fontWeight: 500 }}>
                Organization
              </label>
              <input
                type="text"
                value={form.organization_name}
                onChange={(e) => updateField('organization_name', e.target.value)}
                placeholder="Acme Inc."
                required
                className="input-field"
              />
            </div>
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: 5, fontWeight: 500 }}>
              Email
            </label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => updateField('email', e.target.value)}
              placeholder="you@company.com"
              required
              className="input-field"
            />
          </div>

          <div style={{ marginBottom: 14 }}>
            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: 5, fontWeight: 500 }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                value={form.password}
                onChange={(e) => updateField('password', e.target.value)}
                placeholder="Min. 8 characters"
                required
                minLength={8}
                className="input-field"
                style={{ paddingRight: 44 }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{ position: 'absolute', right: 16, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: 4 }}
              >
                {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
            {/* Password strength */}
            {form.password && (
              <div style={{ marginTop: 6 }}>
                <div style={{ height: 3, borderRadius: 9999, background: 'var(--bg-elevated)', overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${pw.percent}%`, background: pw.color, borderRadius: 9999, transition: 'all 0.3s ease' }} />
                </div>
                <p style={{ fontSize: '0.68rem', color: pw.color, marginTop: 3 }}>{pw.label}</p>
              </div>
            )}
          </div>

          <div style={{ marginBottom: 22 }}>
            <label style={{ display: 'block', fontSize: '0.78rem', color: 'var(--text-secondary)', marginBottom: 5, fontWeight: 500 }}>
              Confirm Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                value={form.confirmPassword}
                onChange={(e) => updateField('confirmPassword', e.target.value)}
                placeholder="••••••••"
                required
                className="input-field"
                style={{ paddingRight: 44 }}
              />
              {form.confirmPassword && form.password === form.confirmPassword && (
                <CheckCircle size={16} style={{ position: 'absolute', right: 16, top: '50%', transform: 'translateY(-50%)', color: 'var(--status-success)' }} />
              )}
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
                <Loader2 size={18} className="animate-spin" /> Creating account...
              </>
            ) : (
              <>
                Create Account <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        {/* Login Link */}
        <p style={{ textAlign: 'center', marginTop: 22, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: '#000000', textDecoration: 'none', fontWeight: 600 }}>
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
