/**
 * Provider Indicator.
 *
 * Compact provider icon/badge. Maps provider strings to color and label.
 */

import { Database } from 'lucide-react';
import { PROVIDER_META } from '../api/dashboardApi';

interface ProviderIndicatorProps {
  provider: string;
  size?: 'sm' | 'md';
  showLabel?: boolean;
}

export default function ProviderIndicator({ provider, size = 'md', showLabel = true }: ProviderIndicatorProps) {
  const meta = PROVIDER_META[provider] || { label: provider, color: 'var(--text-muted)', bgColor: 'rgba(148, 163, 184, 0.12)' };
  const iconSize = size === 'sm' ? 14 : 16;
  const boxSize = size === 'sm' ? 28 : 34;

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: size === 'sm' ? 6 : 10 }}>
      <div
        style={{
          width: boxSize,
          height: boxSize,
          borderRadius: size === 'sm' ? 6 : 8,
          background: meta.bgColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
      >
        <Database size={iconSize} style={{ color: meta.color }} />
      </div>
      {showLabel && (
        <span style={{ fontSize: size === 'sm' ? '0.72rem' : '0.82rem', fontWeight: 500, color: 'var(--text-primary)' }}>
          {meta.label}
        </span>
      )}
    </div>
  );
}
