/**
 * Data Map Legend — Collapsible node/edge type key.
 */

import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

export default function DataMapLegend() {
  const [open, setOpen] = useState(true);

  const nodeTypes = [
    { color: '#6366f1', label: 'Pivota Root', shape: 'circle' },
    { color: '#6366f1', label: 'Provider', shape: 'rect' },
    { color: '#6366f1', label: 'Database', shape: 'rect' },
    { color: '#8b5cf6', label: 'Schema', shape: 'rect' },
    { color: '#6366f1', label: 'Table / View', shape: 'rect' },
  ];

  const edgeTypes = [
    { color: 'rgba(99,102,241,0.5)', dash: false, label: 'Hierarchy' },
    { color: 'rgba(16,185,129,0.6)', dash: true, label: 'FK Relationship' },
  ];

  return (
    <div
      style={{
        background: 'rgba(17,24,39,0.88)',
        backdropFilter: 'blur(14px)',
        WebkitBackdropFilter: 'blur(14px)',
        border: '1px solid rgba(148,163,184,0.08)',
        borderRadius: 12,
        overflow: 'hidden',
        minWidth: 150,
      }}
    >
      {/* Toggle header */}
      <button
        onClick={() => setOpen(!open)}
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '7px 12px',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          color: 'var(--text-muted)',
          fontSize: '0.65rem',
          fontWeight: 700,
          letterSpacing: 1,
          textTransform: 'uppercase',
        }}
      >
        Legend
        {open ? <ChevronDown size={11} /> : <ChevronUp size={11} />}
      </button>

      {open && (
        <div style={{ padding: '4px 12px 10px' }}>
          {/* Node types */}
          <div style={{ marginBottom: 8 }}>
            {nodeTypes.map((t) => (
              <div key={t.label} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '2px 0' }}>
                {t.shape === 'circle' ? (
                  <svg width={12} height={12}>
                    <circle cx={6} cy={6} r={5} fill={t.color} opacity={0.8} />
                  </svg>
                ) : (
                  <svg width={12} height={8}>
                    <rect width={12} height={8} rx={2} fill={t.color} opacity={0.3} stroke={t.color} strokeWidth={1} />
                  </svg>
                )}
                <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{t.label}</span>
              </div>
            ))}
          </div>

          {/* Divider */}
          <div style={{ height: 1, background: 'rgba(148,163,184,0.06)', margin: '6px 0' }} />

          {/* Edge types */}
          {edgeTypes.map((e) => (
            <div key={e.label} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '2px 0' }}>
              <svg width={24} height={8}>
                <line
                  x1={0}
                  y1={4}
                  x2={24}
                  y2={4}
                  stroke={e.color}
                  strokeWidth={1.5}
                  strokeDasharray={e.dash ? '4 3' : '0'}
                />
              </svg>
              <span style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>{e.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
