/**
 * Empty State — Shown when no data sources are connected.
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusCircle, Network } from 'lucide-react';

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
      {/* Central pulsing circle */}
      <div style={{ position: 'relative', marginBottom: 8 }}>
        <div
          style={{
            width: 100,
            height: 100,
            borderRadius: '50%',
            background: 'rgba(99,102,241,0.06)',
            border: '1px solid rgba(99,102,241,0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            animation: 'rootPulse 3s ease-in-out infinite',
          }}
        >
          <div
            style={{
              width: 70,
              height: 70,
              borderRadius: '50%',
              background: 'var(--brand-gradient)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 30px rgba(99,102,241,0.3)',
            }}
          >
            <Network size={30} color="white" />
          </div>
        </div>
        {/* Orbit rings */}
        <div
          style={{
            position: 'absolute',
            inset: -20,
            borderRadius: '50%',
            border: '1px dashed rgba(99,102,241,0.1)',
            animation: 'spin 20s linear infinite',
          }}
        />
        <div
          style={{
            position: 'absolute',
            inset: -40,
            borderRadius: '50%',
            border: '1px dashed rgba(99,102,241,0.06)',
            animation: 'spin 30s linear infinite reverse',
          }}
        />
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

      {/* Hint chips */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'center', marginTop: 8 }}>
        {['PostgreSQL', 'MongoDB', 'MySQL', 'Snowflake', 'BigQuery'].map((p) => (
          <span
            key={p}
            style={{
              padding: '4px 12px',
              borderRadius: 20,
              background: 'rgba(99,102,241,0.06)',
              border: '1px solid rgba(99,102,241,0.12)',
              color: 'var(--text-muted)',
              fontSize: '0.72rem',
              fontWeight: 500,
            }}
          >
            {p}
          </span>
        ))}
      </div>
    </div>
  );
}
