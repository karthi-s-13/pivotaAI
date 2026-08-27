/**
 * Inspector Panel — Right-side contextual detail view.
 * Shows metadata for the selected node.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Info,
  Database,
  Table2,
  Network,
  RefreshCw,
  ExternalLink,
  X,
  Link2,
  ChevronRight,
  Layers,
  BarChart3,
} from 'lucide-react';
import type { DataMapNode, ProviderMetadata } from '../types/dataMap.types';
import { getProviderLabel } from '../types/dataMap.types';

interface InspectorPanelProps {
  node: DataMapNode | null;
  onClose: () => void;
  onRefresh: (nodeId: string) => void;
  onNavigate: (nodeId: string) => void;
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <h4
        style={{
          fontSize: '0.65rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: 1,
          color: 'var(--text-muted)',
          marginBottom: 10,
          paddingBottom: 6,
          borderBottom: '1px solid var(--bg-elevated)',
        }}
      >
        {title}
      </h4>
      {children}
    </div>
  );
}

function Row({ label, value, mono }: { label: string; value: React.ReactNode; mono?: boolean }) {
  return (
    <div
      style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        gap: 8,
        padding: '5px 0',
        borderBottom: '1px solid var(--bg-elevated)',
      }}
    >
      <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)', flexShrink: 0 }}>{label}</span>
      <span
        style={{
          fontSize: '0.73rem',
          color: 'var(--text-primary)',
          fontFamily: mono ? "'JetBrains Mono', monospace" : 'inherit',
          textAlign: 'right',
          wordBreak: 'break-all',
        }}
      >
        {value}
      </span>
    </div>
  );
}

/** Shared status token mapping, consistent with the app's StatusIndicator. */
const STATUS_MAP: Record<string, { color: string; bg: string; label: string }> = {
  connected: { color: 'var(--status-success)', bg: 'var(--status-success-bg)', label: 'Connected' },
  healthy: { color: 'var(--status-success)', bg: 'var(--status-success-bg)', label: 'Connected' },
  ready: { color: 'var(--status-success)', bg: 'var(--status-success-bg)', label: 'Ready' },
  disconnected: { color: 'var(--text-disabled)', bg: 'var(--bg-elevated)', label: 'Disconnected' },
  idle: { color: 'var(--text-disabled)', bg: 'var(--bg-elevated)', label: 'Not Verified' },
  unknown: { color: 'var(--text-disabled)', bg: 'var(--bg-elevated)', label: 'Not Verified' },
  error: { color: 'var(--status-error)', bg: 'var(--status-error-bg)', label: 'Error' },
  auth_failed: { color: 'var(--status-error)', bg: 'var(--status-error-bg)', label: 'Auth Failed' },
  network_error: { color: 'var(--status-error)', bg: 'var(--status-error-bg)', label: 'Network Error' },
  permission_denied: { color: 'var(--status-error)', bg: 'var(--status-error-bg)', label: 'Permission Denied' },
  syncing: { color: 'var(--status-info)', bg: 'var(--status-info-bg)', label: 'Syncing' },
  testing: { color: 'var(--status-info)', bg: 'var(--status-info-bg)', label: 'Testing…' },
};

function StatusBadge({ status }: { status: string }) {
  const style = STATUS_MAP[status.toLowerCase()] ?? STATUS_MAP.disconnected;
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 10px',
        borderRadius: 9999,
        background: style.bg,
        color: style.color,
        fontSize: '0.68rem',
        fontWeight: 600,
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: style.color,
          display: 'inline-block',
        }}
      />
      {style.label}
    </span>
  );
}

export default function InspectorPanel({ node, onClose, onRefresh, onNavigate: _onNavigate }: InspectorPanelProps) {
  const navigate = useNavigate();

  if (!node) {
    return (
      <div
        style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--glass-border)',
          borderRadius: 12,
          padding: 24,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 12,
          color: 'var(--text-muted)',
          textAlign: 'center',
          minWidth: 300,
        }}
      >
        <div
          style={{
            width: 48,
            height: 48,
            borderRadius: 12,
            background: 'var(--bg-elevated)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Info size={22} style={{ color: 'var(--text-primary)' }} />
        </div>
        <div>
          <p style={{ fontSize: '0.82rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
            Inspector
          </p>
          <p style={{ fontSize: '0.73rem', lineHeight: 1.5 }}>
            Click any node to inspect its metadata, columns, and relationships.
          </p>
        </div>
      </div>
    );
  }

  const renderContent = () => {
    if (node.type === 'root') {
      return (
        <>
          <Section title="Pivota Intelligence Layer">
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
              The central intelligence layer connecting all your external data systems. Click a provider node to explore its structure.
            </p>
          </Section>
        </>
      );
    }

    if (node.type === 'provider') {
      const meta = node.metadata as ProviderMetadata;
      return (
        <>
          <Section title="Connection">
            <Row label="Status" value={<StatusBadge status={meta.connection_status} />} />
            <Row label="Provider" value={getProviderLabel(meta.provider_type)} />
            <Row label="Environment" value={meta.environment} />
            {meta.host && <Row label="Host" value={meta.host} mono />}
            {meta.port && <Row label="Port" value={String(meta.port)} mono />}
          </Section>

          <Section title="Catalog">
            <Row label="Databases" value={meta.databases_count ?? '–'} />
            <Row label="Tables" value={meta.tables_count ?? '–'} />
            <Row label="Columns" value={meta.columns_count ?? '–'} />
          </Section>

          {(meta.last_tested_at || meta.last_sync_at) && (
            <Section title="Sync">
              {meta.last_tested_at && (
                <Row label="Last Tested" value={new Date(meta.last_tested_at).toLocaleString()} />
              )}
              {meta.last_sync_at && (
                <Row label="Last Sync" value={new Date(meta.last_sync_at).toLocaleString()} />
              )}
            </Section>
          )}

          <button
            onClick={() => onRefresh(node.id)}
            className="btn-ghost"
            style={{
              width: '100%',
              justifyContent: 'center',
              fontSize: '0.78rem',
              padding: '9px 0',
              marginTop: 4,
            }}
          >
            <RefreshCw size={13} /> Refresh Metadata
          </button>
        </>
      );
    }

    if (node.type === 'database') {
      return (
        <>
          <Section title="Database">
            <Row label="Name" value={node.label} mono />
          </Section>
        </>
      );
    }

    if (node.type === 'schema') {
      return (
        <>
          <Section title="Schema">
            <Row label="Name" value={node.label} mono />
          </Section>
        </>
      );
    }

    if (node.type === 'table') {
      const meta = node.metadata as any;
      const columns = meta.columns ?? [];
      const outbound = meta.relationships_outbound ?? [];
      const inbound = meta.relationships_inbound ?? [];
      const indexes = meta.indexes ?? [];

      return (
        <>
          <Section title="Table Information">
            <Row label="Type" value={
              <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.7rem' }}>
                {meta.type}
              </span>
            } />
            <Row label="Database" value={meta.database_name} mono />
            <Row label="Schema" value={meta.schema_name} mono />
            {meta.row_count_estimate > 0 && (
              <Row label="Rows (est.)" value={meta.row_count_estimate.toLocaleString()} />
            )}
            {meta.description && (
              <p style={{ fontSize: '0.73rem', color: 'var(--text-secondary)', lineHeight: 1.5, marginTop: 8 }}>
                {meta.description}
              </p>
            )}
          </Section>

          {columns.length > 0 && (
            <Section title={`Columns (${columns.length})`}>
              <div
                style={{
                  maxHeight: 200,
                  overflowY: 'auto',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 3,
                }}
              >
                {columns.map((col: any) => (
                  <div
                    key={col.id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '4px 8px',
                      background: 'var(--bg-elevated)',
                      borderRadius: 6,
                      gap: 8,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {col.is_primary_key && (
                        <span style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--text-primary)', flexShrink: 0, display: 'inline-block' }} />
                      )}
                      {col.is_foreign_key && !col.is_primary_key && (
                        <Link2 size={9} style={{ color: 'var(--text-muted)', flexShrink: 0 }} />
                      )}
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: col.is_primary_key ? 700 : 400,
                          color: 'var(--text-primary)',
                          fontFamily: "'JetBrains Mono', monospace",
                        }}
                      >
                        {col.name}
                      </span>
                    </div>
                    <span
                      style={{
                        fontSize: '0.65rem',
                        color: 'var(--text-muted)',
                        fontFamily: "'JetBrains Mono', monospace",
                        flexShrink: 0,
                      }}
                    >
                      {col.native_type || col.data_type}
                    </span>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {(outbound.length > 0 || inbound.length > 0) && (
            <Section title="Relationships">
              {outbound.map((rel: any) => (
                <div key={rel.id} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 0', fontSize: '0.72rem' }}>
                  <ChevronRight size={10} style={{ color: 'var(--text-primary)', flexShrink: 0 }} />
                  <span style={{ color: 'var(--text-muted)' }}>References</span>
                  <span style={{ color: 'var(--text-primary)', fontFamily: 'monospace' }}>
                    {rel.to_table_name}
                  </span>
                </div>
              ))}
              {inbound.map((rel: any) => (
                <div key={rel.id} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 0', fontSize: '0.72rem' }}>
                  <ChevronRight size={10} style={{ color: 'var(--text-muted)', flexShrink: 0, transform: 'rotate(180deg)' }} />
                  <span style={{ color: 'var(--text-muted)' }}>Referenced by</span>
                  <span style={{ color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
                    {rel.from_table_name}
                  </span>
                </div>
              ))}
            </Section>
          )}

          {indexes.length > 0 && (
            <Section title={`Indexes (${indexes.length})`}>
              {indexes.slice(0, 4).map((idx: any) => (
                <div key={idx.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '3px 0', fontSize: '0.7rem' }}>
                  <span style={{ color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{idx.name}</span>
                  {idx.unique && (
                    <span style={{ color: 'var(--text-primary)', fontSize: '0.62rem', fontWeight: 700 }}>UNIQUE</span>
                  )}
                </div>
              ))}
            </Section>
          )}

          <button
            onClick={() => navigate(`/catalog?objectId=${node.id.replace('table-', '')}`)}
            className="btn-primary"
            style={{
              width: '100%',
              justifyContent: 'center',
              fontSize: '0.78rem',
              padding: '9px 0',
            }}
          >
            <ExternalLink size={13} /> Open in Catalog
          </button>
        </>
      );
    }

    return null;
  };

  const nodeTypeIcon = {
    root: <Network size={16} style={{ color: 'var(--text-primary)' }} />,
    provider: <Database size={16} style={{ color: 'var(--text-primary)' }} />,
    database: <Database size={16} style={{ color: 'var(--text-primary)' }} />,
    schema: <Layers size={16} style={{ color: 'var(--text-primary)' }} />,
    table: <Table2 size={16} style={{ color: 'var(--text-primary)' }} />,
    column: <BarChart3 size={16} style={{ color: 'var(--text-primary)' }} />,
  }[node.type];

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--glass-border)',
        borderRadius: 12,
        padding: 20,
        display: 'flex',
        flexDirection: 'column',
        gap: 0,
        overflowY: 'auto',
        minWidth: 300,
        maxWidth: 340,
      }}
    >
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          marginBottom: 18,
          paddingBottom: 14,
          borderBottom: '1px solid var(--border-default)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: 10,
              background: 'var(--bg-elevated)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            {nodeTypeIcon}
          </div>
          <div>
            <h3 style={{ fontSize: '0.9rem', fontWeight: 700, margin: 0, color: 'var(--text-primary)' }}>
              {node.label}
            </h3>
            <p style={{ fontSize: '0.68rem', color: 'var(--text-muted)', margin: 0, marginTop: 2, textTransform: 'capitalize' }}>
              {node.type}
            </p>
          </div>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: 'var(--text-muted)',
            display: 'flex',
            padding: 4,
            borderRadius: 6,
          }}
        >
          <X size={15} />
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: 1 }}>{renderContent()}</div>
    </div>
  );
}
