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
  Key,
  Link2,
  ChevronRight,
  Layers,
  BarChart3,
} from 'lucide-react';
import type { DataMapNode, ProviderMetadata, TableMetadata } from '../types/dataMap.types';
import { getProviderColor, getProviderLabel } from '../types/dataMap.types';

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
          borderBottom: '1px solid rgba(148,163,184,0.06)',
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
        borderBottom: '1px solid rgba(148,163,184,0.04)',
      }}
    >
      <span style={{ fontSize: '0.73rem', color: 'var(--text-muted)', flexShrink: 0 }}>{label}</span>
      <span
        style={{
          fontSize: '0.73rem',
          color: 'var(--text-primary)',
          fontFamily: mono ? 'JetBrains Mono, monospace' : 'inherit',
          textAlign: 'right',
          wordBreak: 'break-all',
        }}
      >
        {value}
      </span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { color: string; bg: string; label: string }> = {
    connected: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', label: 'Connected' },
    healthy: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', label: 'Connected' },
    disconnected: { color: '#64748b', bg: 'rgba(100,116,139,0.12)', label: 'Disconnected' },
    idle: { color: '#64748b', bg: 'rgba(100,116,139,0.1)', label: 'Not Verified' },
    unknown: { color: '#64748b', bg: 'rgba(100,116,139,0.1)', label: 'Not Verified' },
    error: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'Error' },
    auth_failed: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'Auth Failed' },
    network_error: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'Network Error' },
    permission_denied: { color: '#ef4444', bg: 'rgba(239,68,68,0.12)', label: 'Permission Denied' },
    syncing: { color: '#f59e0b', bg: 'rgba(245,158,11,0.12)', label: 'Syncing' },
    testing: { color: '#6366f1', bg: 'rgba(99,102,241,0.12)', label: 'Testing…' },
    ready: { color: '#10b981', bg: 'rgba(16,185,129,0.12)', label: 'Ready' },
  };
  const style = map[status.toLowerCase()] ?? map.disconnected;
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: '2px 8px',
        borderRadius: 20,
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
          boxShadow: `0 0 5px ${style.color}`,
        }}
      />
      {style.label}
    </span>
  );
}

export default function InspectorPanel({ node, onClose, onRefresh, onNavigate }: InspectorPanelProps) {
  const navigate = useNavigate();

  if (!node) {
    return (
      <div
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-default)',
          borderRadius: 16,
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
            background: 'rgba(99,102,241,0.08)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Info size={22} style={{ color: 'var(--brand-primary)' }} />
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
      const color = getProviderColor(meta.provider_type);
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
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 8,
              padding: '9px 0',
              background: `${color}18`,
              border: `1px solid ${color}40`,
              borderRadius: 10,
              color: color,
              fontSize: '0.78rem',
              fontWeight: 600,
              cursor: 'pointer',
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

      const typeColor = meta.type === 'VIEW'
        ? '#8b5cf6'
        : meta.type === 'COLLECTION'
        ? '#10b981'
        : '#6366f1';

      return (
        <>
          <Section title="Table Information">
            <Row label="Type" value={
              <span style={{ color: typeColor, fontWeight: 700, fontSize: '0.7rem' }}>
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
                      background: 'rgba(255,255,255,0.02)',
                      borderRadius: 6,
                      gap: 8,
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      {col.is_primary_key && <Key size={9} style={{ color: '#f59e0b', flexShrink: 0 }} />}
                      {col.is_foreign_key && !col.is_primary_key && (
                        <Link2 size={9} style={{ color: '#10b981', flexShrink: 0 }} />
                      )}
                      <span
                        style={{
                          fontSize: '0.72rem',
                          fontWeight: col.is_primary_key ? 700 : 400,
                          color: col.is_primary_key ? '#fcd34d' : 'var(--text-primary)',
                          fontFamily: 'JetBrains Mono, monospace',
                        }}
                      >
                        {col.name}
                      </span>
                    </div>
                    <span
                      style={{
                        fontSize: '0.65rem',
                        color: typeColor,
                        fontFamily: 'JetBrains Mono, monospace',
                        opacity: 0.7,
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
                  <ChevronRight size={10} style={{ color: 'var(--brand-primary)', flexShrink: 0 }} />
                  <span style={{ color: 'var(--text-muted)' }}>References</span>
                  <span style={{ color: 'var(--brand-primary-light)', fontFamily: 'monospace' }}>
                    {rel.to_table_name}
                  </span>
                </div>
              ))}
              {inbound.map((rel: any) => (
                <div key={rel.id} style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '4px 0', fontSize: '0.72rem' }}>
                  <ChevronRight size={10} style={{ color: '#10b981', flexShrink: 0, transform: 'rotate(180deg)' }} />
                  <span style={{ color: 'var(--text-muted)' }}>Referenced by</span>
                  <span style={{ color: '#6ee7b7', fontFamily: 'monospace' }}>
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
                    <span style={{ color: '#a78bfa', fontSize: '0.62rem', fontWeight: 700 }}>UNIQUE</span>
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
    root: <Network size={16} style={{ color: 'var(--brand-primary)' }} />,
    provider: <Database size={16} style={{ color: '#6366f1' }} />,
    database: <Database size={16} style={{ color: '#6366f1' }} />,
    schema: <Layers size={16} style={{ color: '#8b5cf6' }} />,
    table: <Table2 size={16} style={{ color: '#6366f1' }} />,
    column: <BarChart3 size={16} style={{ color: '#6366f1' }} />,
  }[node.type];

  return (
    <div
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-default)',
        borderRadius: 16,
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
              background: 'rgba(99,102,241,0.1)',
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
