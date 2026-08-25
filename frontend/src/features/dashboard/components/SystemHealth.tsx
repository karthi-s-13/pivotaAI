/**
 * System Health.
 *
 * Compact panel showing Pivota's connector infrastructure health.
 * Derived from dashboard stats rather than a separate endpoint.
 */

import type { SystemHealthStatus } from '../api/dashboardApi';
import StatusIndicator from './StatusIndicator';

interface SystemHealthProps {
  health: SystemHealthStatus;
}

interface HealthEntry {
  name: string;
  status: SystemHealthStatus[keyof Omit<SystemHealthStatus, 'summary'>];
}

export default function SystemHealth({ health }: SystemHealthProps) {
  const entries: HealthEntry[] = [
    { name: 'Connector Engine',     status: health.connector_engine },
    { name: 'Metadata Discovery',   status: health.metadata_discovery },
    { name: 'API Services',         status: health.api_services },
    { name: 'Application Database', status: health.application_database },
    { name: 'Authentication',       status: health.authentication },
  ];

  return (
    <div className="dashboard-panel">
      <div className="dashboard-panel__header">
        <h3 className="dashboard-panel__title">System Health</h3>
        <span style={{
          fontSize: '0.68rem',
          fontWeight: 600,
          color: 'var(--text-muted)',
          fontFamily: "'JetBrains Mono', monospace",
        }}>
          {health.summary}
        </span>
      </div>

      <div className="health-list">
        {entries.map((entry) => (
          <div key={entry.name} className="health-item">
            <div className="health-item__left">
              <StatusIndicator status={entry.status} showLabel={false} size="sm" />
              <span className="health-item__name">{entry.name}</span>
            </div>
            <span
              className="health-item__status"
              style={{
                color: entry.status === 'operational' ? 'var(--status-success)'
                  : entry.status === 'degraded' ? 'var(--status-warning)'
                  : 'var(--status-error)',
              }}
            >
              {entry.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
