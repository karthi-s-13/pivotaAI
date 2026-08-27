/**
 * Data Map Legend — Collapsible node/edge type key.
 *
 * Node types are distinguished by shape/stroke treatment (dashed vs
 * solid, filled vs outlined) rather than color — matching how the
 * canvas itself differentiates them.
 */

import React, { useState } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

export default function DataMapLegend() {
  const [open, setOpen] = useState(true);

  const nodeTypes: Array<{ label: string; render: () => React.ReactNode }> = [
    {
      label: 'Pivota Root',
      render: () => (
        <svg width={12} height={12}>
          <circle cx={6} cy={6} r={5} fill="#000000" />
        </svg>
      ),
    },
    {
      label: 'Provider',
      render: () => (
        <svg width={14} height={9}>
          <rect width={14} height={9} rx={2} fill="#ffffff" stroke="#111827" strokeWidth={1.2} />
        </svg>
      ),
    },
    {
      label: 'Database',
      render: () => (
        <svg width={14} height={9}>
          <rect width={14} height={9} rx={2} fill="#ffffff" stroke="#374151" strokeWidth={1} />
        </svg>
      ),
    },
    {
      label: 'Schema',
      render: () => (
        <svg width={14} height={9}>
          <rect width={14} height={9} rx={2} fill="#ffffff" stroke="#9ca3af" strokeWidth={1} strokeDasharray="3 2" />
        </svg>
      ),
    },
    {
      label: 'Table / View',
      render: () => (
        <svg width={14} height={9}>
          <rect width={14} height={9} rx={2} fill="#ffffff" stroke="#374151" strokeWidth={1} />
        </svg>
      ),
    },
  ];

  const edgeTypes = [
    { dash: false, label: 'Hierarchy' },
    { dash: true, label: 'FK Relationship' },
  ];

  return (
    <div
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--glass-border)',
        borderRadius: 10,
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
                {t.render()}
                <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{t.label}</span>
              </div>
            ))}
          </div>

          {/* Divider */}
          <div style={{ height: 1, background: 'var(--glass-border)', opacity: 0.15, margin: '6px 0' }} />

          {/* Edge types */}
          {edgeTypes.map((e) => (
            <div key={e.label} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '2px 0' }}>
              <svg width={24} height={8}>
                <line
                  x1={0}
                  y1={4}
                  x2={24}
                  y2={4}
                  stroke="#374151"
                  strokeWidth={1.5}
                  strokeDasharray={e.dash ? '4 3' : '0'}
                />
              </svg>
              <span style={{ fontSize: '0.65rem', color: 'var(--text-secondary)' }}>{e.label}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
