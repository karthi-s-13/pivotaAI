/**
 * Recent Activity.
 *
 * Shows meaningful platform events with status indicators,
 * source context, and relative timestamps.
 */

import { useNavigate } from 'react-router-dom';
import { ArrowRight, Clock } from 'lucide-react';
import type { ActivityItem } from '../api/dashboardApi';
import { timeAgo, actionLabel, actionDescription, PROVIDER_META } from '../api/dashboardApi';

interface RecentActivityProps {
  activities: ActivityItem[];
}

function activityDotColor(action: string): string {
  if (action.includes('CREATED') || action.includes('CONNECTED') || action === 'SIGNUP') {
    return 'var(--status-success)';
  }
  if (action.includes('DELETED') || action.includes('DISCONNECTED')) {
    return 'var(--status-error)';
  }
  if (action.includes('WARNING') || action.includes('FAILED')) {
    return 'var(--status-warning)';
  }
  return 'var(--brand-primary)';
}

export default function RecentActivity({ activities }: RecentActivityProps) {
  const navigate = useNavigate();

  return (
    <div className="dashboard-panel">
      <div className="dashboard-panel__header">
        <h3 className="dashboard-panel__title">Recent Activity</h3>
        <button
          className="ds-table__link"
          onClick={() => navigate('/audit-logs')}
        >
          View audit log <ArrowRight size={12} />
        </button>
      </div>

      {activities.length === 0 ? (
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
          <Clock size={28} style={{ opacity: 0.3, marginBottom: 8 }} />
          <p style={{ fontSize: '0.82rem' }}>No recent activity</p>
        </div>
      ) : (
        <div className="activity-list">
          {activities.slice(0, 6).map((item) => {
            const desc = actionDescription(item.action, typeof item.details === 'string' ? null : item.details);
            const sourceName = typeof item.details === 'object' && item.details?.name
              ? item.details.name
              : item.user_name || 'System';
            const providerKey = typeof item.details === 'object' && item.details?.provider;
            const providerLabel = providerKey && PROVIDER_META[providerKey]?.label;

            return (
              <div
                key={item.id}
                className="activity-item"
                onClick={() => navigate('/audit-logs')}
              >
                <div
                  className="activity-item__dot"
                  style={{ background: activityDotColor(item.action) }}
                />
                <div className="activity-item__content">
                  <div className="activity-item__title">{actionLabel(item.action)}</div>
                  <div className="activity-item__source">
                    {providerLabel ? `${providerLabel} / ` : ''}{sourceName}
                  </div>
                  {desc && <div className="activity-item__desc">{desc}</div>}
                </div>
                <div className="activity-item__time">{timeAgo(item.timestamp)}</div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
