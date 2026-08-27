/**
 * Data Sources Page.
 *
 * Lists all data sources with cards, filters, and an "Add Data Source" wizard.
 */

import { useState, useEffect } from 'react';
import {
  Database, Plus, RefreshCw, Trash2, Wifi,
  CheckCircle, XCircle, AlertTriangle, Loader2,
  Search,
} from 'lucide-react';
import { dataSourceApi } from '../api/dataSourceApi';
import type { DataSource } from '../api/dataSourceApi';
import AddDataSourceWizard from '../components/AddDataSourceWizard';
import { getProviderColor, getProviderLabel } from '../../data-map/types/dataMap.types';

export default function DataSourcesPage() {
  const [sources, setSources] = useState<DataSource[]>([]);
  const [loading, setLoading] = useState(true);
  const [showWizard, setShowWizard] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [search, setSearch] = useState('');

  useEffect(() => { loadSources(); }, []);

  const loadSources = async () => {
    setLoading(true);
    try {
      const result = await dataSourceApi.list();
      setSources(result);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  };

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      await dataSourceApi.testConnection(id);
      await loadSources();
    } catch { /* ignore */ }
    finally { setTestingId(null); }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete data source "${name}"?`)) return;
    try {
      await dataSourceApi.delete(id);
      setSources(sources.filter(s => s.identity?.id !== id));
    } catch { /* ignore */ }
  };

  const filtered = sources.filter(s =>
    (s.identity?.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (s.identity?.provider || '').toLowerCase().includes(search.toLowerCase())
  );

  const statusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'connected':
        return <CheckCircle size={14} style={{ color: 'var(--status-success)' }} />;
      case 'syncing':
      case 'testing':
        return <Loader2 size={14} className="animate-spin" style={{ color: 'var(--brand-primary)' }} />;
      case 'auth_failed':
      case 'network_error':
      case 'permission_denied':
      case 'error':
        return <XCircle size={14} style={{ color: 'var(--status-error)' }} />;
      default:
        return <AlertTriangle size={14} style={{ color: 'var(--status-warning)' }} />;
    }
  };

  if (showWizard) {
    return (
      <AddDataSourceWizard
        onClose={() => setShowWizard(false)}
        onSuccess={() => {
          setShowWizard(false);
          loadSources();
        }}
      />
    );
  }

  return (
    <div className="animate-fade-in">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: 4 }}>Data Sources</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
            Manage your external database connections
          </p>
        </div>
        <button className="btn-primary" onClick={() => setShowWizard(true)}>
          <Plus size={18} /> Add Data Source
        </button>
      </div>

      {/* Search Bar */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 20 }}>
        <div
          style={{
            flex: 1,
            maxWidth: 360,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            background: '#ffffff',
            border: '1px solid var(--border-default)',
            borderRadius: 9999,
            padding: '8px 16px',
          }}
        >
          <Search size={16} style={{ color: 'var(--text-muted)' }} />
          <input
            type="text"
            placeholder="Search data sources..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ border: 'none', background: 'transparent', color: 'var(--text-primary)', fontSize: '0.85rem', outline: 'none', width: '100%', fontFamily: 'inherit' }}
          />
        </div>
        <button className="btn-ghost" onClick={loadSources} style={{ padding: '8px 14px' }}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ display: 'flex', justifyContent: 'center', padding: 60 }}>
          <Loader2 size={32} className="animate-spin-slow" style={{ color: 'var(--brand-primary)' }} />
        </div>
      )}

      {/* Empty State */}
      {!loading && filtered.length === 0 && (
        <div
          style={{
            textAlign: 'center',
            padding: '60px 30px',
            background: 'var(--bg-elevated)',
            border: '1px dashed var(--border-default)',
            borderRadius: 12,
          }}
        >
          <Database size={48} style={{ color: 'var(--text-disabled)', marginBottom: 16 }} />
          <h2 style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: 8 }}>
            {sources.length === 0 ? 'No data sources yet' : 'No results found'}
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: 20, maxWidth: 400, margin: '0 auto 20px' }}>
            {sources.length === 0
              ? 'Connect your first database to start building your metadata catalog.'
              : 'Try a different search term.'}
          </p>
          {sources.length === 0 && (
            <button className="btn-primary" onClick={() => setShowWizard(true)}>
              <Plus size={18} /> Add Your First Data Source
            </button>
          )}
        </div>
      )}

      {/* Source Cards */}
      {!loading && filtered.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
          {filtered.map((ds, i) => {
            const sId = ds.identity?.id || '';
            const sName = ds.identity?.name || '';
            const sProvider = ds.identity?.provider || '';
            const sEnv = ds.identity?.environment || '';
            const sStatus = ds.health?.status || 'unknown';
            const sError = ds.health?.last_error || '';

            return (
              <div
                key={sId}
                className="hover-card animate-fade-in"
                style={{
                  padding: '20px',
                  animationDelay: `${i * 0.05}s`,
                  opacity: 0,
                  background: '#ffffff',
                  border: '1px solid var(--border-default)',
                  borderRadius: 12,
                }}
              >
                {/* Header */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <div
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: 10,
                        background: `${getProviderColor(sProvider)}18`,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: getProviderColor(sProvider),
                        flexShrink: 0,
                      }}
                    >
                      <Database size={20} />
                    </div>
                    <div>
                      <h3 style={{ fontSize: '0.95rem', fontWeight: 600, lineHeight: 1.2 }}>{sName}</h3>
                      <p style={{ fontSize: '0.72rem', color: 'var(--text-muted)' }}>
                        {getProviderLabel(sProvider)} · {sEnv}
                      </p>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                    {statusIcon(sStatus)}
                    <span
                      className={`badge ${
                        sStatus === 'healthy' || sStatus === 'connected' ? 'badge-success' :
                        sStatus === 'syncing' || sStatus === 'testing' ? 'badge-info' :
                        sStatus === 'unknown' || sStatus === 'disconnected' ? 'badge-warning' : 'badge-error'
                      }`}
                    >
                      {sStatus}
                    </span>
                  </div>
                </div>

                {/* Details */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginBottom: 14 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span style={{ color: 'var(--text-disabled)' }}>Host:</span>{' '}
                    <span className="mono" style={{ color: 'var(--text-secondary)' }}>{ds.connectivity?.host || 'URI Connect'}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span style={{ color: 'var(--text-disabled)' }}>Port:</span>{' '}
                    <span className="mono" style={{ color: 'var(--text-secondary)' }}>{ds.connectivity?.port || 'N/A'}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span style={{ color: 'var(--text-disabled)' }}>Database:</span>{' '}
                    <span className="mono" style={{ color: 'var(--text-secondary)' }}>{ds.connectivity?.provider_config?.database_name || 'N/A'}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    <span style={{ color: 'var(--text-disabled)' }}>Tables:</span>{' '}
                    <span style={{ color: 'var(--text-secondary)' }}>{ds.metadata?.statistics?.objects_count || 0}</span>
                  </div>
                </div>

                {/* Connection Error */}
                {sError && (
                  <div style={{ fontSize: '0.72rem', color: 'var(--status-error)', background: 'var(--status-error-bg)', padding: '6px 10px', borderRadius: 6, marginBottom: 12, lineHeight: 1.4 }}>
                    {sError.slice(0, 100)}
                  </div>
                )}

                {/* Actions */}
                <div style={{ display: 'flex', gap: 8 }}>
                  <button
                    className="btn-ghost"
                    style={{ flex: 1, justifyContent: 'center', padding: '8px 12px', fontSize: '0.78rem' }}
                    onClick={() => handleTest(sId)}
                    disabled={testingId === sId}
                  >
                    {testingId === sId ? (
                      <><Loader2 size={14} className="animate-spin-slow" /> Testing...</>
                    ) : (
                      <><Wifi size={14} /> Test</>
                    )}
                  </button>
                  <button
                    className="btn-ghost"
                    style={{ padding: '8px 12px', fontSize: '0.78rem', color: 'var(--status-error)' }}
                    onClick={() => handleDelete(sId, sName)}
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
