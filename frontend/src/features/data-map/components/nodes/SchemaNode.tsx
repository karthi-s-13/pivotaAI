/**
 * Schema Node — Represents a database schema.
 * Visually de-emphasized as an intermediary node.
 */

import React from 'react';
import type { SchemaMetadata } from '../../types/dataMap.types';

interface SchemaNodeProps {
  x: number;
  y: number;
  label: string;
  metadata: SchemaMetadata;
  selected: boolean;
  highlighted: boolean;
  expanded: boolean;
  status: string;
  onSingleClick: () => void;
  onDoubleClick: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
}

const W = 130;
const H = 50;

export const SchemaNode = React.memo(function SchemaNode({
  x,
  y,
  label,
  selected,
  highlighted,
  expanded,
  status,
  onSingleClick,
  onDoubleClick,
  onContextMenu,
}: SchemaNodeProps) {
  const px = x - W / 2;
  const py = y - H / 2;

  const isLoading = status === 'loading';
  const opacity = highlighted ? 1 : 0.85;

  return (
    <g
      transform={`translate(${px}, ${py})`}
      style={{ cursor: 'pointer', opacity }}
      onClick={onSingleClick}
      onDoubleClick={onDoubleClick}
      onContextMenu={onContextMenu}
    >
      {/* Background */}
      <rect
        width={W}
        height={H}
        rx={8}
        fill="#0f1929"
        stroke={selected ? '#6366f1' : 'rgba(148,163,184,0.08)'}
        strokeWidth={selected ? 1.8 : 1}
        strokeDasharray={selected ? '0' : '4 3'}
        style={{ transition: 'stroke 0.2s' }}
      />

      {/* Icon: folder/schema symbol */}
      <g transform="translate(10, 12)" style={{ pointerEvents: 'none' }}>
        <rect width={18} height={13} rx={2} fill="rgba(139,92,246,0.2)" stroke="rgba(139,92,246,0.35)" strokeWidth={1} />
        <rect x={3} y={-3} width={10} height={5} rx={1.5} fill="rgba(139,92,246,0.3)" stroke="rgba(139,92,246,0.35)" strokeWidth={1} />
      </g>

      {/* Label */}
      <text
        x={36}
        y={22}
        fill="#c4b5fd"
        fontSize="10.5"
        fontWeight="600"
        fontFamily="Inter, sans-serif"
        style={{ pointerEvents: 'none' }}
      >
        {label.length > 12 ? label.slice(0, 11) + '…' : label}
      </text>

      {/* Subtitle */}
      <text
        x={36}
        y={36}
        fill="rgba(148,163,184,0.5)"
        fontSize="7.5"
        fontFamily="Inter, sans-serif"
        style={{ pointerEvents: 'none' }}
      >
        {isLoading ? 'Loading…' : 'Schema'}
      </text>

      {/* Expand chevron */}
      <g
        transform={`translate(${W - 18}, ${H / 2 - 10})`}
        onClick={(e) => {
          e.stopPropagation();
          onDoubleClick();
        }}
        style={{ cursor: 'pointer' }}
      >
        <rect x={-4} y={-4} width={20} height={20} fill="transparent" />
        {expanded ? (
          <path d="M2,11 L6,5 L10,11" fill="none" stroke="rgba(148,163,184,0.55)" strokeWidth="1.3" />
        ) : (
          <path d="M2,5 L6,11 L10,5" fill="none" stroke="rgba(148,163,184,0.55)" strokeWidth="1.3" />
        )}
      </g>
    </g>
  );
});
