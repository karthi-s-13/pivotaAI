/**
 * Pivota App Entry Point.
 *
 * Sets up routing, auth protection, 2FA verification, and query client.
 */

import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, Outlet, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

import { useAuthStore } from './stores/authStore';
import { authApi } from './features/auth/api/authApi';

// Layout
import AppShell from './components/layout/AppShell';

// Pages
import LoginPage from './features/auth/pages/LoginPage';
import SignupPage from './features/auth/pages/SignupPage';
import Verify2FAPage from './features/auth/pages/Verify2FAPage';
import IAMLoginPage from './features/auth/pages/IAMLoginPage';
import IAMChangePasswordPage from './features/auth/pages/IAMChangePasswordPage';
import DashboardPage from './features/dashboard/pages/DashboardPage';
import DataSourcesPage from './features/data-sources/pages/DataSourcesPage';
import DataMapPage from './features/data-map/pages/DataMapPage';
import CatalogPage from './features/catalog/pages/CatalogPage';
import SearchPage from './features/search/pages/SearchPage';
import AskAIPage from './features/ask-ai/pages/AskAIPage';
import AlertsPage from './features/alerts/pages/AlertsPage';
import AuditLogsPage from './features/audit-logs/pages/AuditLogsPage';
import SettingsPage from './features/settings/pages/SettingsPage';

import { Loader2, Compass } from 'lucide-react';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

/**
 * Protected Route Wrapper
 * Checks if user is authenticated and 2FA verified.
 * If not authenticated → /login
 * If authenticated but not 2FA verified → /verify-2fa
 */
function ProtectedRoute() {
  const { isAuthenticated, isLoading, user, setAuth, setLoading } = useAuthStore();
  const [verifying, setVerifying] = useState(true);

  useEffect(() => {
    const verifyAuth = async () => {
      const token = localStorage.getItem('pivota_access_token');
      const refreshToken = localStorage.getItem('pivota_refresh_token');

      if (token && refreshToken && !isAuthenticated) {
        try {
          const user = await authApi.getMe();
          setAuth(user, token, refreshToken);
        } catch {
          // Handled by axios interceptor
        }
      }
      setVerifying(false);
      setLoading(false);
    };

    verifyAuth();
  }, [isAuthenticated, setAuth, setLoading]);

  if (isLoading || verifying) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#ffffff' }}>
        <div style={{ width: 64, height: 64, borderRadius: 9999, background: '#000000', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
          <Compass size={32} color="white" />
        </div>
        <Loader2 size={32} className="animate-spin" style={{ color: '#000000' }} />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Check 2FA verification
  if (user && !user.is_2fa_verified) {
    return <Navigate to="/verify-2fa" replace />;
  }

  return <Outlet />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/verify-2fa" element={<Verify2FAPage />} />
          <Route path="/iam/login" element={<IAMLoginPage />} />
          <Route path="/iam/change-password" element={<IAMChangePasswordPage />} />

          {/* Protected Routes inside App Shell */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppShell />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/data-sources" element={<DataSourcesPage />} />
              <Route path="/data-map" element={<DataMapPage />} />
              <Route path="/catalog" element={<CatalogPage />} />
              <Route path="/search" element={<SearchPage />} />
              <Route path="/ask-pivota-ai" element={<AskAIPage />} />
              <Route path="/alerts" element={<AlertsPage />} />
              <Route path="/audit-logs" element={<AuditLogsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
