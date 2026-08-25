/**
 * Pivota Root Node — Central intelligence node.
 * Renders the animated Pivota logo at the center of the constellation.
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
  highlighted,
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
      {/* Outer ambient glow ring */}
      <circle
        r={r + 22}
        fill="none"
        stroke="rgba(99,102,241,0.12)"
        strokeWidth={16}
        style={{ animation: 'rootPulse 3s ease-in-out infinite' }}
      />

      {/* Mid glow ring */}
      <circle
        r={r + 10}
        fill="none"
        stroke={selected ? 'rgba(99,102,241,0.35)' : 'rgba(99,102,241,0.18)'}
        strokeWidth={2}
        style={{ animation: 'rootPulse 3s ease-in-out infinite 0.5s' }}
      />

      {/* Main circle body */}
      <circle
        r={r}
        fill="url(#rootGradient)"
        stroke={selected ? '#818cf8' : 'rgba(99,102,241,0.5)'}
        strokeWidth={selected ? 2.5 : 1.5}
        style={{
          filter: 'drop-shadow(0 0 16px rgba(99,102,241,0.4))',
        }}
      />

      {/* Defs: gradient for root */}
      <defs>
        <radialGradient id="rootGradient" cx="40%" cy="35%" r="65%">
          <stop offset="0%" stopColor="#818cf8" />
          <stop offset="50%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#4338ca" />
        </radialGradient>
      </defs>

      {/* Compass / logo icon — simplified SVG compass */}
      <g style={{ pointerEvents: 'none' }}>
        {/* Outer ring */}
        <circle r={24} fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth={1} />
        {/* North pointer */}
        <polygon points="0,-18 -5,-2 5,-2" fill="white" opacity={0.95} />
        {/* South pointer */}
        <polygon points="0,18 -5,2 5,2" fill="rgba(255,255,255,0.45)" />
        {/* East pointer */}
        <polygon points="18,0 2,-5 2,5" fill="rgba(255,255,255,0.45)" />
        {/* West pointer */}
        <polygon points="-18,0 -2,-5 -2,5" fill="rgba(255,255,255,0.45)" />
        {/* Center dot */}
        <circle r={4} fill="white" />
      </g>

      {/* Label: PIVOTA */}
      <text
        y={r + 18}
        textAnchor="middle"
        fill="#f1f5f9"
        fontSize="11"
        fontWeight="800"
        fontFamily="Inter, sans-serif"
        letterSpacing="2"
        style={{ pointerEvents: 'none' }}
      >
        PIVOTA
      </text>

      {/* Sub-label */}
      <text
        y={r + 31}
        textAnchor="middle"
        fill="rgba(148,163,184,0.7)"
        fontSize="7.5"
        fontFamily="Inter, sans-serif"
        letterSpacing="0.5"
        style={{ pointerEvents: 'none' }}
      >
        Unified Data Intelligence
      </text>
    </g>
  );
});
