/**
 * Database Node — Represents a discovered database.
 */

import React from 'react';
import type { DatabaseMetadata } from '../../types/dataMap.types';

interface DatabaseNodeProps {
  x: number;
  y: number;
  label: string;
  metadata: DatabaseMetadata;
  selected: boolean;
  highlighted: boolean;
  expanded: boolean;
  status: string;
  onSingleClick: () => void;
  onDoubleClick: () => void;
  onContextMenu: (e: React.MouseEvent) => void;
}

const W = 148;
const H = 62;

export const DatabaseNode = React.memo(function DatabaseNode({
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
}: DatabaseNodeProps) {
  const px = x - W / 2;
  const py = y - H / 2;

  const borderColor = selected
    ? '#818cf8'
    : highlighted
    ? 'rgba(99,102,241,0.4)'
    : 'rgba(148,163,184,0.1)';

  const isLoading = status === 'loading';
  const opacity = highlighted ? 1 : 0.9;

  return (
    <g
      transform={`translate(${px}, ${py})`}
      style={{ cursor: 'pointer', opacity }}
      onClick={onSingleClick}
      onDoubleClick={onDoubleClick}
      onContextMenu={onContextMenu}
    >
      {/* Shadow */}
      <rect width={W} height={H} rx={10} fill="rgba(0,0,0,0.25)" transform="translate(1.5,2.5)" />

      {/* Background */}
      <rect
        width={W}
        height={H}
        rx={10}
        fill="#111827"
        stroke={borderColor}
        strokeWidth={selected ? 2 : 1.2}
        style={{
          filter: selected ? 'drop-shadow(0 0 10px rgba(99,102,241,0.2))' : 'none',
          transition: 'stroke 0.2s',
        }}
      />

      {/* Top accent line */}
      <rect
        width={W}
        height={3}
        rx={1.5}
        fill={selected ? '#6366f1' : 'rgba(99,102,241,0.4)'}
        style={{ pointerEvents: 'none' }}
      />

      {/* Database cylinder icon (simplified) */}
      <g transform="translate(14, 12)" style={{ pointerEvents: 'none' }}>
        <ellipse cx={11} cy={4} rx={11} ry={4} fill="rgba(99,102,241,0.2)" stroke="rgba(99,102,241,0.4)" strokeWidth={1} />
        <rect x={0} y={4} width={22} height={16} fill="rgba(99,102,241,0.08)" />
        <ellipse cx={11} cy={20} rx={11} ry={4} fill="rgba(99,102,241,0.2)" stroke="rgba(99,102,241,0.4)" strokeWidth={1} />
        {/* Horizontal lines on cylinder */}
        <line x1={0} y1={9} x2={22} y2={9} stroke="rgba(99,102,241,0.2)" strokeWidth={0.8} />
        <line x1={0} y1={14} x2={22} y2={14} stroke="rgba(99,102,241,0.2)" strokeWidth={0.8} />
      </g>

      {/* Label */}
      <text
        x={50}
        y={26}
        fill="#e2e8f0"
        fontSize="11"
        fontWeight="700"
        fontFamily="Inter, sans-serif"
        style={{ pointerEvents: 'none' }}
      >
        {label.length > 13 ? label.slice(0, 12) + '…' : label}
      </text>

      {/* Subtitle */}
      <text
        x={50}
        y={40}
        fill="rgba(148,163,184,0.6)"
        fontSize="8"
        fontFamily="Inter, sans-serif"
        style={{ pointerEvents: 'none' }}
      >
        {isLoading ? 'Loading schemas…' : 'Database'}
      </text>

      {/* Expand chevron */}
      <g
        transform={`translate(${W - 20}, ${H / 2 - 12})`}
        onClick={(e) => {
          e.stopPropagation();
          onDoubleClick();
        }}
        style={{ cursor: 'pointer' }}
      >
        <rect x={-4} y={-4} width={24} height={24} fill="transparent" />
        {expanded ? (
          <path d="M4,13 L9,6 L14,13" fill="none" stroke="rgba(148,163,184,0.6)" strokeWidth="1.6" />
        ) : (
          <path d="M4,6 L9,13 L14,6" fill="none" stroke="rgba(148,163,184,0.6)" strokeWidth="1.6" />
        )}
      </g>
    </g>
  );
});
