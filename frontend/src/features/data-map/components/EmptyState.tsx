/**
 * Empty State — Shown when no data sources are connected.
 */

import { useNavigate } from 'react-router-dom';
import { PlusCircle, Network } from 'lucide-react';
import { getProviderColor } from '../types/dataMap.types';

const SUGGESTED_PROVIDERS = ['PostgreSQL', 'MongoDB', 'MySQL', 'Snowflake', 'BigQuery'];

export default function EmptyState() {
  const navigate = useNavigate();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        flex: 1,
        gap: 20,
        textAlign: 'center',
        padding: 48,
      }}
    >
      {/* Central badge — black roundel, matching the root node */}
      <div style={{ position: 'relative', marginBottom: 8 }}>
        <div
          style={{
            width: 100,
            height: 100,
            borderRadius: '50%',
            background: '#ffffff',
            border: '1px solid var(--glass-border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <div
            style={{
              width: 70,
              height: 70,
              borderRadius: '50%',
              background: '#000000',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Network size={30} color="#ffffff" />
          </div>
        </div>
      </div>

      <div>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: 10, color: 'var(--text-primary)' }}>
          Your Data Map starts here
        </h2>
        <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', lineHeight: 1.7, maxWidth: 400 }}>
          Connect your first data source to begin mapping your data constellation.
          Pivota will automatically discover your databases, tables, columns, and relationships.
        </p>
      </div>

      <button
        onClick={() => navigate('/data-sources')}
        className="btn-primary"
        style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '12px 28px', fontSize: '0.88rem' }}
      >
        <PlusCircle size={16} />
        Add Data Source
      </button>

      {/* Hint chips — provider brand color shown as a thin accent border (sanctioned exception) */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', marginTop: 8 }}>
        {SUGGESTED_PROVIDERS.map((p) => {
          const accent = getProviderColor(p);
          return (
            <span
              key={p}
              style={{
                padding: '4px 12px',
                borderRadius: 9999,
                background: 'var(--bg-surface)',
                border: `1px solid ${accent}55`,
                color: 'var(--text-secondary)',
                fontSize: '0.72rem',
                fontWeight: 500,
              }}
            >
              {p}
            </span>
          );
        })}
      </div>
    </div>
  );
}
