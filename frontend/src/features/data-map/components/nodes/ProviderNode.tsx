/**
 * Provider Node — Represents a connected data source.
 */

import React from 'react';
import { getProviderColor, getProviderLabel } from '../../types/dataMap.types';
import type { ProviderMetadata } from '../../types/dataMap.types';

interface ProviderNodeProps {
  id: string;
  x: number;
  y: number;
  label: string;
  metadata: ProviderMetadata;
  selected: boolean;
  highlighted: boolean;
  expanded: boolean;
  status: string;
  onSingleClick: () => void;
  onDoubleClick: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
}

const W = 168;
const H = 76;

export const ProviderNode = React.memo(function ProviderNode({
  x,
  y,
  label,
  metadata,
  selected,
  highlighted,
  expanded,
  status,
  onSingleClick,
  onDoubleClick,
  onContextMenu,
}: ProviderNodeProps) {
  const px = x - W / 2;
  const py = y - H / 2;
  const color = getProviderColor(metadata.provider_type);
  const providerLabel = getProviderLabel(metadata.provider_type);

  const isConnected = metadata.connection_status === 'connected';
  const isError = status === 'error';
  const isSyncing = status === 'loading' || status === 'syncing' || metadata.health_status === 'syncing';
  const isIdle = status === 'idle' || (!isConnected && !isError && !isSyncing);

  const statusColor = isError
    ? '#ef4444'
    : isSyncing
    ? '#f59e0b'
    : isConnected
    ? '#10b981'
    : '#64748b'; // grey for idle/unknown

  const borderColor = selected
    ? '#818cf8'
    : highlighted
    ? `${color}80`
    : 'rgba(148,163,184,0.12)';

  const opacity = highlighted ? 1 : 0.88;

  // Provider type abbreviation icon
  const abbrev = metadata.provider_type.slice(0, 2).toUpperCase();

  return (
    <g
      transform={`translate(${px}, ${py})`}
      style={{ cursor: 'pointer', opacity }}
      onClick={onSingleClick}
      onDoubleClick={onDoubleClick}
      onContextMenu={onContextMenu}
    >
      {/* Drop shadow */}
      <rect
        width={W}
        height={H}
        rx={12}
        fill="rgba(0,0,0,0.3)"
        transform="translate(2,3)"
      />

      {/* Card background */}
      <rect
        width={W}
        height={H}
        rx={12}
        fill="#1a2235"
        stroke={borderColor}
        strokeWidth={selected ? 2 : 1.5}
        style={{
          filter: selected
            ? `drop-shadow(0 0 12px rgba(99,102,241,0.25))`
            : highlighted
            ? `drop-shadow(0 0 8px ${color}30)`
            : 'none',
          transition: 'stroke 0.2s, filter 0.2s',
        }}
      />

      {/* Left color stripe */}
      <rect width={4} height={H} rx={2} fill={color} opacity={0.9} />
      <rect x={0} y={0} width={4} height={H} rx={2} fill={color} />

      {/* Provider icon circle */}
      <circle cx={32} cy={H / 2} r={18} fill={`${color}22`} stroke={`${color}55`} strokeWidth={1} />
      <text
        x={32}
        y={H / 2 + 4}
        textAnchor="middle"
        fill={color}
        fontSize="9"
        fontWeight="800"
        fontFamily="JetBrains Mono, monospace"
        style={{ pointerEvents: 'none' }}
      >
        {abbrev}
      </text>

      {/* Status dot */}
      <circle cx={W - 14} cy={14} r={5} fill={statusColor} style={{ filter: `drop-shadow(0 0 4px ${statusColor})` }} />

      {/* Provider name */}
      <text
        x={56}
        y={28}
        fill="#f1f5f9"
        fontSize="12"
        fontWeight="700"
        fontFamily="Inter, sans-serif"
        style={{ pointerEvents: 'none' }}
      >
        {label.length > 14 ? label.slice(0, 13) + '…' : label}
      </text>

      {/* Provider type subtitle */}
      <text
        x={56}
        y={44}
        fill={color}
        fontSize="8.5"
        fontWeight="600"
        fontFamily="Inter, sans-serif"
        style={{ pointerEvents: 'none' }}
      >
        {providerLabel}
      </text>

      {/* DB count badge */}
      {metadata.databases_count > 0 && (
        <>
          <rect x={56} y={52} width={48} height={14} rx={4} fill={`${color}20`} />
          <text
            x={80}
            y={62}
            textAnchor="middle"
            fill={color}
            fontSize="8"
            fontWeight="700"
            fontFamily="Inter, sans-serif"
            style={{ pointerEvents: 'none' }}
          >
            {metadata.databases_count} {metadata.databases_count === 1 ? 'database' : 'databases'}
          </text>
        </>
      )}

      {/* Expand/collapse chevron */}
      <g
        transform={`translate(${W - 24}, ${H / 2 - 12})`}
        onClick={(e) => {
          e.stopPropagation();
          onDoubleClick();
        }}
        style={{ cursor: 'pointer' }}
      >
        <rect x={-4} y={-4} width={24} height={24} fill="transparent" />
        {expanded ? (
          <path d="M4,14 L10,6 L16,14" fill="none" stroke="rgba(148,163,184,0.7)" strokeWidth="1.8" />
        ) : (
          <path d="M4,6 L10,14 L16,6" fill="none" stroke="rgba(148,163,184,0.7)" strokeWidth="1.8" />
        )}
      </g>

      {/* Error overlay — only for genuine connection failures */}
      {isError && (
        <>
          <rect width={W} height={H} rx={12} fill="rgba(239,68,68,0.06)" style={{ pointerEvents: 'none' }} />
          <text x={W / 2} y={H - 8} textAnchor="middle" fill="#ef4444" fontSize="7.5" fontWeight="600" style={{ pointerEvents: 'none' }}>
            Connection Error
          </text>
        </>
      )}

      {/* Syncing indicator */}
      {isSyncing && (
        <text x={W / 2} y={H - 8} textAnchor="middle" fill="#f59e0b" fontSize="7.5" fontWeight="600" style={{ pointerEvents: 'none' }}>
          Syncing…
        </text>
      )}
    </g>
  );
});
