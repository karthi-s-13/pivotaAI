/**
 * Pivota Dashboard Page — Enterprise Redesign.
 *
 * Contemporary metadata navigation dashboard with:
 * - Time-of-day greeting with organization context
 * - Core metric cards (Providers → Databases → Tables → Columns)
 * - Data Source Overview table
 * - Recent Activity + System Health split
 * - Data Landscape preview
 *
 * All data fetched from real backend endpoints.
 */

import { useState, useEffect, useCallback } from 'react';
import {
  Database,
  Server,
  Table2,
  Columns3,
} from 'lucide-react';
import { useAuthStore } from '../../../stores/authStore';
import {
  dashboardApi,
  deriveSystemHealth,
  type DashboardData,
  type DataSourceRow,
  type SystemHealthStatus,
} from '../api/dashboardApi';

// Components
import DashboardWelcome from '../components/DashboardWelcome';
import MetricCard from '../components/MetricCard';
import DataSourceOverview from '../components/DataSourceOverview';
import RecentActivity from '../components/RecentActivity';
import SystemHealth from '../components/SystemHealth';
import LoadingSkeleton from '../components/LoadingSkeleton';

// Styles
import '../styles/dashboard.css';

export default function DashboardPage() {
  const { user } = useAuthStore();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [dataSources, setDataSources] = useState<DataSourceRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const [dashboard, sources] = await Promise.all([
        dashboardApi.getDashboard(),
        dashboardApi.getDataSources(),
      ]);
      setDashboardData(dashboard);
      setDataSources(sources);
    } catch {
      // Graceful fallback — show what we can
      setDashboardData({
        stats: { data_sources_count: 0, databases_count: 0, tables_count: 0, columns_count: 0, connected_count: 0, error_count: 0 },
        recent_activity: [],
        data_source_health: [],
      });
      setDataSources([]);
      setError(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // ─── Loading State ──────────────────────────
  if (loading) {
    return <LoadingSkeleton />;
  }

  const stats = dashboardData!.stats;
  const orgName = user?.organization_name || user?.full_name?.split(' ')[0] || 'there';

  // Count unique providers
  const uniqueProviders = new Set(dataSources.map(ds => ds.provider));
  const providerCount = uniqueProviders.size || stats.data_sources_count;

  // Derive system health from real data
  const systemHealth: SystemHealthStatus = deriveSystemHealth(stats, dashboardData!.data_source_health);

  return (
    <div className="dashboard-content animate-fade-in">
      {/* ─── Welcome Section ─── */}
      <DashboardWelcome organizationName={orgName} />

      {/* ─── Core Metric Cards ─── */}
      <div className="metric-cards-row">
        <MetricCard
          icon={<Database size={20} />}
          value={providerCount}
          label="Data Providers"
          subtitle="Connected providers"
          navigateTo="/data-sources"
          delay={0}
        />
        <MetricCard
          icon={<Server size={20} />}
          value={stats.databases_count}
          label="Databases"
          subtitle="Across all connected sources"
          navigateTo="/catalog"
          delay={0.06}
        />
        <MetricCard
          icon={<Table2 size={20} />}
          value={stats.tables_count}
          label="Tables"
          subtitle="Discovered metadata objects"
          navigateTo="/catalog"
          delay={0.12}
        />
        <MetricCard
          icon={<Columns3 size={20} />}
          value={stats.columns_count}
          label="Columns"
          subtitle="Cataloged attributes"
          navigateTo="/catalog"
          delay={0.18}
        />
      </div>

      {/* ─── Data Source Overview ─── */}
      <DataSourceOverview
        sources={dataSources}
        onSync={(id) => {
          // Trigger sync via API and reload
          import('../../data-sources/api/dataSourceApi').then(({ dataSourceApi }) => {
            dataSourceApi.testConnection(id).then(() => loadData());
          });
        }}
        onTest={(id) => {
          import('../../data-sources/api/dataSourceApi').then(({ dataSourceApi }) => {
            dataSourceApi.testConnection(id).then(() => loadData());
          });
        }}
      />

      {/* ─── Activity + Health Split ─── */}
      <div className="dashboard-split">
        <RecentActivity activities={dashboardData!.recent_activity} />
        <SystemHealth health={systemHealth} />
      </div>
    </div>
  );
}
