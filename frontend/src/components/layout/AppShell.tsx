/**
 * Pivota App Shell.
 *
 * Persistent layout wrapper with Sidebar + TopBar + MainContent.
 * Handles sidebar collapse state.
 */

import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import TopBar from './TopBar';

export default function AppShell() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  return (
    <div style={{ display: 'flex', minHeight: '100vh' }}>
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />

      {/* Main Area */}
      <div
        style={{
          flex: 1,
          marginLeft: sidebarCollapsed ? 'var(--sidebar-collapsed)' : 'var(--sidebar-width)',
          transition: 'margin-left var(--transition-base)',
          display: 'flex',
          flexDirection: 'column',
          minHeight: '100vh',
        }}
      >
        <TopBar />
        <main
          style={{
            flex: 1,
            padding: '28px',
            overflowY: 'auto',
          }}
        >
          <Outlet />
        </main>
      </div>
    </div>
  );
}
