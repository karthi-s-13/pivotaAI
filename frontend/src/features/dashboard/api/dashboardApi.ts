/**
 * Dashboard API Layer.
 *
 * Typed interfaces and API functions for the enterprise dashboard.
 * Consumes /dashboard and /data-sources endpoints.
 */

import apiClient from '../../../services/api/apiClient';

// ─── Types ───────────────────────────────────────────────────

export interface DashboardStats {
  data_sources_count: number;
  databases_count: number;
  tables_count: number;
  columns_count: number;
  connected_count: number;
  error_count: number;
}

export interface ActivityItem {
  id: string;
  action: string;
  resource_type: string | null;
  resource_id: string | null;
  details: Record<string, any> | null;
  user_name: string | null;
  timestamp: string;
}

export interface DataSourceHealth {
  id: string;
  name: string;
  provider_type: string;
  connection_status: string;
  last_tested_at: string | null;
  environment: string;
}

export interface DashboardData {
  stats: DashboardStats;
  recent_activity: ActivityItem[];
  data_source_health: DataSourceHealth[];
}

/** Data source row used by the overview table */
export interface DataSourceRow {
  id: string;
  name: string;
  description: string | null;
  provider: string;
  host: string;
  port: number;
  environment: string;
  status: string;
  health_status: string;
  databases_count: number;
  tables_count: number;
  columns_count: number;
  last_sync_at: string | null;
  created_at: string;
}

/** System health status (derived from dashboard data) */
export interface SystemHealthStatus {
  connector_engine: 'operational' | 'degraded' | 'down';
  metadata_discovery: 'operational' | 'degraded' | 'down';
  api_services: 'operational' | 'degraded' | 'down';
  application_database: 'operational' | 'degraded' | 'down';
  authentication: 'operational' | 'degraded' | 'down';
  summary: string;
}

// ─── Provider Metadata ──────────────────────────────────────

export const PROVIDER_META: Record<string, { label: string; color: string; bgColor: string }> = {
  postgresql: { label: 'PostgreSQL', color: '#6366f1', bgColor: 'rgba(99, 102, 241, 0.12)' },
  mysql:      { label: 'MySQL',      color: '#8b5cf6', bgColor: 'rgba(139, 92, 246, 0.12)' },
  sqlserver:  { label: 'SQL Server', color: '#3b82f6', bgColor: 'rgba(59, 130, 246, 0.12)' },
  mongodb:    { label: 'MongoDB',    color: '#10b981', bgColor: 'rgba(16, 185, 129, 0.12)' },
};

// ─── Helpers ────────────────────────────────────────────────

export function deriveSystemHealth(
  stats: DashboardStats,
  healthList: DataSourceHealth[]
): SystemHealthStatus {
  const total = stats.data_sources_count;
  const connected = stats.connected_count;
  const errors = stats.error_count;

  const connectorEngine: SystemHealthStatus['connector_engine'] =
    total === 0 ? 'operational' :
    errors === 0 ? 'operational' :
    errors < total ? 'degraded' : 'down';

  const hasWarning = healthList.some(h =>
    h.connection_status !== 'healthy' && h.connection_status !== 'connected'
  );

  return {
    connector_engine: connectorEngine,
    metadata_discovery: connectorEngine === 'down' ? 'degraded' : 'operational',
    api_services: 'operational',
    application_database: 'operational',
    authentication: 'operational',
    summary: `${connected} / ${total} operational`,
  };
}

export function timeAgo(dateStr: string | null): string {
  if (!dateStr) return 'Never';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

export function actionLabel(action: string): string {
  const map: Record<string, string> = {
    DATA_SOURCE_CREATED: 'Data source connected',
    DATA_SOURCE_UPDATED: 'Data source updated',
    DATA_SOURCE_DELETED: 'Data source removed',
    DATA_SOURCE_CONNECTED: 'Data source connected',
    DATA_SOURCE_DISCONNECTED: 'Data source disconnected',
    DATA_SOURCE_DISCOVERY_STARTED: 'Metadata discovery started',
    CONNECTION_TESTED: 'Connection tested',
    LOGIN: 'User signed in',
    SIGNUP: 'Account created',
  };
  return map[action] || action.replace(/_/g, ' ').toLowerCase();
}

export function actionDescription(action: string, details: Record<string, any> | null): string {
  if (!details) return '';
  if (action === 'CONNECTION_TESTED') {
    return details.success ? 'Connection test successful' : 'Connection test failed';
  }
  if (action === 'DATA_SOURCE_CREATED' || action === 'DATA_SOURCE_CONNECTED') {
    return details.provider ? `${PROVIDER_META[details.provider]?.label || details.provider} provider` : '';
  }
  if (details.name) return details.name;
  return '';
}

// ─── API Functions ──────────────────────────────────────────

export const dashboardApi = {
  /** Fetch dashboard stats, activity, and health */
  getDashboard: async (): Promise<DashboardData> => {
    const response = await apiClient.get('/dashboard');
    return response.data;
  },

  /** Fetch all data sources for the overview table */
  getDataSources: async (): Promise<DataSourceRow[]> => {
    const response = await apiClient.get('/data-sources');
    // Normalize the nested response into flat rows
    return response.data.map((ds: any) => ({
      id: ds.identity?.id || ds.id,
      name: ds.identity?.name || ds.name,
      description: ds.description || null,
      provider: ds.identity?.provider || ds.provider_type || ds.provider,
      host: ds.connectivity?.host || ds.host || '',
      port: ds.connectivity?.port || ds.port || 0,
      environment: ds.identity?.environment || ds.environment || 'development',
      status: ds.status?.current || ds.status || 'active',
      health_status: ds.status?.health || ds.health_status || ds.connection_status || 'unknown',
      databases_count: ds.metadata?.databases_count ?? ds.databases_count ?? 0,
      tables_count: ds.metadata?.tables_count ?? ds.tables_count ?? 0,
      columns_count: ds.metadata?.columns_count ?? ds.columns_count ?? 0,
      last_sync_at: ds.metadata?.last_sync_at || ds.last_sync_at || null,
      created_at: ds.created_at || '',
    }));
  },
};
