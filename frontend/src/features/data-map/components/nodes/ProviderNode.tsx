/**
 * Provider Node — Represents a connected data source.
 *
 * The only accent color allowed here is the real provider brand
 * color (PostgreSQL blue, MongoDB green, etc.) shown as a thin left
 * border stripe — the sanctioned "brand recognition" exception.
 * Everything else is black / white / gray, and status is conveyed
 * only through the shared status tokens.
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

/** Shared status → token color mapping, consistent with StatusIndicator. */
function statusColorVar(isError: boolean, isSyncing: boolean, isConnected: boolean): string {
  if (isError) return 'var(--status-error)';
  if (isSyncing) return 'var(--status-info)';
  if (isConnected) return 'var(--status-success)';
  return 'var(--text-disabled)';
}

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

  const statusColor = statusColorVar(isError, isSyncing, isConnected);

  const borderColor = selected ? '#000000' : highlighted ? '#111827' : '#d1d5db';

  const opacity = highlighted ? 1 : 0.92;

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
      {/* Card background */}
      <rect
        width={W}
        height={H}
        rx={12}
        fill="#ffffff"
        stroke={borderColor}
        strokeWidth={selected ? 2 : 1.2}
        style={{ transition: 'stroke 0.2s' }}
      />

      {/* Left stripe — the one sanctioned brand-color accent */}
      <rect x={0} y={0} width={3} height={H} rx={1.5} fill={color} />

      {/* Provider icon circle — neutral, no brand color */}
      <circle cx={32} cy={H / 2} r={18} fill="#f3f4f6" stroke="#e5e7eb" strokeWidth={1} />
      <text
        x={32}
        y={H / 2 + 4}
        textAnchor="middle"
        fill="#111827"
        fontSize="9"
        fontWeight="800"
        fontFamily="'JetBrains Mono', monospace"
        style={{ pointerEvents: 'none' }}
      >
        {abbrev}
      </text>

      {/* Status dot — shared status tokens only */}
      <circle cx={W - 14} cy={14} r={5} style={{ fill: statusColor }} />

      {/* Provider name */}
      <text
        x={56}
        y={28}
        fill="#111827"
        fontSize="12"
        fontWeight="700"
        fontFamily="'Open Sans', sans-serif"
        style={{ pointerEvents: 'none' }}
      >
        {label.length > 14 ? label.slice(0, 13) + '…' : label}
      </text>

      {/* Provider type subtitle */}
      <text
        x={56}
        y={44}
        fill="#6b7280"
        fontSize="8.5"
        fontWeight="600"
        fontFamily="'Open Sans', sans-serif"
        style={{ pointerEvents: 'none' }}
      >
        {providerLabel}
      </text>

      {/* DB count badge — neutral pill */}
      {metadata.databases_count > 0 && (
        <>
          <rect x={56} y={52} width={48} height={14} rx={7} fill="#f3f4f6" />
          <text
            x={80}
            y={62}
            textAnchor="middle"
            fill="#374151"
            fontSize="8"
            fontWeight="700"
            fontFamily="'Open Sans', sans-serif"
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
          <path d="M4,14 L10,6 L16,14" fill="none" stroke="#6b7280" strokeWidth="1.8" />
        ) : (
          <path d="M4,6 L10,14 L16,6" fill="none" stroke="#6b7280" strokeWidth="1.8" />
        )}
      </g>

      {/* Error overlay — only for genuine connection failures */}
      {isError && (
        <>
          <rect width={W} height={H} rx={12} fill="var(--status-error-bg)" style={{ pointerEvents: 'none' }} />
          <text x={W / 2} y={H - 8} textAnchor="middle" fill="var(--status-error)" fontSize="7.5" fontWeight="600" style={{ pointerEvents: 'none' }}>
            Connection Error
          </text>
        </>
      )}

      {/* Syncing indicator */}
      {isSyncing && (
        <text x={W / 2} y={H - 8} textAnchor="middle" fill="var(--status-info)" fontSize="7.5" fontWeight="600" style={{ pointerEvents: 'none' }}>
          Syncing…
        </text>
      )}
    </g>
  );
});
