/**
 * Data Source Overview.
 *
 * Enterprise table showing all connected data sources with
 * provider, environment, metadata counts, sync status, and actions.
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight,
  MoreHorizontal,
  Eye,
  RefreshCw,
  Wifi,
  Settings,
  Unplug,
  Database,
  Plus,
} from 'lucide-react';
import type { DataSourceRow } from '../api/dashboardApi';
import { PROVIDER_META, timeAgo } from '../api/dashboardApi';
import ProviderIndicator from './ProviderIndicator';
import { StatusBadge } from './StatusIndicator';

interface DataSourceOverviewProps {
  sources: DataSourceRow[];
  onSync?: (id: string) => void;
  onTest?: (id: string) => void;
}

function EnvironmentBadge({ env }: { env: string }) {
  const normalized = env.toLowerCase();
  const cls = normalized === 'production' ? 'env-badge--production'
    : normalized === 'staging' ? 'env-badge--staging'
    : 'env-badge--development';
  return <span className={`env-badge ${cls}`}>{env}</span>;
}

function ActionsMenu({ sourceId, onSync, onTest }: { sourceId: string; onSync?: (id: string) => void; onTest?: (id: string) => void }) {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  return (
    <div className="actions-menu">
      <button
        className="actions-menu__trigger"
        onClick={(e) => { e.stopPropagation(); setOpen(!open); }}
        aria-label="Actions"
      >
        <MoreHorizontal size={16} />
      </button>
      {open && (
        <>
          <div style={{ position: 'fixed', inset: 0, zIndex: 25 }} onClick={() => setOpen(false)} />
          <div className="actions-menu__dropdown">
            <button className="actions-menu__item" onClick={() => { setOpen(false); navigate(`/data-sources`); }}>
              <Eye size={14} /> View
            </button>
            <button className="actions-menu__item" onClick={() => { setOpen(false); onSync?.(sourceId); }}>
              <RefreshCw size={14} /> Sync
            </button>
            <button className="actions-menu__item" onClick={() => { setOpen(false); onTest?.(sourceId); }}>
              <Wifi size={14} /> Test Connection
            </button>
            <button className="actions-menu__item" onClick={() => { setOpen(false); navigate(`/data-sources`); }}>
              <Settings size={14} /> Edit
            </button>
            <div style={{ height: 1, background: 'var(--glass-border)', margin: '4px 0' }} />
            <button className="actions-menu__item actions-menu__item--danger" onClick={() => setOpen(false)}>
              <Unplug size={14} /> Disconnect
            </button>
          </div>
        </>
      )}
    </div>
  );
}

export default function DataSourceOverview({ sources, onSync, onTest }: DataSourceOverviewProps) {
  const navigate = useNavigate();

  if (sources.length === 0) {
    return (
      <div style={{ marginBottom: 32 }}>
        <div className="section-header">
          <h2 className="section-header__title">Data Source Overview</h2>
          <p className="section-header__sub">Monitor the connected systems powering your organization's data landscape.</p>
        </div>
        <div className="dashboard-empty">
          <div className="dashboard-empty__icon">
            <Database size={28} />
          </div>
          <h3 className="dashboard-empty__title">Connect your first data source</h3>
          <p className="dashboard-empty__desc">
            Start building your organization's data map by connecting a database.
          </p>
          <button className="btn-primary" onClick={() => navigate('/data-sources')}>
            <Plus size={16} /> Add Data Source
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ marginBottom: 32 }}>
      <div className="section-header">
        <div className="section-header__row">
          <div>
            <h2 className="section-header__title">Data Source Overview</h2>
            <p className="section-header__sub">Monitor the connected systems powering your organization's data landscape.</p>
          </div>
        </div>
      </div>

      <div className="ds-table-wrap">
        <table className="ds-table">
          <thead>
            <tr>
              <th>Provider</th>
              <th>Source Name</th>
              <th>Environment</th>
              <th>Databases</th>
              <th>Tables</th>
              <th>Last Sync</th>
              <th>Status</th>
              <th style={{ width: 48 }} />
            </tr>
          </thead>
          <tbody>
            {sources.map((ds) => {
              const meta = PROVIDER_META[ds.provider] || { label: ds.provider, color: 'var(--text-muted)', bgColor: 'rgba(148,163,184,0.12)' };
              return (
                <tr key={ds.id} onClick={() => navigate('/data-sources')}>
                  <td>
                    <ProviderIndicator provider={ds.provider} size="sm" />
                  </td>
                  <td>
                    <div>
                      <div style={{ fontWeight: 500 }}>{ds.name}</div>
                      {ds.host && (
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-disabled)', fontFamily: "'JetBrains Mono', monospace" }}>
                          {ds.host}:{ds.port}
                        </div>
                      )}
                    </div>
                  </td>
                  <td><EnvironmentBadge env={ds.environment} /></td>
                  <td><span className="ds-table__meta-count">{ds.databases_count}</span></td>
                  <td><span className="ds-table__meta-count">{ds.tables_count}</span></td>
                  <td style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>{timeAgo(ds.last_sync_at)}</td>
                  <td><StatusBadge status={ds.health_status} /></td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <ActionsMenu sourceId={ds.id} onSync={onSync} onTest={onTest} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <div className="ds-table__footer">
          <button className="ds-table__link" onClick={() => navigate('/data-sources')}>
            View all sources <ArrowRight size={13} />
          </button>
        </div>
      </div>
    </div>
  );
}
