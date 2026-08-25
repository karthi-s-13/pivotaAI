/**
 * Pivota IAM User Login Page.
 *
 * Distinct from standard Pivota login. Asks for:
 * 1. Email
 * 2. IAM User ID (e.g., EMP-1042)
 * 3. Temporary / Permanent Password
 */

import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Shield, Eye, EyeOff, ArrowRight, Loader2 } from 'lucide-react';
import { authApi } from '../api/authApi';
import { useAuthStore } from '../../../stores/authStore';

export default function IAMLoginPage() {
  const navigate = useNavigate();
  const { setAuth, isAuthenticated } = useAuthStore();

  const [email, setEmail] = useState('');
  const [iamId, setIamId] = useState('');
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
      const response = await authApi.iamLogin({
        email,
        iam_id: iamId,
        password,
      });

      if (response.password_change_required && response.temp_token) {
        // Store the temp token and temporary password for reset flow
        sessionStorage.setItem('pivota_iam_temp_token', response.temp_token);
        sessionStorage.setItem('pivota_iam_temp_pass', password);
        navigate('/iam/change-password');
      } else if (response.access_token && response.refresh_token && response.user) {
        setAuth(response.user, response.access_token, response.refresh_token);
        navigate('/dashboard');
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
        {/* Branding */}
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
            <Shield size={26} color="white" />
          </div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, marginBottom: 6 }}>
            IAM User Login
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.82rem' }}>
            Enter your employee credentials to access Pivota
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
          {/* Email */}
          <div style={{ marginBottom: 16 }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.8rem',
                fontWeight: 600,
                color: '#333333',
                marginBottom: 6,
              }}
            >
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              required
              id="iam-login-email"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #d0d0d0',
                borderRadius: 8,
                fontSize: '0.88rem',
                outline: 'none',
              }}
            />
          </div>

          {/* IAM User ID */}
          <div style={{ marginBottom: 16 }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.8rem',
                fontWeight: 600,
                color: '#333333',
                marginBottom: 6,
              }}
            >
              IAM User ID
            </label>
            <input
              type="text"
              value={iamId}
              onChange={(e) => setIamId(e.target.value)}
              placeholder="EMP-1001"
              required
              id="iam-login-id"
              style={{
                width: '100%',
                padding: '12px 16px',
                border: '1px solid #d0d0d0',
                borderRadius: 8,
                fontSize: '0.88rem',
                outline: 'none',
              }}
            />
          </div>

          {/* Password */}
          <div style={{ marginBottom: 24 }}>
            <label
              style={{
                display: 'block',
                fontSize: '0.8rem',
                fontWeight: 600,
                color: '#333333',
                marginBottom: 6,
              }}
            >
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                required
                id="iam-login-password"
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  paddingRight: 44,
                  border: '1px solid #d0d0d0',
                  borderRadius: 8,
                  fontSize: '0.88rem',
                  outline: 'none',
                }}
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
                  color: '#888888',
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
            style={{
              width: '100%',
              justifyContent: 'center',
              padding: '12px 24px',
              fontSize: '0.9rem',
              borderRadius: 9999,
            }}
            id="iam-login-submit"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" /> Logging in...
              </>
            ) : (
              <>
                Sign In <ArrowRight size={18} />
              </>
            )}
          </button>
        </form>

        <p
          style={{
            textAlign: 'center',
            marginTop: 28,
            fontSize: '0.78rem',
            color: 'var(--text-muted)',
          }}
        >
          Are you an Administrator?{' '}
          <Link to="/login" style={{ color: '#000000', fontWeight: 600, textDecoration: 'none' }}>
            Main Admin Login
          </Link>
        </p>
      </div>
    </div>
  );
}
