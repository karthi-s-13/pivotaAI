/**
 * Loading Skeleton.
 *
 * Full dashboard skeleton with pulsing placeholders for all sections.
 */

export default function LoadingSkeleton() {
  return (
    <div className="dashboard-content" style={{ opacity: 0.8 }}>
      {/* Welcome Skeleton */}
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 32, gap: 24 }}>
        <div>
          <div className="skeleton-pulse" style={{ width: 280, height: 24, marginBottom: 8 }} />
          <div className="skeleton-pulse" style={{ width: 360, height: 14 }} />
        </div>
        <div style={{ display: 'flex', gap: 10 }}>
          <div className="skeleton-pulse" style={{ width: 140, height: 38, borderRadius: 10 }} />
          <div className="skeleton-pulse" style={{ width: 120, height: 38, borderRadius: 10 }} />
        </div>
      </div>

      {/* Metric Cards Skeleton */}
      <div className="metric-cards-row">
        {[0, 1, 2, 3].map(i => (
          <div key={i} className="skeleton-card">
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
              <div className="skeleton-pulse" style={{ width: 40, height: 40, borderRadius: 10 }} />
              <div className="skeleton-pulse" style={{ width: 30, height: 14 }} />
            </div>
            <div className="skeleton-pulse" style={{ width: 80, height: 32, marginBottom: 8 }} />
            <div className="skeleton-pulse" style={{ width: 120, height: 12, marginBottom: 4 }} />
            <div className="skeleton-pulse" style={{ width: 90, height: 10 }} />
          </div>
        ))}
      </div>

      {/* Table Skeleton */}
      <div className="ds-table-wrap" style={{ marginBottom: 32 }}>
        <div style={{ padding: '12px 16px', background: 'var(--bg-elevated)' }}>
          <div className="skeleton-pulse" style={{ width: '100%', height: 14 }} />
        </div>
        {[0, 1, 2, 3].map(i => (
          <div key={i} style={{ padding: '14px 16px', borderBottom: '1px solid var(--glass-border)' }}>
            <div className="skeleton-pulse" style={{ width: '100%', height: 18 }} />
          </div>
        ))}
      </div>

      {/* Split Panel Skeleton */}
      <div className="dashboard-split">
        <div className="skeleton-card" style={{ padding: 20, minHeight: 260 }}>
          <div className="skeleton-pulse" style={{ width: 140, height: 16, marginBottom: 16 }} />
          {[0, 1, 2, 3].map(i => (
            <div key={i} className="skeleton-pulse" style={{ width: '100%', height: 40, marginBottom: 8, borderRadius: 8 }} />
          ))}
        </div>
        <div className="skeleton-card" style={{ padding: 20, minHeight: 260 }}>
          <div className="skeleton-pulse" style={{ width: 120, height: 16, marginBottom: 16 }} />
          {[0, 1, 2, 3, 4].map(i => (
            <div key={i} className="skeleton-pulse" style={{ width: '100%', height: 36, marginBottom: 6, borderRadius: 8 }} />
          ))}
        </div>
      </div>
    </div>
  );
}
