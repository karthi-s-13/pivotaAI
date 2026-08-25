/**
 * Pivota Sidebar Navigation.
 *
 * Persistent left sidebar with navigation links, collapsible toggle,
 * and Pivota branding. Navigation organized into four sections:
 * Overview, Data, Governance, System.
 */

import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Database,
  Map,
  BookOpen,
  Search,
  Sparkles,
  Bell,
  FileText,
  Settings,
  ChevronLeft,
  ChevronRight,
  Compass,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
  section: string;
}

const navItems: NavItem[] = [
  // OVERVIEW
  { path: '/dashboard',     label: 'Dashboard',     icon: <LayoutDashboard size={20} />, section: 'overview' },
  { path: '/data-map',      label: 'Data Map',       icon: <Map size={20} />,             section: 'overview' },
  { path: '/catalog',       label: 'Catalog',        icon: <BookOpen size={20} />,         section: 'overview' },
  { path: '/search',        label: 'Search',         icon: <Search size={20} />,           section: 'overview' },
  { path: '/ask-pivota-ai', label: 'Ask Pivota AI',  icon: <Sparkles size={20} />,         section: 'overview' },

  // DATA
  { path: '/data-sources',  label: 'Data Sources',   icon: <Database size={20} />,         section: 'data' },

  // GOVERNANCE
  { path: '/alerts',        label: 'Alerts',         icon: <Bell size={20} />,             section: 'governance' },
  { path: '/audit-logs',    label: 'Audit Logs',     icon: <FileText size={20} />,         section: 'governance' },

  // SYSTEM
  { path: '/settings',      label: 'Settings',       icon: <Settings size={20} />,         section: 'system' },
];

const sectionLabels: Record<string, string> = {
  overview: 'Overview',
  data: 'Data',
  governance: 'Governance',
  system: 'System',
};

const sectionOrder = ['overview', 'data', 'governance', 'system'];

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuthStore();

  const hasPermission = (path: string) => {
    if (!user) return false;
    if (!user.is_iam) return true; // Admins bypass all checks

    const perms = user.permissions || {};
    if (path === '/data-map') return !!perms.view_data_map;
    if (path === '/catalog') return !!perms.view_catalog;
    if (path === '/search') return !!perms.view_catalog;
    if (path === '/ask-pivota-ai') return !!perms.run_select_queries;
    if (path === '/data-sources') return !!perms.create_connections || !!perms.delete_data_sources;

    return true;
  };

  return (
    <aside
      style={{
        width: collapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-width)',
        minHeight: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        transition: 'width var(--transition-base)',
        background: 'var(--bg-surface)',
        borderRight: '1px solid var(--glass-border)',
      }}
    >
      {/* Logo */}
      <div
        style={{
          height: 'var(--topbar-height)',
          display: 'flex',
          alignItems: 'center',
          padding: collapsed ? '0 16px' : '0 20px',
          gap: '12px',
          borderBottom: '1px solid var(--glass-border)',
        }}
      >
        <div
          style={{
            width: 36,
            height: 36,
            borderRadius: 9999,
            background: '#000000',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
          }}
        >
          <Compass size={20} color="white" />
        </div>
        {!collapsed && (
          <div style={{ overflow: 'hidden' }}>
            <h1
              style={{
                fontSize: '1.15rem',
                fontWeight: 800,
                letterSpacing: '-0.02em',
                whiteSpace: 'nowrap',
              }}
              className="gradient-text"
            >
              Pivota
            </h1>
            <p style={{ fontSize: '0.6rem', color: 'var(--text-muted)', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
              Data Navigator
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 8px', overflowY: 'auto' }}>
        {sectionOrder.map((section) => (
          <div key={section}>
            {!collapsed && (
              <p style={{
                fontSize: '0.65rem',
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
                padding: section === 'overview' ? '8px 12px 4px' : '16px 12px 4px',
                fontWeight: 600,
              }}>
                {sectionLabels[section]}
              </p>
            )}
            {navItems.filter(n => n.section === section && hasPermission(n.path)).map(renderNavItem)}
          </div>
        ))}
      </nav>

      {/* Collapse Toggle */}
      <div style={{ padding: '12px 8px', borderTop: '1px solid var(--glass-border)' }}>
        <button
          onClick={onToggle}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: collapsed ? 'center' : 'flex-start',
            gap: '12px',
            padding: '10px 12px',
            borderRadius: 9999,
            border: 'none',
            background: 'transparent',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            fontSize: '0.8rem',
            transition: 'all var(--transition-fast)',
          }}
          onMouseEnter={e => {
            e.currentTarget.style.background = 'var(--bg-elevated)';
            e.currentTarget.style.color = 'var(--text-primary)';
          }}
          onMouseLeave={e => {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'var(--text-muted)';
          }}
        >
          {collapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
          {!collapsed && <span>Collapse</span>}
        </button>
      </div>
    </aside>
  );

  function renderNavItem(item: NavItem) {
    // For items with query params, match on base path
    const basePath = item.path.split('?')[0];
    const isActive = item.path.includes('?')
      ? location.pathname === basePath && location.search.includes(item.path.split('?')[1])
      : location.pathname === item.path || location.pathname.startsWith(item.path + '/');

    return (
      <NavLink
        key={item.path}
        to={item.path}
        title={collapsed ? item.label : undefined}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: collapsed ? '10px 0' : '10px 12px',
          justifyContent: collapsed ? 'center' : 'flex-start',
          borderRadius: 9999,
          marginBottom: 2,
          textDecoration: 'none',
          fontSize: '0.85rem',
          fontWeight: isActive ? 600 : 400,
          color: isActive ? '#ffffff' : 'var(--text-secondary)',
          background: isActive ? '#000000' : 'transparent',
          transition: 'all var(--transition-fast)',
          position: 'relative',
        }}
        onMouseEnter={e => {
          if (!isActive) {
            e.currentTarget.style.background = 'var(--bg-elevated)';
            e.currentTarget.style.color = 'var(--text-primary)';
          }
        }}
        onMouseLeave={e => {
          if (!isActive) {
            e.currentTarget.style.background = 'transparent';
            e.currentTarget.style.color = 'var(--text-secondary)';
          }
        }}
      >
        <span style={{ color: isActive ? '#ffffff' : 'inherit', flexShrink: 0 }}>
          {item.icon}
        </span>
        {!collapsed && <span style={{ whiteSpace: 'nowrap' }}>{item.label}</span>}
      </NavLink>
    );
  }
}
