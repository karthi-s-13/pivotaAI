/**
 * Edge Components — Hierarchy and Relationship edges.
 * Hierarchy: solid curved line from parent to child.
 * Relationship: dashed FK connection between table nodes.
 */

import React from 'react';
import type { DataMapNode, DataMapEdge } from '../../types/dataMap.types';

// ─────────────────────────────────────────────
// Bezier path helper
// ─────────────────────────────────────────────

function cubicBezierPath(
  x1: number,
  y1: number,
  x2: number,
  y2: number
): string {
  const dx = x2 - x1;
  const dy = y2 - y1;
  const dist = Math.sqrt(dx * dx + dy * dy);
  const curve = Math.min(dist * 0.45, 100);

  const mx = (x1 + x2) / 2;
  const my = (y1 + y2) / 2;

  // Perpendicular offset for slight curve
  const nx = -dy / dist;
  const ny = dx / dist;

  const cx1 = x1 + dx * 0.35;
  const cy1 = y1 + dy * 0.15;
  const cx2 = x2 - dx * 0.35;
  const cy2 = y2 - dy * 0.15;

  return `M ${x1} ${y1} C ${cx1} ${cy1}, ${cx2} ${cy2}, ${x2} ${y2}`;
}

// ─────────────────────────────────────────────
// Hierarchy Edge
// ─────────────────────────────────────────────

interface HierarchyEdgeProps {
  edge: DataMapEdge;
  sourceNode: DataMapNode;
  targetNode: DataMapNode;
  isHighlighted: boolean;
  isSelected: boolean;
}

export const HierarchyEdge = React.memo(function HierarchyEdge({
  edge,
  sourceNode,
  targetNode,
  isHighlighted,
  isSelected,
}: HierarchyEdgeProps) {
  const path = cubicBezierPath(
    sourceNode.x,
    sourceNode.y,
    targetNode.x,
    targetNode.y
  );

  const stroke = isSelected
    ? 'rgba(129,140,248,0.7)'
    : isHighlighted
    ? 'rgba(99,102,241,0.4)'
    : 'rgba(99,102,241,0.15)';

  const strokeWidth = isSelected ? 2.5 : isHighlighted ? 1.8 : 1;

  return (
    <g>
      {/* Broad invisible hit area */}
      <path
        d={path}
        fill="none"
        stroke="transparent"
        strokeWidth={12}
        style={{ cursor: 'default' }}
      />
      {/* Visible path */}
      <path
        d={path}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        style={{
          transition: 'stroke 0.2s, stroke-width 0.2s',
          pointerEvents: 'none',
        }}
      />
    </g>
  );
});

// ─────────────────────────────────────────────
// Relationship Edge (FK connections)
// ─────────────────────────────────────────────

interface RelationshipEdgeProps {
  edge: DataMapEdge;
  sourceNode: DataMapNode;
  targetNode: DataMapNode;
  isHighlighted: boolean;
  isSelected: boolean;
  markerId: string;
}

export const RelationshipEdge = React.memo(function RelationshipEdge({
  edge,
  sourceNode,
  targetNode,
  isHighlighted,
  isSelected,
  markerId,
}: RelationshipEdgeProps) {
  const path = cubicBezierPath(
    sourceNode.x,
    sourceNode.y,
    targetNode.x,
    targetNode.y
  );

  const stroke = isSelected
    ? 'rgba(16,185,129,0.9)'
    : isHighlighted
    ? 'rgba(16,185,129,0.6)'
    : 'rgba(16,185,129,0.22)';

  const strokeWidth = isSelected ? 2.5 : isHighlighted ? 2 : 1.2;

  return (
    <g>
      {/* Broad hit area */}
      <path
        d={path}
        fill="none"
        stroke="transparent"
        strokeWidth={14}
        style={{ cursor: 'pointer' }}
      />
      {/* Visible dashed path */}
      <path
        d={path}
        fill="none"
        stroke={stroke}
        strokeWidth={strokeWidth}
        strokeDasharray={isHighlighted ? '7 4' : '5 5'}
        markerEnd={`url(#${markerId})`}
        style={{
          transition: 'stroke 0.2s, stroke-width 0.2s',
          pointerEvents: 'none',
        }}
      />

      {/* Mid-point label for highlighted FK */}
      {isHighlighted && edge.label && (
        <FKLabel path={path} label={edge.label} />
      )}
    </g>
  );
});

// ─────────────────────────────────────────────
// FK Label at midpoint
// ─────────────────────────────────────────────

function FKLabel({ label }: { path: string; label: string }) {
  const truncated = label.length > 24 ? label.slice(0, 23) + '…' : label;
  const w = truncated.length * 5.5 + 12;
  const h = 16;
  return (
    <g>
      <rect
        x={-w / 2}
        y={-h / 2}
        width={w}
        height={h}
        rx={4}
        fill="#0d1526"
        stroke="rgba(16,185,129,0.35)"
        strokeWidth={1}
      />
      <text
        textAnchor="middle"
        dominantBaseline="middle"
        fill="rgba(16,185,129,0.9)"
        fontSize="7.5"
        fontFamily="JetBrains Mono, monospace"
      >
        {truncated}
      </text>
    </g>
  );
}

// ─────────────────────────────────────────────
// SVG Defs for markers
// ─────────────────────────────────────────────

export function EdgeMarkerDefs() {
  return (
    <defs>
      {/* Arrow for FK relationship edges */}
      <marker
        id="fk-arrow"
        viewBox="0 0 10 10"
        refX="8"
        refY="5"
        markerWidth="6"
        markerHeight="6"
        orient="auto-start-reverse"
      >
        <path d="M 0 1 L 9 5 L 0 9 z" fill="rgba(16,185,129,0.5)" />
      </marker>
      <marker
        id="fk-arrow-highlighted"
        viewBox="0 0 10 10"
        refX="8"
        refY="5"
        markerWidth="7"
        markerHeight="7"
        orient="auto-start-reverse"
      >
        <path d="M 0 1 L 9 5 L 0 9 z" fill="rgba(16,185,129,0.9)" />
      </marker>
    </defs>
  );
}
