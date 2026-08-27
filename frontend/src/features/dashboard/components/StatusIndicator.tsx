/**
 * Status Indicator.
 *
 * Reusable status dot + label. Maps connection status strings
 * to appropriate colors and icons.
 */

import { Loader2 } from 'lucide-react';

interface StatusIndicatorProps {
  status: string;
  showLabel?: boolean;
  size?: 'sm' | 'md';
}

const STATUS_CONFIG: Record<string, { color: string; label: string; bg: string }> = {
  healthy:    { color: 'var(--status-success)', label: 'Connected',  bg: 'var(--status-success-bg)' },
  connected:  { color: 'var(--status-success)', label: 'Connected',  bg: 'var(--status-success-bg)' },
  operational:{ color: 'var(--status-success)', label: 'Operational', bg: 'var(--status-success-bg)' },
  warning:    { color: 'var(--status-warning)', label: 'Warning',    bg: 'var(--status-warning-bg)' },
  degraded:   { color: 'var(--status-warning)', label: 'Degraded',   bg: 'var(--status-warning-bg)' },
  error:      { color: 'var(--status-error)',   label: 'Error',      bg: 'var(--status-error-bg)' },
  auth_failed:{ color: 'var(--status-error)',   label: 'Auth Failed', bg: 'var(--status-error-bg)' },
  network_error:{ color: 'var(--status-error)', label: 'Network Error', bg: 'var(--status-error-bg)' },
  permission_denied:{ color: 'var(--status-error)', label: 'Permission Denied', bg: 'var(--status-error-bg)' },
  down:       { color: 'var(--status-error)',   label: 'Down',       bg: 'var(--status-error-bg)' },
  syncing:    { color: 'var(--status-info)',    label: 'Syncing',    bg: 'var(--status-info-bg)' },
  disconnected:{ color: 'var(--text-disabled)', label: 'Disconnected', bg: 'var(--bg-elevated)' },
  unknown:    { color: 'var(--text-disabled)',  label: 'Unknown',    bg: 'var(--bg-elevated)' },
};

export default function StatusIndicator({ status, showLabel = true, size = 'md' }: StatusIndicatorProps) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.unknown;
  const dotSize = size === 'sm' ? 6 : 8;

  if (status === 'syncing') {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        <Loader2 size={dotSize + 4} className="animate-spin" style={{ color: config.color }} />
        {showLabel && (
          <span style={{ fontSize: size === 'sm' ? '0.68rem' : '0.75rem', fontWeight: 600, color: config.color }}>
            {config.label}
          </span>
        )}
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div
        style={{
          width: dotSize,
          height: dotSize,
          borderRadius: '50%',
          background: config.color,
          flexShrink: 0,
        }}
      />
      {showLabel && (
        <span style={{ fontSize: size === 'sm' ? '0.68rem' : '0.75rem', fontWeight: 600, color: config.color }}>
          {config.label}
        </span>
      )}
    </div>
  );
}

/** Badge variant with background */
export function StatusBadge({ status }: { status: string }) {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.unknown;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 5,
        padding: '3px 10px',
        borderRadius: 20,
        fontSize: '0.68rem',
        fontWeight: 600,
        background: config.bg,
        color: config.color,
        textTransform: 'capitalize',
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: '50%',
          background: config.color,
        }}
      />
      {config.label}
    </span>
  );
}
