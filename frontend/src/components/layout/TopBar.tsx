/**
 * Pivota Top Bar.
 *
 * Displays search, notifications, and user avatar/menu.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, LogOut, User, ChevronDown } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

export default function TopBar() {
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const [showMenu, setShowMenu] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const initials = user?.full_name
    ?.split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) || 'U';

  return (
    <header
      style={{
        height: 'var(--topbar-height)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 28px',
        borderBottom: '1px solid var(--glass-border)',
        background: 'var(--bg-surface)',
        position: 'sticky',
        top: 0,
        zIndex: 40,
      }}
    >
      {/* Search Bar */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: '#ffffff',
          border: '1px solid #000000',
          borderRadius: 9999,
          padding: '8px 16px',
          width: '100%',
          maxWidth: 400,
          transition: 'all var(--transition-fast)',
        }}
      >
        <Search size={16} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
        <input
          type="text"
          placeholder="Search metadata..."
          style={{
            border: 'none',
            background: 'transparent',
            color: 'var(--text-primary)',
            fontSize: '0.85rem',
            outline: 'none',
            width: '100%',
            fontFamily: 'inherit',
          }}
        />
        <kbd
          style={{
            fontSize: '0.65rem',
            color: 'var(--text-muted)',
            background: 'var(--bg-surface)',
            padding: '2px 6px',
            borderRadius: 4,
            border: '1px solid var(--border-default)',
            whiteSpace: 'nowrap',
          }}
        >
          ⌘K
        </kbd>
      </div>

      {/* Right Section */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Notifications */}
        <button
          style={{
            position: 'relative',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-secondary)',
            cursor: 'pointer',
            padding: 8,
            borderRadius: 9999,
            transition: 'all var(--transition-fast)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'var(--bg-elevated)';
            e.currentTarget.style.color = 'var(--text-primary)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'var(--text-secondary)';
          }}
        >
          <Bell size={20} />
        </button>

        {/* User Menu */}
        <div style={{ position: 'relative' }}>
          <button
            onClick={() => setShowMenu(!showMenu)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: '#ffffff',
              border: '1px solid #000000',
              borderRadius: 9999,
              padding: '6px 16px 6px 6px',
              cursor: 'pointer',
              transition: 'all var(--transition-fast)',
            }}
            onMouseEnter={e => {
              e.currentTarget.style.borderColor = 'var(--border-hover)';
              e.currentTarget.style.background = 'var(--bg-elevated)';
            }}
            onMouseLeave={e => {
              e.currentTarget.style.borderColor = 'var(--border-default)';
              e.currentTarget.style.background = 'transparent';
            }}
          >
            <div
              style={{
                width: 32,
                height: 32,
                borderRadius: 9999,
                background: '#000000',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.75rem',
                fontWeight: 700,
                color: 'white',
              }}
            >
              {initials}
            </div>
            <div style={{ textAlign: 'left' }}>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-primary)', fontWeight: 500, lineHeight: 1.2 }}>
                {user?.full_name || 'User'}
              </p>
              <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>
                {user?.role || 'admin'}
              </p>
            </div>
            <ChevronDown size={14} style={{ color: 'var(--text-muted)' }} />
          </button>

          {/* Dropdown Menu */}
          {showMenu && (
            <>
              <div
                style={{ position: 'fixed', inset: 0, zIndex: 40 }}
                onClick={() => setShowMenu(false)}
              />
              <div
                className="glass"
                style={{
                  position: 'absolute',
                  top: '100%',
                  right: 0,
                  marginTop: 8,
                  width: 200,
                  borderRadius: 8,
                  padding: 6,
                  zIndex: 50,
                  border: '1px solid #000000',
                  boxShadow: 'none',
                }}
              >
                <button
                  onClick={() => { setShowMenu(false); navigate('/settings'); }}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    width: '100%',
                    padding: '10px 12px',
                    border: 'none',
                    background: 'transparent',
                    color: 'var(--text-secondary)',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    borderRadius: 8,
                    transition: 'all var(--transition-fast)',
                  }}
                  onMouseEnter={e => {
                    e.currentTarget.style.background = 'var(--bg-elevated)';
                    e.currentTarget.style.color = 'var(--text-primary)';
                  }}
                  onMouseLeave={e => {
                    e.currentTarget.style.background = 'transparent';
                    e.currentTarget.style.color = 'var(--text-secondary)';
                  }}
                >
                  <User size={16} /> Profile
                </button>
                <div style={{ height: 1, background: 'var(--glass-border)', margin: '4px 0' }} />
                <button
                  onClick={handleLogout}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    width: '100%',
                    padding: '10px 12px',
                    border: 'none',
                    background: 'transparent',
                    color: 'var(--status-error)',
                    fontSize: '0.8rem',
                    cursor: 'pointer',
                    borderRadius: 8,
                    transition: 'all var(--transition-fast)',
                  }}
                  onMouseEnter={e => { e.currentTarget.style.background = 'var(--status-error-bg)'; }}
                  onMouseLeave={e => { e.currentTarget.style.background = 'transparent'; }}
                >
                  <LogOut size={16} /> Sign Out
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
