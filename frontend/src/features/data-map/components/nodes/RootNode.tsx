/**
 * Pivota Root Node — Central intelligence node.
 * Renders the Pivota logo as a black circular badge at the center
 * of the constellation (Codex: black is the sole surface tone for
 * elevated elements).
 */

import React from 'react';

interface RootNodeProps {
  x: number;
  y: number;
  selected: boolean;
  highlighted: boolean;
  onClick: () => void;
}

export const RootNode = React.memo(function RootNode({
  x,
  y,
  selected,
  onClick,
}: RootNodeProps) {
  const cx = x;
  const cy = y;
  const r = 44;

  return (
    <g
      transform={`translate(${cx}, ${cy})`}
      style={{ cursor: 'pointer' }}
      onClick={onClick}
    >
      {/* Selection ring */}
      {selected && (
        <circle r={r + 8} fill="none" stroke="#000000" strokeWidth={1.5} />
      )}

      {/* Main circle body — black badge (Codex glass-card surface) */}
      <circle r={r} fill="#000000" stroke="#000000" strokeWidth={1.5} />

      {/* Compass / logo icon — simplified SVG compass */}
      <g style={{ pointerEvents: 'none' }}>
        {/* Outer ring */}
        <circle r={24} fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth={1} />
        {/* North pointer */}
        <polygon points="0,-18 -5,-2 5,-2" fill="#ffffff" />
        {/* South pointer */}
        <polygon points="0,18 -5,2 5,2" fill="rgba(255,255,255,0.5)" />
        {/* East pointer */}
        <polygon points="18,0 2,-5 2,5" fill="rgba(255,255,255,0.5)" />
        {/* West pointer */}
        <polygon points="-18,0 -2,-5 -2,5" fill="rgba(255,255,255,0.5)" />
        {/* Center dot */}
        <circle r={4} fill="#ffffff" />
      </g>

      {/* Label: PIVOTA */}
      <text
        y={r + 20}
        textAnchor="middle"
        fill="#111827"
        fontSize="11"
        fontWeight="800"
        fontFamily="'Open Sans', sans-serif"
        letterSpacing="2"
        style={{ pointerEvents: 'none' }}
      >
        PIVOTA
      </text>

      {/* Sub-label */}
      <text
        y={r + 34}
        textAnchor="middle"
        fill="#6b7280"
        fontSize="7.5"
        fontFamily="'Open Sans', sans-serif"
        letterSpacing="0.5"
        style={{ pointerEvents: 'none' }}
      >
        Unified Data Intelligence
      </text>
    </g>
  );
});
