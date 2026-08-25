/**
 * Auth Pivota Home Page — TOTP Code Display.
 *
 * Shows a large 6-digit code that rotates every 30 seconds,
 * with a circular countdown timer and smooth transitions.
 */

import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, Copy, Check, LogOut } from 'lucide-react';
import { authServiceApi } from '../services/api';

export default function HomePage() {
  const navigate = useNavigate();
  const email = sessionStorage.getItem('auth_pivota_email') || '';

  const [code, setCode] = useState('------');
  const [remaining, setRemaining] = useState(30);
  const [copied, setCopied] = useState(false);
  const [transitioning, setTransitioning] = useState(false);

  const fetchCode = useCallback(async () => {
    try {
      const res = await authServiceApi.getCurrentCode();
      if (res.code !== code && code !== '------') {
        // Animate code transition
        setTransitioning(true);
        setTimeout(() => {
          setCode(res.code);
          setTransitioning(false);
        }, 300);
      } else {
        setCode(res.code);
      }
      setRemaining(res.remaining_seconds);
    } catch (err: any) {
      if (err.response?.status === 401) {
        navigate('/login');
      }
    }
  }, [code, navigate]);

  useEffect(() => {
    if (!email) {
      navigate('/login');
      return;
    }
    fetchCode();
  }, []);

  // Countdown timer + refetch
  useEffect(() => {
    const interval = setInterval(() => {
      setRemaining((prev) => {
        if (prev <= 1) {
          fetchCode();
          return 30;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [fetchCode]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleLogout = () => {
    sessionStorage.clear();
    navigate('/login');
  };

  // Timer ring calculations
  const radius = 44;
  const circumference = 2 * Math.PI * radius;
  const progress = (remaining / 30) * circumference;
  const timerColor = remaining > 10 ? '#22c55e' : remaining > 5 ? '#f59e0b' : '#ef4444';

  return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative' }}>
      <div className="ambient-bg">
        <div className="orb orb-1" />
        <div className="orb orb-2" />
        <div className="orb orb-3" />
      </div>

      <div className="auth-card animate-fade-in" style={{ maxWidth: 480, textAlign: 'center' }}>
        {/* Header */}
        <div style={{ marginBottom: 12 }}>
          <div style={{
            width: 56, height: 56, borderRadius: '50%',
            background: 'linear-gradient(135deg, #ffffff 0%, #a0a0a0 100%)',
            display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
            marginBottom: 14, boxShadow: '0 0 40px rgba(255,255,255,0.08)',
          }}>
            <Shield size={26} color="#0a0a0a" />
          </div>
          <h1 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: 4 }}>
            Your Authentication Code
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>
            {email}
          </p>
        </div>

        {/* TOTP Code Display */}
        <div style={{ margin: '28px 0' }}>
          <div
            className="totp-code"
            style={{
              opacity: transitioning ? 0.3 : 1,
              transform: transitioning ? 'scale(0.95)' : 'scale(1)',
              transition: 'all 0.3s ease',
            }}
          >
            {code.split('').map((digit, i) => (
              <span
                key={`${digit}-${i}`}
                style={{
                  display: 'inline-block',
                  animation: !transitioning ? `fadeIn 0.3s ease ${i * 0.05}s both` : 'none',
                }}
              >
                {digit}
              </span>
            ))}
            {/* Progress bar at bottom */}
            <div style={{
              position: 'absolute', bottom: 0, left: 0,
              height: 3,
              width: `${(remaining / 30) * 100}%`,
              background: `linear-gradient(90deg, ${timerColor}, ${timerColor}88)`,
              transition: 'width 0.5s linear, background 0.5s ease',
              borderRadius: '0 2px 2px 0',
            }} />
          </div>
        </div>

        {/* Timer Ring */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 28 }}>
          <div className="timer-ring">
            <svg width="100" height="100" viewBox="0 0 100 100">
              {/* Background circle */}
              <circle
                cx="50" cy="50" r={radius}
                fill="none"
                stroke="var(--border-primary)"
                strokeWidth="4"
              />
              {/* Progress circle */}
              <circle
                cx="50" cy="50" r={radius}
                fill="none"
                stroke={timerColor}
                strokeWidth="4"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={circumference - progress}
                style={{ transition: 'stroke-dashoffset 0.5s linear, stroke 0.5s ease' }}
              />
            </svg>
            <span className="timer-text" style={{ color: timerColor }}>
              {remaining}s
            </span>
          </div>
        </div>

        {/* Copy Button */}
        <button
          onClick={handleCopy}
          className="btn-primary"
          style={{
            width: '100%', justifyContent: 'center', padding: '12px 24px',
            fontSize: '0.9rem', marginBottom: 12,
            background: copied ? 'var(--success)' : undefined,
          }}
          id="auth-copy-code"
        >
          {copied ? (
            <><Check size={18} /> Copied!</>
          ) : (
            <><Copy size={18} /> Copy Code</>
          )}
        </button>

        <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: 20, lineHeight: 1.5 }}>
          Enter this code in Pivota to complete authentication.
          <br />
          The code refreshes every 30 seconds.
        </p>

        {/* Logout */}
        <button onClick={handleLogout} className="btn-secondary" style={{ fontSize: '0.78rem' }} id="auth-logout">
          <LogOut size={14} /> Sign Out
        </button>
      </div>
    </div>
  );
}
