/**
 * Data Landscape Preview.
 *
 * Lightweight tree visualization showing provider hierarchy:
 * PIVOTA → Providers → Databases/Tables/Columns counts.
 *
 * This is a compact preview — the full interactive graph
 * belongs to the Data Map page.
 */

import { useNavigate } from 'react-router-dom';
import { ArrowRight, Compass, Database } from 'lucide-react';
import type { DataSourceRow } from '../api/dashboardApi';
import { PROVIDER_META } from '../api/dashboardApi';

interface DataLandscapePreviewProps {
  sources: DataSourceRow[];
}

export default function DataLandscapePreview({ sources }: DataLandscapePreviewProps) {
  const navigate = useNavigate();

  // Group sources by provider
  const providerGroups: Record<string, { databases: number; tables: number; columns: number; count: number }> = {};
  sources.forEach((ds) => {
    const key = ds.provider;
    if (!providerGroups[key]) {
      providerGroups[key] = { databases: 0, tables: 0, columns: 0, count: 0 };
    }
    providerGroups[key].databases += ds.databases_count;
    providerGroups[key].tables += ds.tables_count;
    providerGroups[key].columns += ds.columns_count;
    providerGroups[key].count += 1;
  });

  const providers = Object.entries(providerGroups);

  if (providers.length === 0) return null;

  return (
    <div className="landscape-section">
      <div className="section-header">
        <div className="section-header__row">
          <div>
            <h2 className="section-header__title">Your Data Landscape</h2>
            <p className="section-header__sub">A snapshot of your connected metadata hierarchy.</p>
          </div>
          <button className="ds-table__link" onClick={() => navigate('/data-map')}>
            Explore Data Map <ArrowRight size={13} />
          </button>
        </div>
      </div>

      {/* Tree Visualization */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        {/* Root */}
        <div className="landscape-tree__root">
          <div className="landscape-tree__root-badge">
            <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Compass size={13} />
              Pivota
            </span>
          </div>
          <div className="landscape-tree__connector" />
        </div>

        {/* Horizontal branch line */}
        {providers.length > 1 && (
          <div
            style={{
              width: `${Math.min(providers.length * 180, 720)}px`,
              height: 1,
              background: 'var(--border-default)',
              marginBottom: 0,
            }}
          />
        )}

        {/* Provider Nodes */}
        <div className="landscape-tree">
          {providers.map(([provider, data]) => {
            const meta = PROVIDER_META[provider] || { label: provider, color: 'var(--text-muted)', bgColor: 'rgba(148,163,184,0.12)' };
            return (
              <div key={provider} className="landscape-tree__provider">
                <div className="landscape-tree__connector" />
                <div className="landscape-tree__icon" style={{ background: meta.bgColor }}>
                  <Database size={20} style={{ color: meta.color }} />
                </div>
                <div className="landscape-tree__name">{meta.label}</div>
                <div className="landscape-tree__stats">
                  <span className="landscape-tree__stat">{data.databases} databases</span>
                  <span className="landscape-tree__stat">{data.tables} tables</span>
                  <span className="landscape-tree__stat">{data.columns.toLocaleString()} columns</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
